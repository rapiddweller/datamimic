# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The blind-agent eval oracle and transcript audit (#412): each reference project passes, each deliberately
broken variant fails exactly the checks it should, and the audit flags forbidden actions."""

import contextlib
import errno
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

import pytest

from benchmarks.authoring_eval import oracle, run_subject
from benchmarks.authoring_eval.audit_transcript import FindingKind, audit
from benchmarks.authoring_eval.capture import Capture
from benchmarks.authoring_eval.oracle import (
    CASES,
    DateRange,
    DateWindow,
    ExactCount,
    ExactRows,
    FieldRef,
    Observed,
    OracleSpec,
    Output,
    OutputRows,
    PerParentCount,
    Repeatable,
    RowExistsIn,
    SeedIs,
    Text,
    Unique,
    UniqueTogether,
    ValueIn,
    WholeNumber,
    _finish,
    _start,
    evaluate,
    json_outputs,
)
from benchmarks.authoring_eval.run_subject import brief, isolation_problems

_ALL_CASES = sorted(path.name for path in CASES.iterdir() if path.is_dir())


@dataclass(frozen=True)
class Broken:
    """A reference project plus text edits (file -> [(old, new)]) and the check labels the oracle must fail."""

    case: str
    name: str
    edits: dict[str, list[tuple[str, str]]]
    fails: frozenset[str]


_XML = "datamimic.xml"
_ACCEPTANCE = "acceptance/build.json"

# Under PYTHONHASHSEED=1 this is 0 and under 2 it is 1 (CPython 3.11), which is what the oracle sets for its two runs.
_BOTH_OUTPUTS = frozenset({"output_rows:priced_orders:fixtures", "output_rows:priced_orders:fixtures_changed"})

# A run that fails: no output file, no captured rows, and Build stops too.
_E04_RUN_FAILS = _BOTH_OUTPUTS | {"build_ready", "repeatable"}

# Build and the second oracle run both replay the project under another hash seed.
_HASH_ORDER = frozenset({"build_ready", "repeatable"})

_FLAG = "list({'alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf', 'hotel'}).index('bravo') % 2"

# Texts of the e06 and e07 references that several variants edit.
_E06_ASSIGNEE = (
    '<key name="assignment_id" script="parent.employment_id"/>\n'
    '                <key name="person_id" script="parent.person_id"/>'
)
_E06_EXPIRY = (
    "script=\"'2026-03-%02d' % parent.work_day if n == 1 else (None if parent.person_id % 2 == 0 else '2026-12-31')\""
)
_PERSON = '\n            <key name="person_id" script="parent.person_id"/>'
_E06_FUNCTION = 'source="fixtures/functions.wgt.csv"'
_E07_KEPT = "[order for order in orders if int(order.amount_cents) &gt;= 1000]"
_E07_NET = "amount - amount * percent // 100"
_E07_LAST_KEY = (
    "<key name=\"campaign\" script=\"'YES' if '2026-03-01' &lt;= order.order_date &lt;= '2026-03-31' else 'NO'\"/>"
)
_E07_OUTPUTS = frozenset({"output_rows:order_report:fixtures", "output_rows:order_report:fixtures_changed"})
# The reference acceptance pins 10 rows and the two campaign values, and Build needs a known row count.
_E07_OUTPUTS_AND_BUILD = _E07_OUTPUTS | {"build_ready"}


def _COUNTED(field: str, counter: str, script: str) -> tuple[str, str]:
    """Edit that turns an IncrementGenerator identifier into one built by ``script`` from a counter variable."""
    return (
        f'<key name="{field}" generator="IncrementGenerator"/>',
        f'<variable name="{counter}" generator="IncrementGenerator"/>\n        <key name="{field}" script="{script}"/>',
    )


_BROKEN = [
    Broken(
        "e01",
        "constant_ids",
        {_XML: [('name="ticket_id" generator="IncrementGenerator"', 'name="ticket_id" constant="7"')]},
        # constant= is text, and every title is the same "Ticket 7"
        frozenset({"unique:tickets.ticket_id", "whole_number:tickets.ticket_id", "unique:tickets.title"}),
    ),
    Broken(
        "e01",
        "constant_title",
        {_XML: [('string="Ticket __ticket_id__"', 'constant="Untitled"')]},
        frozenset({"unique:tickets.title"}),
    ),
    # integer titles are unique and not empty, but the prompt asks for text
    Broken(
        "e01",
        "numeric_titles",
        {_XML: [('string="Ticket __ticket_id__"', 'generator="IncrementGenerator"')]},
        frozenset({"text:tickets.title"}),
    ),
    Broken(
        "e01",
        "priority_outside_set",
        {_XML: [("('LOW', 'MEDIUM', 'HIGH')", "('LOW', 'MEDIUM', 'HIGH', 'URGENT')")]},
        frozenset({"value_in:tickets.priority"}),
    ),
    # The agent's own acceptance agrees with the wrong count, so only the oracle can catch it.
    Broken(
        "e01",
        "weak_acceptance",
        {_XML: [('count="25"', 'count="24"')], _ACCEPTANCE: [('"count": 25', '"count": 24')]},
        frozenset({"exact_count:tickets"}),
    ),
    Broken(
        "e02",
        "colliding_invoice_ids",
        {_XML: [('script="parent.subscriber_id * 10 + invoice_no"', 'script="invoice_no"')]},
        frozenset({"unique:invoices.invoice_id", "build_ready"}),
    ),
    Broken(
        "e02",
        "hardcoded_foreign_key",
        {_XML: [('name="subscriber_id" script="parent.subscriber_id"', 'name="subscriber_id" script="1"')]},
        frozenset({"per_parent_count:invoices.subscriber_id", "build_ready"}),
    ),
    Broken(
        "e02",
        "two_invoices_per_subscriber",
        {
            _XML: [('<generate name="invoices" count="3">', '<generate name="invoices" count="2">')],
            _ACCEPTANCE: [('"count": 15', '"count": 10'), ('"count": 3', '"count": 2')],
        },
        frozenset({"exact_count:invoices", "per_parent_count:invoices.subscriber_id"}),
    ),
    Broken(
        "e03",
        "colliding_slot_ids",
        {_XML: [('script="parent.depot_id * 100 + token"', 'script="token"')]},
        frozenset({"exact_rows:slots", "build_ready"}),
    ),
    Broken(
        "e03",
        "token_in_output",
        {_XML: [('<variable name="token"', '<key name="token"')]},
        frozenset({"exact_rows:slots", "build_ready"}),
    ),
    Broken(
        "e03",
        "wrong_state",
        {_XML: [('constant="FREE"', 'constant="BUSY"')]},
        frozenset({"exact_rows:slots"}),
    ),
    Broken(
        "e04",
        "total_left_as_text",
        {_XML: [('script="int(source_row.total_cents)"', 'script="source_row.total_cents"')]},
        _BOTH_OUTPUTS,
    ),
    Broken(
        "e04",
        "wrong_priority_threshold",
        {_XML: [(">= 5000", ">= 4000")]},
        _BOTH_OUTPUTS,
    ),
    Broken(
        "e04",
        "no_json_target",
        {_XML: [(' target="JSON"', "")]},
        _BOTH_OUTPUTS,
    ),
    # chunked output is valid, so only the wrong rule fails
    Broken(
        "e04",
        "chunked_wrong_priority_threshold",
        {_XML: [(' target="JSON"', ' target="JSON(chunk_size=4)"'), (">= 5000", ">= 4000")]},
        _BOTH_OUTPUTS,
    ),
    # the right rows in priced_orders_0.json, but the dataset has the wrong name
    Broken(
        "e04",
        "product_named_like_a_chunk",
        {
            _XML: [('<generate name="priced_orders"', '<generate name="priced_orders_0"')],
            _ACCEPTANCE: [('"product": "priced_orders"', '"product": "priced_orders_0"')],
        },
        _BOTH_OUTPUTS,
    ),
    # the file is pipe-separated: with a comma, each line is one column and the row has no order_id
    Broken(
        "e04",
        "comma_separator",
        {_XML: [('source="fixtures/orders.ent.csv"', 'source="fixtures/orders.ent.csv" separator=","')]},
        _E04_RUN_FAILS,
    ),
    # file missing: the project reads a file that the case does not supply
    Broken(
        "e04",
        "file_missing",
        {_XML: [('source="fixtures/orders.ent.csv"', 'source="fixtures/orders.csv"')]},
        _E04_RUN_FAILS,
    ),
    # a second product named like a chunk of the first holds the right rows; the first one writes a CSV file only
    Broken(
        "e04",
        "decoy_product_named_like_a_chunk",
        {
            _XML: [
                (
                    '<generate name="priced_orders" count="6" target="JSON">',
                    '<generate name="priced_orders" count="6" target="CSV">\n'
                    '        <variable name="source_row" source="fixtures/orders.ent.csv" distribution="ordered"/>\n'
                    '        <key name="order_id" script="source_row.order_id"/>\n'
                    "    </generate>\n"
                    '    <generate name="priced_orders_0" count="6" target="JSON">',
                )
            ],
            _ACCEPTANCE: [
                ('"max_count": 6', '"max_count": 12'),
                (
                    '"count": 6}\n  ]',
                    '"count": 6},\n    {"kind": "exact_count", '
                    '"subject": {"kind": "product", "product": "priced_orders_0"}, "count": 6}\n  ]',
                ),
            ],
        },
        _BOTH_OUTPUTS,
    ),
    Broken(
        "e05",
        "independent_prices",
        {_XML: [('script="list_price * 8 // 10"', 'type="int" min="50" max="900"')]},
        frozenset({"field_at_most:offers.sale_price"}),
    ),
    Broken(
        "e05",
        "sale_price_below_floor",
        {_XML: [("list_price * 8 // 10", "list_price // 10")]},
        frozenset({"range:offers.sale_price"}),
    ),
    Broken(
        "e05",
        "tier_outside_set",
        {_XML: [("('BRONZE', 'SILVER', 'GOLD')", "('BRONZE', 'SILVER', 'GOLD', 'PLATINUM')")]},
        frozenset({"value_in:offers.tier"}),
    ),
    # --- seed and repeatability (the prompts prescribe a seed) ---
    *[
        Broken(case, "missing_seed", {_XML: [(f' rngSeed="{seed}"', "")]}, fails)
        for case, seed, fails in [
            ("e01", "10421", frozenset({"seed_is", "repeatable"})),
            ("e02", "30517", frozenset({"seed_is", "repeatable"})),
            ("e03", "56606", frozenset({"seed_is"})),  # no random draw, so unseeded runs still agree
            ("e04", "51110", frozenset({"seed_is"})),
            ("e05", "77031", frozenset({"seed_is", "repeatable"})),
        ]
    ],
    *[
        Broken(case, "wrong_seed", {_XML: [(f'rngSeed="{seed}"', 'rngSeed="1"')]}, frozenset({"seed_is"}))
        for case, seed in [("e01", "10421"), ("e02", "30517"), ("e03", "56606"), ("e04", "51110"), ("e05", "77031")]
    ],
    # The seed is right, but one value depends on the order of a set of strings. That order changes with the
    # interpreter's hash seed. Build replays under another hash seed, and so does the second oracle run.
    Broken(
        "e01",
        "hash_ordered_hours",
        {_XML: [('name="estimate_hours" type="int" min="1" max="40"', f'name="estimate_hours" script="1 + {_FLAG}"')]},
        _HASH_ORDER,
    ),
    Broken(
        "e02",
        "hash_ordered_amount",
        {
            _XML: [
                ('name="amount_cents" type="int" min="500" max="20000"', f'name="amount_cents" script="500 + {_FLAG}"')
            ]
        },
        _HASH_ORDER,
    ),
    Broken(
        "e03",
        "hash_ordered_slot_ids",
        {
            _XML: [
                ('script="parent.depot_id * 100 + token"', f'script="parent.depot_id * 100 + token + 50 * ({_FLAG})"')
            ]
        },
        _HASH_ORDER,
    ),
    Broken(
        "e04",
        "hash_ordered_priority",
        {
            _XML: [
                (
                    "script=\"'high' if int(source_row.total_cents) >= 5000 else 'standard'\"",
                    "script=\"('high' if int(source_row.total_cents) >= 5000 else 'standard') "
                    f"if {_FLAG} == 0 else 'unknown'\"",
                )
            ]
        },
        _HASH_ORDER,
    ),
    Broken(
        "e05",
        "hash_ordered_sale_price",
        {_XML: [("list_price * 8 // 10", f"list_price * 8 // 10 + {_FLAG}")]},
        _HASH_ORDER,
    ),
    # --- the supplied fixtures must stay as they are ---
    # the project still works, but the prompt says not to change the file
    Broken(
        "e04",
        "edited_fixture",
        {"fixtures/orders.ent.csv": [("O-100|C-10|OPEN|1200", "O-100|C-10|CLOSED|1200")]},
        frozenset({"fixtures_unchanged"}),
    ),
    # --- the depots ---
    Broken(
        "e03",
        "depot_ids_skip_three",
        {
            _XML: [
                (
                    '<key name="depot_id" generator="IncrementGenerator"/>',
                    '<variable name="depot_no" generator="IncrementGenerator"/>\n'
                    '        <key name="depot_id" script="[1, 2, 4][depot_no - 1]"/>',
                )
            ]
        },
        frozenset({"exact_rows:depots", "exact_rows:slots"}),
    ),
    # --- identifiers must be whole numbers ---
    Broken(
        "e01",
        "string_ticket_ids",
        {_XML: [_COUNTED("ticket_id", "ticket_no", "str(ticket_no)")]},
        frozenset({"whole_number:tickets.ticket_id"}),
    ),
    Broken(
        "e01",
        "float_ticket_ids",
        {_XML: [_COUNTED("ticket_id", "ticket_no", "float(ticket_no)")]},
        frozenset({"whole_number:tickets.ticket_id"}),
    ),
    Broken(
        "e02",
        "string_invoice_ids",
        {
            _XML: [
                (
                    'script="parent.subscriber_id * 10 + invoice_no"',
                    'script="str(parent.subscriber_id * 10 + invoice_no)"',
                )
            ]
        },
        frozenset({"whole_number:invoices.invoice_id"}),
    ),
    Broken(
        "e03",
        "string_slot_ids",
        {_XML: [('script="parent.depot_id * 100 + token"', 'script="str(parent.depot_id * 100 + token)"')]},
        frozenset({"exact_rows:slots"}),
    ),
    Broken(
        "e05",
        "string_offer_ids",
        {_XML: [_COUNTED("offer_id", "offer_no", "str(offer_no)")]},
        frozenset({"whole_number:offers.offer_id"}),
    ),
    Broken(
        "e05",
        "float_offer_ids",
        {_XML: [_COUNTED("offer_id", "offer_no", "float(offer_no)")]},
        frozenset({"whole_number:offers.offer_id"}),
    ),
    # --- e06: one variant per rule; the reference itself is the boundary case "work_date is the expiry day" ---
    Broken(
        "e06",
        "assignment_at_a_company_without_employment",
        {
            _XML: [
                (
                    'name="company_id" script="parent.company_id"',
                    'name="company_id" script="(parent.company_id + 1) % 4 + 1"',
                )
            ]
        },
        frozenset({"row_exists_in:assignments->employments"}),
    ),
    Broken(
        "e06",
        "assignment_in_another_function",
        {
            _XML: [
                (
                    'name="function" script="parent.function"',
                    "name=\"function\" script=\"'PLANNER' if parent.function == 'OPERATOR' else 'OPERATOR'\"",
                )
            ]
        },
        frozenset({"row_exists_in:assignments->employments"}),
    ),
    Broken(
        "e06",
        "assignment_of_another_person",
        {
            _XML: [
                (
                    _E06_ASSIGNEE,
                    _E06_ASSIGNEE.replace(
                        'person_id" script="parent.person_id', 'person_id" script="parent.person_id % 20 + 1'
                    ),
                )
            ]
        },
        frozenset({"row_exists_in:assignments->employments", "row_exists_in:assignments->licenses"}),
    ),
    # max + 1: the work date is the day after the expiry day
    Broken(
        "e06",
        "work_date_after_the_expiry_day",
        {_XML: [("'2026-03-%02d' % parent.work_day if n == 1", "'2026-03-%02d' % (parent.work_day - 1) if n == 1")]},
        frozenset({"row_exists_in:assignments->licenses"}),
    ),
    # min - 1: the work date is the day before the license starts
    Broken(
        "e06",
        "work_date_before_valid_from",
        {_XML: [("'2026-01-%02d' % parent.person_id if n == 1", "'2026-03-%02d' % (parent.work_day + 1) if n == 1")]},
        frozenset({"row_exists_in:assignments->licenses"}),
    ),
    # the even people work on a license without an expiry date; still 10 such licenses
    Broken(
        "e06",
        "missing_expiry_counts_as_valid",
        {
            _XML: [
                (
                    _E06_EXPIRY,
                    "script=\"(None if parent.person_id % 2 == 0 else '2026-03-%02d' % parent.work_day) "
                    "if n == 1 else '2026-12-31'\"",
                )
            ]
        },
        frozenset({"row_exists_in:assignments->licenses"}),
    ),
    # absent: the license without an expiry date leaves the field out instead of null
    Broken(
        "e06",
        "absent_field_for_a_missing_expiry",
        {
            _XML: [
                (
                    '<key name="expires_on" script=',
                    '<key name="expires_on" condition="n == 1 or parent.person_id % 2 == 1" script=',
                )
            ]
        },
        frozenset({"date_range:licenses.expires_on"}),
    ),
    Broken(
        "e06",
        "empty_text_for_a_missing_expiry",
        {_XML: [("(None if parent.person_id % 2 == 0", "('' if parent.person_id % 2 == 0")]},
        frozenset({"date_range:licenses.expires_on"}),
    ),
    Broken(  # min - 1
        "e06",
        "nine_missing_expiries",
        {_XML: [("None if parent.person_id % 2 == 0", "None if parent.person_id % 2 == 0 and parent.person_id != 20")]},
        frozenset({"date_range:licenses.expires_on"}),
    ),
    Broken(  # max + 1
        "e06",
        "eleven_missing_expiries",
        {_XML: [("None if parent.person_id % 2 == 0", "None if parent.person_id % 2 == 0 or parent.person_id == 1")]},
        frozenset({"date_range:licenses.expires_on"}),
    ),
    # a date text of another form is no date, so no license can cover it
    Broken(
        "e06",
        "work_date_in_another_format",
        {_XML: [("'2026-03-%02d' % root.work_day", "'%02d.03.2026' % root.work_day")]},
        frozenset({"date_range:assignments.work_date", "row_exists_in:assignments->licenses"}),
    ),
    Broken(
        "e06",
        "two_employments_at_one_company",
        {_XML: [("(parent.person_id + n) % 4 + 1", "(parent.person_id + 1) % 4 + 1")]},
        frozenset({"unique_together:employments.person_id+company_id"}),
    ),
    # the reference acceptance has the visible set too
    Broken(
        "e06",
        "function_outside_the_file",
        {_XML: [(_E06_FUNCTION, 'constant="SUPERVISOR"')]},
        frozenset({"value_in:employments.function", "value_in:employments.function:fixtures_changed", "build_ready"}),
    ),
    # the visible list and its weights typed into the project: the hidden list has other functions
    Broken(
        "e06",
        "functions_typed_into_the_project",
        {_XML: [(_E06_FUNCTION, "values=\"'OPERATOR', 'INSPECTOR', 'PLANNER'\" weights=\"80, 15, 5\"")]},
        frozenset({"value_in:employments.function:fixtures_changed"}),
    ),
    Broken(
        "e06",
        "badge_without_three_digits",
        {_XML: [("'P-%03d' % person_id", "'P-%d' % person_id")]},
        frozenset({"exact_rows:people"}),
    ),
    # the text "2" is not the company 2; the assignment copies the text and so still matches its employment
    Broken(
        "e06",
        "text_company_ids_in_employments",
        {_XML: [("(parent.person_id + n) % 4 + 1", "str((parent.person_id + n) % 4 + 1)")]},
        frozenset({"row_exists_in:employments->companies", "build_ready"}),
    ),
    Broken(
        "e06",
        "three_employments_per_person",
        {
            _XML: [('<generate name="employments" count="2">', '<generate name="employments" count="3">')],
            _ACCEPTANCE: [('"max_count": 124', '"max_count": 144')],
        },
        frozenset({"exact_count:employments", "per_parent_count:employments.person_id"}),
    ),
    # person 1 is assigned at company 4, which then has 6 assignments and company 3 has 4
    Broken(
        "e06",
        "six_assignments_at_one_company",
        {_XML: [("(parent.person_id + n) % 4 + 1", "(parent.person_id + n + (parent.person_id == 1)) % 4 + 1")]},
        frozenset({"per_parent_count:assignments.company_id"}),
    ),
    Broken(
        "e06",
        "text_assignment_ids",
        {
            _XML: [
                (
                    _E06_ASSIGNEE,
                    _E06_ASSIGNEE.replace(
                        '"assignment_id" script="parent.employment_id',
                        '"assignment_id" script="str(parent.employment_id)',
                    ),
                )
            ]
        },
        frozenset({"whole_number:assignments.assignment_id"}),
    ),
    Broken(
        "e06",
        "empty_full_names",
        {_XML: [("script=\"given + ' ' + family\"", "script=\"''\"")]},
        frozenset({"text:people.full_name"}),
    ),
    Broken("e06", "missing_seed", {_XML: [(' rngSeed="61423"', "")]}, frozenset({"seed_is", "repeatable"})),
    Broken("e06", "wrong_seed", {_XML: [('rngSeed="61423"', 'rngSeed="1"')]}, frozenset({"seed_is"})),
    Broken(
        "e06",
        "hash_ordered_names",
        {_XML: [("script=\"given + ' ' + family\"", f"script=\"given + ' ' + family + str({_FLAG})\"")]},
        _HASH_ORDER,
    ),
    # duplicate: person 1 takes the assignment of person 2 at company 4, on the day of its other assignment
    Broken(
        "e06",
        "two_assignments_on_one_day",
        {
            _XML: [
                (
                    'count="{1 if n == 1 else 0}"',
                    'count="{1 if (n == 1 and person_id != 2) or (n == 2 and person_id == 1) else 0}"',
                )
            ]
        },
        frozenset({"unique_together:assignments.person_id+work_date"}),
    ),
    Broken(
        "e06",
        "person_without_assignment",
        {_XML: [('count="{1 if n == 1 else 0}"', 'count="{1 if n == 1 and person_id != 1 else 0}"')]},
        frozenset({"exact_count:assignments", "per_parent_count:assignments.company_id", "build_ready"}),
    ),
    Broken(  # max + 1
        "e06",
        "valid_from_after_march",
        {_XML: [("else '2026-03-31'\"/>", "else '2026-04-01'\"/>")]},
        frozenset({"date_range:licenses.valid_from"}),
    ),
    # the third license of each even person has no expiry date either: 20 nulls
    Broken(
        "e06",
        "three_licenses_per_person",
        {
            _XML: [('<generate name="licenses" count="2">', '<generate name="licenses" count="3">')],
            _ACCEPTANCE: [('"max_count": 124', '"max_count": 144')],
        },
        frozenset({"exact_count:licenses", "per_parent_count:licenses.person_id", "date_range:licenses.expires_on"}),
    ),
    # company 5 has no assignment
    Broken(
        "e06",
        "five_companies",
        {
            _XML: [('<generate name="companies" count="4">', '<generate name="companies" count="5">')],
            _ACCEPTANCE: [('"max_count": 124', '"max_count": 125')],
        },
        frozenset({"exact_rows:companies", "per_parent_count:assignments.company_id"}),
    ),
    Broken(
        "e06",
        "numeric_company_names",
        {_XML: [('string="Company __company_id__"', 'script="company_id"')]},
        frozenset({"text:companies.name"}),
    ),
    # The assignment_id copies the employment_id, so a broken employment_id breaks the assignment_id too.
    Broken(
        "e06",
        "colliding_employment_ids",
        {_XML: [('name="employment_id" script="parent.person_id * 10 + n"', 'name="employment_id" script="n"')]},
        frozenset({"unique:employments.employment_id", "unique:assignments.assignment_id", "build_ready"}),
    ),
    Broken(
        "e06",
        "colliding_license_ids",
        {_XML: [('name="license_id" script="parent.person_id * 10 + n"', 'name="license_id" script="n"')]},
        frozenset({"unique:licenses.license_id", "build_ready"}),
    ),
    Broken(
        "e06",
        "colliding_assignment_ids",
        {_XML: [('name="assignment_id" script="parent.employment_id"', 'name="assignment_id" script="1"')]},
        frozenset({"unique:assignments.assignment_id", "build_ready"}),
    ),
    Broken(
        "e06",
        "text_employment_ids",
        {
            _XML: [
                (
                    'name="employment_id" script="parent.person_id * 10 + n"',
                    'name="employment_id" script="str(parent.person_id * 10 + n)"',
                )
            ]
        },
        frozenset({"whole_number:employments.employment_id", "whole_number:assignments.assignment_id"}),
    ),
    Broken(
        "e06",
        "text_license_ids",
        {
            _XML: [
                (
                    'name="license_id" script="parent.person_id * 10 + n"',
                    'name="license_id" script="str(parent.person_id * 10 + n)"',
                )
            ]
        },
        frozenset({"whole_number:licenses.license_id"}),
    ),
    # The text "1" is not the person 1. The assignments copy it, so no license of the person matches; Build's
    # foreign key role compares the types too.
    *[
        Broken(
            "e06",
            f"text_person_ids_in_{product}",
            {_XML: [(f"{before}{_PERSON}", f"{before}{_PERSON.replace('parent.person_id', 'str(parent.person_id)')}")]},
            frozenset({f"whole_number:{product}.person_id", "row_exists_in:assignments->licenses", "build_ready"}),
        )
        for product, before in [
            ("employments", '<key name="employment_id" script="parent.person_id * 10 + n"/>'),
            ("licenses", '<key name="license_id" script="parent.person_id * 10 + n"/>'),
        ]
    ],
    # --- e07: one variant per rule; every rule has a boundary row in both fixture sets ---
    Broken("e07", "no_threshold", {_XML: [(_E07_KEPT, "list(orders)")]}, _E07_OUTPUTS_AND_BUILD),
    Broken("e07", "threshold_excludes_1000", {_XML: [("&gt;= 1000", "&gt; 1000")]}, _E07_OUTPUTS_AND_BUILD),
    # source values are texts: '999' >= '1000' is true
    Broken(
        "e07",
        "threshold_compared_as_text",
        {_XML: [("int(order.amount_cents) &gt;= 1000", "order.amount_cents &gt;= '1000'")]},
        _E07_OUTPUTS_AND_BUILD,
    ),
    Broken("e07", "other_default_name", {_XML: [("'UNKNOWN'", "'N/A'")]}, _E07_OUTPUTS),
    Broken("e07", "silver_without_discount", {_XML: [("{'GOLD': 10, 'SILVER': 5}", "{'GOLD': 10}")]}, _E07_OUTPUTS),
    # 1999 at 10 percent: 1999 - 199 = 1800, but int(1999 * 0.9) = 1799
    Broken(
        "e07",
        "net_rounded_down_instead_of_the_discount",
        {_XML: [(_E07_NET, "int(amount * (1 - percent / 100))")]},
        _E07_OUTPUTS,
    ),
    Broken(
        "e07",
        "campaign_without_its_last_day",
        {_XML: [("order.order_date &lt;= '2026-03-31'", "order.order_date &lt; '2026-03-31'")]},
        _E07_OUTPUTS,
    ),
    Broken(
        "e07",
        "campaign_without_its_first_day",
        {_XML: [("'2026-03-01' &lt;= order.order_date", "'2026-03-01' &lt; order.order_date")]},
        _E07_OUTPUTS,
    ),
    # both fixture sets hold a kept order from March of another year
    Broken(
        "e07",
        "campaign_ignores_the_year",
        {_XML: [("'2026-03-01' &lt;= order.order_date &lt;= '2026-03-31'", "order.order_date[5:7] == '03'")]},
        _E07_OUTPUTS,
    ),
    # GOLDEN is another tier, so it gets no discount
    Broken(
        "e07",
        "tier_matched_on_its_prefix",
        {_XML: [("{'GOLD': 10, 'SILVER': 5}.get(customer.tier, 0)", "{'G': 10, 'S': 5}.get(customer.tier[:1], 0)")]},
        frozenset({"output_rows:order_report:fixtures_changed"}),
    ),
    # a scripted generate copies every source column into the row
    Broken(
        "e07",
        "source_columns_in_the_output",
        {_XML: [('count="{len(kept)}"', 'script="kept"')]},
        _E07_OUTPUTS_AND_BUILD,
    ),
    Broken(
        "e07",
        "extra_field",
        {_XML: [(_E07_LAST_KEY, _E07_LAST_KEY + '\n            <key name="channel" script="order.channel"/>')]},
        _E07_OUTPUTS,
    ),
    # duplicate: every kept order twice
    Broken(
        "e07",
        "each_order_twice",
        {
            _XML: [
                ('count="{len(kept)}"', 'count="{2 * len(kept)}"'),
                ("parent.kept[i - 1]", "parent.kept[(i - 1) % len(parent.kept)]"),
            ]
        },
        _E07_OUTPUTS_AND_BUILD,
    ),
    Broken("e07", "missing_field", {_XML: [(_E07_LAST_KEY, "")]}, _E07_OUTPUTS_AND_BUILD),
    Broken("e07", "no_json_file", {_XML: [('count="{len(kept)}" target="JSON"', 'count="{len(kept)}"')]}, _E07_OUTPUTS),
    Broken(
        "e07",
        "edited_fixture",
        {"fixtures/customers.ent.csv": [("C-104|Dune Parts|GOLD|PT", "C-104|Dune Parts|SILVER|PT")]},
        frozenset({"fixtures_unchanged"}),
    ),
    Broken("e07", "missing_seed", {_XML: [(' rngSeed="40961"', "")]}, frozenset({"seed_is"})),  # no random draw
    Broken("e07", "wrong_seed", {_XML: [('rngSeed="40961"', 'rngSeed="1"')]}, frozenset({"seed_is"})),
    Broken(
        "e07",
        "hash_ordered_campaign",
        {_XML: [("else 'NO'\"", f"else 'NO' if {_FLAG} == 0 else 'MAYBE'\"")]},
        _HASH_ORDER,
    ),
]

# Variants that change the method but not the values; the oracle must pass them.
_EQUIVALENT = [
    # order: without distribution="ordered" the read is shuffled, and output_rows ignores the row order
    Broken(
        "e04",
        "orders_read_shuffled",
        {_XML: [(' source="fixtures/orders.ent.csv" distribution="ordered"', ' source="fixtures/orders.ent.csv"')]},
        frozenset(),
    ),
    # min: the work date is the first day of the license
    Broken(
        "e06",
        "work_date_on_valid_from",
        {_XML: [("'2026-01-%02d' % parent.person_id if n == 1", "'2026-03-%02d' % parent.work_day if n == 1")]},
        frozenset(),
    ),
    # the weighted list read through a variable instead of the key's own source
    Broken(
        "e06",
        "function_read_through_a_variable",
        {
            _XML: [
                (
                    f'<key name="function" {_E06_FUNCTION}/>',
                    f'<variable name="drawn" {_E06_FUNCTION}/>\n            <key name="function" script="drawn"/>',
                )
            ]
        },
        frozenset(),
    ),
    # order: the people in reverse order; every check ignores the row order
    Broken(
        "e06",
        "people_in_reverse_order",
        {
            _XML: [
                (
                    '<key name="person_id" generator="IncrementGenerator"/>',
                    '<variable name="person_no" generator="IncrementGenerator"/>\n'
                    '        <key name="person_id" script="21 - person_no"/>',
                )
            ]
        },
        frozenset(),
    ),
    # order: the orders read in a shuffled order
    Broken(
        "e07",
        "orders_read_shuffled",
        {
            _XML: [
                (
                    'name="orders" source="fixtures/orders.ent.csv" storage="data" distribution="ordered"',
                    'name="orders" source="fixtures/orders.ent.csv" storage="data"',
                )
            ]
        },
        frozenset(),
    ),
]


@pytest.mark.parametrize("variant", _EQUIVALENT, ids=lambda variant: f"{variant.case}-{variant.name}")
def test_an_equivalent_variant_passes(variant: Broken, tmp_path: Path) -> None:
    project = _edited_reference(tmp_path, variant)

    assert _failed(project, variant.case) == set()


def _typed_rows(case: str, product: str) -> str:
    """A project that types the expected rows of the case fixtures into one script and reads no file."""
    spec = OracleSpec.model_validate_json((CASES / case / "oracle.json").read_text(encoding="utf-8"))
    rows = next(check.rows for check in spec.checks if isinstance(check, OutputRows) and check.fixtures == "fixtures")
    seed = next(check.seed for check in spec.checks if isinstance(check, SeedIs))
    keys = "".join(f'\n        <key name="{name}" script="row[{name!r}]"/>' for name in rows[0])
    return (
        f'<setup rngSeed="{seed}">\n    <generate name="{product}" count="{len(rows)}" target="JSON">\n'
        f'        <variable name="i" generator="IncrementGenerator"/>\n'
        f'        <variable name="row" script="{xml_escape(repr(rows))}[i - 1]"/>{keys}\n    </generate>\n</setup>'
    )


# Whole wrong projects that a weak agent can write. Each one has the right shape and must still fail.
_CHEAT_ACCEPTANCE = '{"version": "5.0", "max_count": 200, "expectations": []}'
_CHEATS = {
    # slot_id from one counter over all slots, not from the depot and a counter inside it
    ("e03", "global_counter"): (
        """<setup rngSeed="56606">
    <generate name="depots" count="3">
        <key name="depot_id" generator="IncrementGenerator"/>
    </generate>
    <generate name="slots" count="12">
        <key name="slot_id" generator="IncrementGenerator"/>
        <key name="depot_id" script="(slot_id - 1) // 4 + 1"/>
        <key name="state" constant="FREE"/>
    </generate>
</setup>""",
        frozenset({"exact_rows:slots"}),
    ),
    # the six rows typed into scripts: the input file is never read
    ("e04", "typed_rows"): (
        _typed_rows("e04", "priced_orders"),
        frozenset({"output_rows:priced_orders:fixtures_changed"}),
    ),
    # every foreign key drawn at random from the right set: each one exists, but the rules across tables break;
    # the functions are typed, so the hidden weighted file fails them
    ("e06", "random_foreign_keys"): (
        """<setup rngSeed="61423">
    <generate name="companies" count="4">
        <key name="company_id" generator="IncrementGenerator"/>
        <key name="name" string="Company __company_id__"/>
    </generate>
    <generate name="people" count="20">
        <key name="person_id" generator="IncrementGenerator"/>
        <key name="badge" script="'P-%03d' % person_id"/>
        <key name="full_name" string="Person __person_id__"/>
    </generate>
    <generate name="employments" count="40">
        <key name="employment_id" generator="IncrementGenerator"/>
        <key name="person_id" script="(employment_id - 1) // 2 + 1"/>
        <key name="company_id" type="int" min="1" max="4"/>
        <key name="function" values="'OPERATOR', 'INSPECTOR', 'PLANNER'"/>
    </generate>
    <generate name="licenses" count="40">
        <key name="license_id" generator="IncrementGenerator"/>
        <key name="person_id" script="(license_id - 1) // 2 + 1"/>
        <key name="valid_from" constant="2026-01-01"/>
        <key name="expires_on" script="None if license_id % 4 == 0 else '2026-12-31'"/>
    </generate>
    <generate name="assignments" count="20">
        <key name="assignment_id" generator="IncrementGenerator"/>
        <key name="person_id" type="int" min="1" max="20"/>
        <key name="company_id" script="(assignment_id - 1) // 5 + 1"/>
        <key name="function" values="'OPERATOR', 'INSPECTOR', 'PLANNER'"/>
        <key name="work_date" script="'2026-03-%02d' % assignment_id"/>
    </generate>
</setup>""",
        frozenset(
            {
                "unique_together:employments.person_id+company_id",
                "row_exists_in:assignments->employments",
                "value_in:employments.function:fixtures_changed",
            }
        ),
    ),
    # the kept rows typed into scripts: the input files are never read
    ("e07", "typed_rows"): (
        _typed_rows("e07", "order_report"),
        frozenset({"output_rows:order_report:fixtures_changed"}),
    ),
    # a flat copy of the orders file: every order and every column
    ("e07", "flat_copy"): (
        """<setup rngSeed="40961">
    <generate name="order_report" source="fixtures/orders.ent.csv" distribution="ordered" target="JSON"/>
</setup>""",
        _E07_OUTPUTS,
    ),
}


# Whole valid projects in another style than the reference; the oracle must pass them.
_OTHER_STYLES = {
    # one report row under each order row, only for a kept order; the lookups are list comprehensions
    "e07": """<setup rngSeed="40961">
    <iterate name="orders" source="fixtures/orders.ent.csv" distribution="ordered" target="ConsoleExporter">
        <variable name="customers" source="fixtures/customers.ent.csv" storage="data" distribution="ordered"/>
        <variable name="names" script="[c.name for c in customers if c.customer_id == customer_id]"/>
        <variable name="percents" script="[{'GOLD': 10, 'SILVER': 5}.get(c.tier, 0)
            for c in customers if c.customer_id == customer_id]"/>
        <variable name="amount" script="int(amount_cents)"/>
        <variable name="report" script="{'order_id': order_id, 'customer_id': customer_id,
            'customer_name': names[0] if names else 'UNKNOWN',
            'net_cents': amount - amount * (percents[0] if percents else 0) // 100,
            'campaign': 'YES' if '2026-03-01' &lt;= order_date &lt;= '2026-03-31' else 'NO'}"/>
        <generate name="order_report" count="{1 if amount &gt;= 1000 else 0}" target="JSON">
            <key name="order_id" script="parent.report['order_id']"/>
            <key name="customer_id" script="parent.report['customer_id']"/>
            <key name="customer_name" script="parent.report['customer_name']"/>
            <key name="net_cents" script="parent.report['net_cents']"/>
            <key name="campaign" script="parent.report['campaign']"/>
        </generate>
    </iterate>
</setup>""",
}


def _whole_project(tmp_path: Path, case: str, xml: str) -> Path:
    project = _start_dir(tmp_path, case)
    (project / "acceptance").mkdir(parents=True)
    (project / _XML).write_text(xml, encoding="utf-8")
    (project / _ACCEPTANCE).write_text(_CHEAT_ACCEPTANCE, encoding="utf-8")
    return project


@pytest.mark.parametrize(("case", "name"), sorted(_CHEATS), ids=[f"{case}-{name}" for case, name in sorted(_CHEATS)])
def test_cheat_project_fails_the_oracle(case: str, name: str, tmp_path: Path) -> None:
    xml, fails = _CHEATS[case, name]

    assert _failed(_whole_project(tmp_path, case, xml), case) == fails


@pytest.mark.parametrize("case", sorted(_OTHER_STYLES))
def test_a_valid_project_in_another_style_passes(case: str, tmp_path: Path) -> None:
    assert _failed(_whole_project(tmp_path, case, _OTHER_STYLES[case]), case) == set()


def _failed(project: Path, case: str) -> set[str]:
    return {result.check for result in evaluate(case, project).checks if not result.passed}


def _start_dir(tmp_path: Path, case: str) -> Path:
    """The project directory as a subject gets it: empty, or with the case fixtures, as run_subject makes it."""
    project = tmp_path / "project"
    project.mkdir()
    if (CASES / case / "fixtures").is_dir():
        shutil.copytree(CASES / case / "fixtures", project / "fixtures")
    return project


def _reference(tmp_path: Path, case: str) -> Path:
    return shutil.copytree(CASES / case / "reference", _start_dir(tmp_path, case), dirs_exist_ok=True)


@pytest.mark.parametrize("case", _ALL_CASES)
def test_reference_passes_every_check(case: str, tmp_path: Path) -> None:
    verdict = evaluate(case, _reference(tmp_path, case))

    assert [result for result in verdict.checks if not result.passed] == []
    assert verdict.passed


def _edited_reference(tmp_path: Path, variant: Broken) -> Path:
    project = _reference(tmp_path, variant.case)
    for filename, edits in variant.edits.items():
        text = (project / filename).read_text(encoding="utf-8")
        for old, new in edits:
            assert text.count(old) == 1, f"edit target not exactly once in {filename}: {old}"
            text = text.replace(old, new)
        (project / filename).write_text(text, encoding="utf-8")
    return project


@pytest.mark.parametrize("broken", _BROKEN, ids=lambda broken: f"{broken.case}-{broken.name}")
def test_broken_variant_fails_exactly_the_expected_checks(broken: Broken, tmp_path: Path) -> None:
    project = _edited_reference(tmp_path, broken)

    assert _failed(project, broken.case) == broken.fails
    assert not evaluate(broken.case, project).passed


def test_a_deleted_fixture_fails_although_the_oracle_supplies_it(tmp_path: Path) -> None:
    project = _reference(tmp_path, "e04")
    (project / "fixtures" / "orders.ent.csv").unlink()

    assert _failed(project, "e04") == {"fixtures_unchanged"}


def test_a_new_fixture_file_passes(tmp_path: Path) -> None:
    project = _reference(tmp_path, "e04")
    (project / "fixtures" / "notes.txt").write_text("my notes", encoding="utf-8")

    assert _failed(project, "e04") == set()


def test_an_extra_depot_field_passes(tmp_path: Path) -> None:
    project = _reference(tmp_path, "e03")
    depot_id = '<key name="depot_id" generator="IncrementGenerator"/>'
    xml = (project / _XML).read_text(encoding="utf-8")
    assert depot_id in xml
    # the prompt fixes the field set for slots only
    label = '\n        <key name="label" string="Depot __depot_id__"/>'
    (project / _XML).write_text(xml.replace(depot_id, depot_id + label), encoding="utf-8")

    assert _failed(project, "e03") == set()


@pytest.mark.parametrize("chunk_size", [10, 4])  # one part priced_orders_0.json, or two parts
def test_chunked_json_output_passes_for_both_fixtures(chunk_size: int, tmp_path: Path) -> None:
    project = _reference(tmp_path, "e04")
    xml = (project / _XML).read_text(encoding="utf-8")
    (project / _XML).write_text(xml.replace(' target="JSON"', f' target="JSON(chunk_size={chunk_size})"'))

    assert _failed(project, "e04") == set()


@pytest.mark.parametrize("folder", ["output", "Output"])  # macOS file systems ignore case
def test_output_file_left_by_the_agents_own_run_does_not_count(folder: str, tmp_path: Path) -> None:
    project = _reference(tmp_path, "e04")
    stale = project / folder / "earlier-run"
    stale.mkdir(parents=True)
    spec = OracleSpec.model_validate_json((CASES / "e04" / "oracle.json").read_text(encoding="utf-8"))
    right = next(check for check in spec.checks if isinstance(check, OutputRows) and check.fixtures == "fixtures")
    (stale / "priced_orders.json").write_text(json.dumps(right.rows), encoding="utf-8")
    (project / _XML).write_text((project / _XML).read_text(encoding="utf-8").replace(' target="JSON"', ""))

    assert _failed(project, "e04") == _BOTH_OUTPUTS


# A project script can reach the os module through the subclasses of object, despite the empty __builtins__.
_OS = "[c for c in ().__class__.__base__.__subclasses__() if c.__name__ == '_wrap_close'][0].__init__.__globals__"


def test_the_capture_run_sees_neither_the_repository_nor_the_operators_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DM_EVAL_OPERATOR_SECRET", "x")
    project = tmp_path / "project"
    project.mkdir()
    (project / _XML).write_text(
        f"""<setup>
    <generate name="probe" count="1">
        <key name="cwd" script="{_OS}['getcwd']()"/>
        <key name="secret" script="{_OS}['environ'].get('DM_EVAL_OPERATOR_SECRET', 'absent')"/>
    </generate>
</setup>""",
        encoding="utf-8",
    )

    capture = _capture(project)

    assert capture.rows["probe"] == [{"cwd": str(project), "secret": "absent"}]


def _capture(project: Path) -> Capture:
    return _finish(*_start(project, "1"))


@dataclass(frozen=True)
class Descendants:
    """A capture whose key script starts processes. ``{pidfile}`` in the script names where a shell writes a pid."""

    name: str
    script: str
    timeout: int | None  # the run timeout in seconds; None keeps the oracle's own
    error: str | None  # the expected Capture.error
    dies: bool = True  # False: the process left the group (setsid), and no group kill can reach it
    rows: dict[str, list[dict[str, object]]] | None = None  # set when the script starts no process
    refused_killpg: bool = False  # True: killpg fails with EPERM, as macOS does while the group exits (#432)


_SYSTEM = f"{_OS}['system']"
_EXEC_SLEEP = f"{_SYSTEM}('echo $PPID > {{pidfile}}') or {_OS}['execv']('/bin/sleep', ['sleep', '30'])"
_SPAWN = f"{_OS}['posix_spawn']('/bin/sleep', ['sleep', '30'], dict()"
_DESCENDANTS = [
    Descendants("finishes", "7", None, None, rows={"probe": [{"out": 7}]}),
    Descendants("times_out_without_child", _EXEC_SLEEP, 8, "Timeout"),
    Descendants("times_out_while_killpg_is_refused", _EXEC_SLEEP, 8, "Timeout", refused_killpg=True),
    # the Codex case: the child inherits stdout and outlives the killed capture interpreter
    Descendants(
        "times_out_with_child_on_stdout", f"{_SYSTEM}('sleep 30 & echo $! > {{pidfile}}; sleep 30')", 8, "Timeout"
    ),
    # the subshell exits at once: init adopts the sleep, which stays in the group and keeps stdout open
    Descendants("leaves_daemonized_grandchild", f"{_SYSTEM}('(sleep 30 & echo $! > {{pidfile}})')", None, None),
    Descendants("leaves_stray_child", f"{_SYSTEM}('echo %d > {{pidfile}}' % {_SPAWN}))", None, None),
    Descendants(
        "leaves_child_in_own_session",
        f"{_SYSTEM}('echo %d > {{pidfile}}' % {_SPAWN}, setsid=True))",
        None,
        None,
        dies=False,
    ),
]


def _refuse_killpg(pgid: int, signum: int) -> None:
    raise PermissionError(errno.EPERM, "Operation not permitted")


@pytest.mark.parametrize("case", _DESCENDANTS, ids=lambda case: case.name)
def test_a_capture_returns_promptly_and_ends_its_descendants(
    case: Descendants, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A descendant that holds stdout open must not delay the verdict, and the group kill must end it."""
    if case.timeout is not None:
        monkeypatch.setattr(oracle, "_RUN_TIMEOUT_SECONDS", case.timeout)
    if case.refused_killpg:
        monkeypatch.setattr(oracle.os, "killpg", _refuse_killpg)
    pidfile = tmp_path / "descendant.pid"
    project = tmp_path / "project"
    project.mkdir()
    script = xml_escape(case.script.format(pidfile=pidfile))
    xml = f'<setup rngSeed="1">\n    <generate name="probe" count="1">\n        <key name="out" script="{script}"/>\n'
    (project / _XML).write_text(xml + "    </generate>\n</setup>", encoding="utf-8")
    try:
        started = time.monotonic()
        capture = _capture(project)
        elapsed = time.monotonic() - started

        assert capture.error == case.error
        # a timeout ends after the timeout plus the kill; a normal exit ends long before the 30 s of the descendant
        assert elapsed < (case.timeout + 2 if case.timeout is not None else 20)
        if case.rows is not None:
            assert capture.rows == case.rows
            return
        # without the pid the script never ran, and the test would prove nothing
        pid = int(pidfile.read_text(encoding="utf-8"))
        deadline = time.monotonic() + 5
        while case.dies and _alive(pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        assert _alive(pid) is not case.dies
    finally:
        # also after a failed assert: a descendant must not outlive the test
        if pidfile.is_file() and _alive(pid := int(pidfile.read_text(encoding="utf-8"))):
            with contextlib.suppress(ProcessLookupError):
                os.kill(pid, signal.SIGKILL)


def test_a_module_shipped_in_the_project_does_not_replace_the_capture_code(tmp_path: Path) -> None:
    project = _reference(tmp_path, "e01")
    shadow = project / "benchmarks" / "authoring_eval"
    shadow.mkdir(parents=True)
    (project / "benchmarks" / "__init__.py").write_text("", encoding="utf-8")
    (shadow / "__init__.py").write_text("", encoding="utf-8")
    (shadow / "capture.py").write_text('print(\'{"rows": {"shadow": []}}\')', encoding="utf-8")

    assert set(_capture(project).rows) == {"tickets"}


def test_a_project_cannot_tell_the_changed_fixtures_run_by_its_path(tmp_path: Path) -> None:
    project = _reference(tmp_path, "e04")
    xml = (project / _XML).read_text(encoding="utf-8")
    rule = "'high' if int(source_row.total_cents) >= 5000 else 'standard'"
    (project / _XML).write_text(
        xml.replace(
            f'script="{rule}"',
            f"script=\"'x' if {_OS}['getcwd']().rsplit('/', 1)[1] in ('3', 'fixtures_changed') else {rule}\"",
        ),
        encoding="utf-8",
    )

    assert _failed(project, "e04") == set()


def test_unreadable_output_files_are_skipped_not_a_crash(tmp_path: Path) -> None:
    (tmp_path / "output" / "run").mkdir(parents=True)
    (tmp_path / "output" / "run" / "broken.json").write_text('{"a": 1}\n{"a": 2}\n', encoding="utf-8")
    (tmp_path / "output" / "run" / "object.json").write_text('{"a": 1}', encoding="utf-8")
    (tmp_path / "output" / "run" / "good.json").write_text("[1, 2]", encoding="utf-8")

    assert json_outputs(tmp_path) == {"good": [1, 2]}


def test_rows_that_json_cannot_encode_fail_the_check_but_do_not_crash() -> None:
    observed = Observed(None, None, {"p": [{"a": datetime(2026, 1, 1), "b": {1, 2}}]})

    assert ExactRows(kind="exact_rows", product="p", rows=[{"a": 1}]).failure(observed) is not None
    assert Unique(kind="unique", product="p", field="b").failure(observed) is not None


@pytest.mark.parametrize("case", [case for case in _ALL_CASES if (CASES / case / "fixtures").is_dir()])
def test_case_fixtures_follow_the_project_file_standard(case: str) -> None:
    """Business data is ``*.ent.csv`` and a distribution ``*.wgt.csv``: UTF-8 without a BOM, each line pipe-separated.
    The CE default separator is the pipe, so the reference names no separator."""
    for path in (path for path in (CASES / case).glob("fixtures*/**/*") if path.is_file()):
        assert path.name.endswith((".ent.csv", ".wgt.csv")), path
        raw = path.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), path
        assert all("|" in line for line in raw.decode("utf-8").splitlines()), path
    for xml in (CASES / case / "reference").rglob("*.xml"):
        assert "separator" not in xml.read_text(encoding="utf-8").casefold(), xml


def test_the_e06_function_sets_are_the_names_in_each_weighted_file() -> None:
    """The oracle states each closed set literally; this keeps it equal to the first column of the file it checks."""
    spec = OracleSpec.model_validate_json((CASES / "e06" / "oracle.json").read_text(encoding="utf-8"))
    checks = [check for check in spec.checks if isinstance(check, ValueIn) and check.field == "function"]
    assert {check.fixtures for check in checks} == {"fixtures", "fixtures_changed"}
    for check in checks:
        lines = (CASES / "e06" / check.fixtures / "functions.wgt.csv").read_text(encoding="utf-8").splitlines()
        assert sorted(check.values) == sorted(line.split("|")[0] for line in lines)


def test_every_case_has_broken_variants() -> None:
    assert {broken.case for broken in _BROKEN} == set(_ALL_CASES)


@pytest.mark.parametrize("case", ["e06", "e07"])
def test_every_check_of_the_complex_cases_fails_in_some_variant(case: str) -> None:
    """A check that no variant or cheat fails is not proven to fail at all."""
    spec = OracleSpec.model_validate_json((CASES / case / "oracle.json").read_text(encoding="utf-8"))
    failed = {label for broken in _BROKEN if broken.case == case for label in broken.fails}
    failed |= {label for (cheat_case, _), (_, fails) in _CHEATS.items() if cheat_case == case for label in fails}

    assert {check.label() for check in spec.checks} - failed == set()


def test_oracle_ignores_the_agents_own_acceptance(tmp_path: Path) -> None:
    project = _reference(tmp_path, "e01")
    (project / _ACCEPTANCE).write_text('{"version": "5.0", "expectations": []}', encoding="utf-8")
    (project / _XML).write_text((project / _XML).read_text(encoding="utf-8").replace('count="25"', 'count="3"'))

    assert "exact_count:tickets" in _failed(project, "e01")


def test_oracle_reports_a_missing_project_as_failed_checks(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()

    verdict = evaluate("e01", empty)

    assert not verdict.passed
    assert not any(result.passed for result in verdict.checks)


# Build raises on two top-level names with the same last segment; the capture names both "tickets".
def test_a_build_that_raises_fails_build_ready_and_still_gives_a_verdict(tmp_path: Path) -> None:
    project = _reference(tmp_path, "e01")
    xml = (project / _XML).read_text(encoding="utf-8")
    (project / _XML).write_text(xml.replace("</setup>", '<generate name="x|tickets" count="1"/></setup>'))

    verdict = evaluate("e01", project)

    assert {result.check: result.reason for result in verdict.checks}["build_ready"] == "Build raised ValidationError"


def test_verdict_carries_no_row_values(tmp_path: Path) -> None:
    text = evaluate("e04", _reference(tmp_path, "e04")).model_dump_json()

    assert "O-100" not in text
    assert "C-10" not in text


# --- transcript audit ---------------------------------------------------------------------------------------


def _line(*blocks: dict) -> str:
    return json.dumps({"type": "assistant", "message": {"role": "assistant", "content": list(blocks)}})


def _call(name: str, **tool_input: str) -> dict:
    return {"type": "tool_use", "id": "t1", "name": name, "input": tool_input}


def _transcript(tmp_path: Path, *lines: str) -> Path:
    prompt = json.dumps({"type": "user", "message": {"role": "user", "content": "Do not read AGENTS.md."}})
    path = tmp_path / "agent.jsonl"
    path.write_text("\n".join([prompt, *lines]) + "\n", encoding="utf-8")
    return path


def _audit(transcript: Path, run: Path, venv: Path, canary: str | None = None) -> list[FindingKind]:
    allow = [run, venv / "bin" / "datamimic"]
    return [finding.kind for finding in audit(transcript, allow=allow, forbid=[Path("/repo")], canary=canary)]


def test_clean_transcript_has_no_findings(tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"
    transcript = _transcript(
        tmp_path,
        _line(_call("Bash", command=f"cd {run} && {venv}/bin/datamimic authoring build . | head -c 500")),
        _line(_call("Write", file_path=f"{run}/datamimic.xml", content="<setup/>")),
        _line(_call("Glob", pattern="**/*.xml", path=str(run))),
        _line({"type": "text", "text": "I read AGENTS.md"}),
    )

    assert _audit(transcript, run, venv, canary="canary-0123") == []


def test_reading_the_installed_source_is_flagged(tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"
    source = f"{venv}/lib/python3.11/site-packages/datamimic_ce/__init__.py"

    assert _audit(_transcript(tmp_path, _line(_call("Read", file_path=source))), run, venv) == [
        FindingKind.OUTSIDE_ALLOWED
    ]


@pytest.mark.parametrize("tool", ["Skill", "WebFetch", "WebSearch", "Agent", "Task", "NotebookEdit"])
def test_tool_outside_the_allowlist_is_flagged(tool: str, tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"

    assert _audit(_transcript(tmp_path, _line(_call(tool, prompt="x"))), run, venv) == [FindingKind.TOOL]


def test_absolute_glob_pattern_outside_the_run_directory_is_flagged(tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"
    transcript = _transcript(tmp_path, _line(_call("Glob", pattern=f"{venv}/lib/**/*.py")))

    assert _audit(transcript, run, venv) == [FindingKind.OUTSIDE_ALLOWED]


_OUT, _REPO = [FindingKind.OUTSIDE_ALLOWED], [FindingKind.FORBIDDEN_ROOT, FindingKind.OUTSIDE_ALLOWED]


@pytest.mark.parametrize(
    ("pattern", "kinds"),
    [
        ("/etc/*", _OUT),
        ("{home}/.claude/**", _OUT),
        ("~/.claude/**", _OUT),
        ("{run}*/datamimic.xml", _OUT),  # run* also matches the siblings of the run directory
        ("{run}/**/../*", _OUT),  # ** can match no directory, so .. climbs out of the run directory
        ("/repo/benchmarks/authoring_eval/cases/**/reference/*", _REPO),
        ("/repo*/x", _OUT),  # the root is /, outside the run directory; not proven to touch /repo
        ("{run}/**/*.xml", []),
        ("{run}/datamimic.xml", []),
    ],
)
def test_an_absolute_glob_pattern_without_a_path_is_checked_from_its_root(
    pattern: str, kinds: list[FindingKind], tmp_path: Path
) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"
    glob = pattern.format(run=run, home=Path.home())

    assert _audit(_transcript(tmp_path, _line(_call("Glob", pattern=glob))), run, venv) == kinds


def test_a_home_relative_read_is_checked(tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"

    assert _audit(_transcript(tmp_path, _line(_call("Read", file_path="~/.claude/x.json"))), run, venv) == _OUT


# --- regressions from the first real runs (transcript line numbers of the reports) ---

_TMP = "/private/var/folders/sn/ws6fv3bj5tv3gz79ycxkprk00000gn/T"


def test_floor_division_in_a_heredoc_is_not_a_path(tmp_path: Path) -> None:
    """e03, line 72."""
    run, venv = Path(f"{_TMP}/dm-eval-a5imyqwq/run"), Path(f"{_TMP}/dm-single-CfvHjGvC/v-e03")
    command = (
        "mkdir -p acceptance && cat > datamimic.xml <<'EOF'\n<setup rngSeed=\"56606\">\n"
        '    <generate name="slots" count="12">\n        <variable name="i" generator="IncrementGenerator"/>\n'
        '        <key name="depot_id" script="(i - 1) // 4 + 1"/>\n'
        '        <key name="slot_id" script="((i - 1) // 4 + 1) * 100 + (i - 1) % 4 + 1"/>\n'
        f"    </generate>\n</setup>\nEOF\n{venv}/bin/datamimic authoring build . 2>&1"
    )
    transcript = _transcript(tmp_path, _line(_call("Bash", command=command)))

    assert _audit(transcript, run, venv) == []


@pytest.mark.parametrize(
    ("command", "kinds"),
    [
        ('python3 -c "print(7 // 2, 7//2)"', []),
        ("cat //etc/passwd", [FindingKind.OUTSIDE_ALLOWED]),  # POSIX reads // as /
        ("cat ///etc/passwd", [FindingKind.OUTSIDE_ALLOWED]),
    ],
)
def test_a_double_slash_is_a_path_only_with_a_name_after_it(
    command: str, kinds: list[FindingKind], tmp_path: Path
) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"

    assert _audit(_transcript(tmp_path, _line(_call("Bash", command=command))), run, venv) == kinds


_SESSION = "ce382f35-85d8-4fbc-89c7-acb61bf5a4f3"
_E01_RUN = Path(f"{_TMP}/dm-eval-ly3uyh84/run")
_E01_SLUG = "-private-var-folders-sn-ws6fv3bj5tv3gz79ycxkprk00000gn-T-dm-eval-ly3uyh84-run"


def _read_saved_output(path: str) -> str:
    """e01, line 29: the CLI saved a long tool result and told the model to read it there."""
    return f"F={path}; python3 -c \"\nimport json,sys\nd=json.load(open('$F'))\n\" 2>&1 | head -80"


@pytest.mark.parametrize(
    ("relative", "kinds"),
    [
        (f"{_E01_SLUG}/{_SESSION}/tool-results/b94d2b45t.txt", []),
        (f"{_E01_SLUG}/{_SESSION}/tool-results", []),
        (f"{_E01_SLUG}/00000000-0000-4000-8000-000000000000/tool-results/x.txt", [FindingKind.OUTSIDE_ALLOWED]),
        (f"{_E01_SLUG}/{_SESSION}.jsonl", [FindingKind.OUTSIDE_ALLOWED]),
        (f"{_E01_SLUG}-x/{_SESSION}/tool-results/x.txt", [FindingKind.OUTSIDE_ALLOWED]),
        (f"{_E01_SLUG}/{_SESSION}/tool-results/../../x.jsonl", [FindingKind.OUTSIDE_ALLOWED]),
    ],
)
def test_only_the_tool_results_of_the_runs_own_session_are_allowed(
    relative: str, kinds: list[FindingKind], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    venv = tmp_path / "venv"
    command = _read_saved_output(f"{tmp_path}/home/.claude/projects/{relative}")
    allow = [_E01_RUN, venv / "bin" / "datamimic", run_subject.own_tool_results(_E01_RUN, _SESSION)]

    findings = audit(_transcript(tmp_path, _line(_call("Bash", command=command))), allow=allow, forbid=[])

    assert [finding.kind for finding in findings] == kinds


def test_the_tool_results_slug_replaces_every_character_but_letters_and_digits(tmp_path: Path) -> None:
    slug = run_subject.own_tool_results(tmp_path / "dm-eval-z8_zcb7h" / "run", _SESSION).parts[-3]

    assert slug.endswith("-dm-eval-z8-zcb7h-run")
    assert slug.replace("-", "").isalnum()


def test_a_session_id_that_is_not_a_uuid_allows_nothing(tmp_path: Path) -> None:
    assert run_subject.own_tool_results(tmp_path, "../..") is None


def test_a_path_that_does_not_exist_is_still_an_access_attempt(tmp_path: Path) -> None:
    """e05, line 51: a typo for /var/folders."""
    run = Path("/var/folders/sn/ws6fv3bj5tv3gz79ycxkprk00000gn/T/dm-eval-1e4cn30o/run")
    command = f"cd /var/floders 2>/dev/null; cd {run} && sed -n '567,580p' $TMPDIR/exp.txt"

    findings = audit(_transcript(tmp_path, _line(_call("Bash", command=command))), allow=[run], forbid=[])

    assert [(finding.kind, finding.detail) for finding in findings] == [
        (
            FindingKind.OUTSIDE_ALLOWED,
            "/var/floders: an access attempt outside the allowed roots, also if it does not exist",
        )
    ]


def test_canary_anywhere_in_the_transcript_is_flagged(tmp_path: Path) -> None:
    """A relative `cat ../AGENTS.md` passes the path checks; its tool result still carries the token."""
    run, venv = tmp_path / "run", tmp_path / "venv"
    tool_result = {"type": "tool_result", "content": "canary-0123"}
    result = {"type": "user", "message": {"role": "user", "content": [tool_result]}}
    transcript = _transcript(tmp_path, _line(_call("Bash", command="cat ../AGENTS.md")), json.dumps(result))

    assert _audit(transcript, run, venv, canary="canary-0123") == [FindingKind.AGENTS_FILE, FindingKind.CANARY]


def test_xml_in_a_heredoc_is_not_a_path(tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"
    command = f'cat > {run}/datamimic.xml <<\'EOF\'\n<setup>\n  <key name="x" constant="1"/>\n</setup>\nEOF'
    transcript = _transcript(tmp_path, _line(_call("Bash", command=command)))

    assert _audit(transcript, run, venv) == []


def test_repository_read_and_agents_file_are_flagged(tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"
    transcript = _transcript(tmp_path, _line(_call("Read", file_path="/repo/AGENTS.md")))

    assert set(_audit(transcript, run, venv)) == {
        FindingKind.AGENTS_FILE,
        FindingKind.FORBIDDEN_ROOT,
        FindingKind.OUTSIDE_ALLOWED,
    }


def test_shell_path_outside_the_run_directory_is_flagged(tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"
    transcript = _transcript(tmp_path, _line(_call("Bash", command="cat /etc/hosts")))

    assert _audit(transcript, run, venv) == [FindingKind.OUTSIDE_ALLOWED]


def test_line_separator_inside_a_tool_call_does_not_split_a_record(tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"
    line = json.dumps(
        {"message": {"role": "assistant", "content": [_call("Bash", command="echo \u2028 /etc/hosts")]}},
        ensure_ascii=False,
    )

    assert _audit(_transcript(tmp_path, line), run, venv) == [FindingKind.OUTSIDE_ALLOWED]


# --- the new check kinds, one by one ---------------------------------------------------------------------------


def test_whole_number_rejects_bool_float_and_text() -> None:
    check = WholeNumber(kind="whole_number", product="p", field="id")

    assert check.failure(Observed(None, None, {"p": [{"id": 1}, {"id": 2}]})) is None
    for bad in (True, 1.0, "1", None):
        assert check.failure(Observed(None, None, {"p": [{"id": 1}, {"id": bad}]})) is not None


def test_text_rejects_a_number_an_empty_text_and_a_missing_value() -> None:
    check = Text(kind="text", product="p", field="title")

    assert check.failure(Observed(None, None, {"p": [{"title": "a"}, {"title": "b"}]})) is None
    for bad in (1, 1.5, True, "", None):
        assert check.failure(Observed(None, None, {"p": [{"title": "a"}, {"title": bad}]})) is not None
    assert check.failure(Observed(None, None, {"p": [{"title": "a"}, {}]})) is not None


def test_whole_number_on_the_parent_key_is_what_catches_orphans() -> None:
    """unique + per_parent_count + exact_count prove that no child is an orphan only while the parent keys stay
    distinct as text: per_parent_count groups by str(), so the parents 1 and "1" merge and children 99 hide."""
    parents, children = FieldRef(product="p", field="id"), FieldRef(product="c", field="pid")
    observed = Observed(None, None, {"p": [{"id": 1}, {"id": "1"}], "c": [{"pid": v} for v in (1, 1, 99, 99)]})

    assert Unique(kind="unique", product="p", field="id").failure(observed) is None
    assert PerParentCount(kind="per_parent_count", child=children, parent=parents, n=2).failure(observed) is None
    assert ExactCount(kind="exact_count", product="c", n=4).failure(observed) is None
    assert WholeNumber(kind="whole_number", product="p", field="id").failure(observed) is not None


def test_repeatable_compares_the_second_run_in_order() -> None:
    check = Repeatable(kind="repeatable")
    rows = {"p": [{"a": 1}, {"a": 2}]}

    assert check.failure(Observed(None, None, rows, second_rows={"p": [{"a": 1}, {"a": 2}]})) is None
    assert check.failure(Observed(None, None, rows, second_rows={"p": [{"a": 2}, {"a": 1}]})) is not None
    assert check.failure(Observed(None, None, rows, second_error="Timeout")) is not None


def test_value_in_with_a_fixtures_set_reads_the_rows_of_that_run() -> None:
    check = ValueIn(kind="value_in", product="p", field="f", values=["X", "Y"], fixtures="fixtures_changed")
    observed = Observed(
        None,
        None,
        {"p": [{"f": "OTHER"}]},  # the first run is not the one this check reads
        {"fixtures_changed": Output(None, rows={"p": [{"f": "X"}, {"f": "Y"}]})},
    )

    assert check.label() == "value_in:p.f:fixtures_changed"
    assert check.failure(observed) is None
    outside = {"fixtures_changed": Output(None, rows={"p": [{"f": "X"}, {"f": "Z"}]})}
    assert check.failure(Observed(None, None, {}, outside)) == "1 values outside the allowed set"
    assert check.failure(Observed(None, None, {}, {"fixtures_changed": Output("Timeout")})) == "run failed: Timeout"
    assert check.failure(Observed(None, None, {})) == "no run with fixtures_changed"
    assert ValueIn(kind="value_in", product="p", field="f", values=["X"]).label() == "value_in:p.f"


def test_unique_together_rejects_a_repeated_pair_only() -> None:
    check = UniqueTogether(kind="unique_together", product="p", fields=["a", "b"])

    # each field repeats, but no pair does
    assert (
        check.failure(Observed(None, None, {"p": [{"a": 1, "b": "x"}, {"a": 1, "b": "y"}, {"a": 2, "b": "x"}]})) is None
    )
    assert check.failure(Observed(None, None, {"p": [{"a": 1, "b": "x"}, {"a": 1, "b": "x"}]})) is not None
    for bad in (None, [1], {}):
        assert check.failure(Observed(None, None, {"p": [{"a": 1, "b": bad}]})) is not None
    assert check.failure(Observed(None, None, {"p": [{"a": 1}]})) is not None
    assert check.label() == "unique_together:p.a+b"


def _exists(rows: list[dict[str, object]], targets: list[dict[str, object]], window: bool = False) -> str | None:
    bounds = DateWindow(date="day", start="start", end="end") if window else None
    check = RowExistsIn(kind="row_exists_in", product="c", target="t", fields=["k"], window=bounds)
    return check.failure(Observed(None, None, {"c": rows, "t": targets}))


def test_row_exists_in_compares_the_fields_with_their_json_types() -> None:
    assert _exists([{"k": 1}, {"k": 2}], [{"k": 1}, {"k": 2}, {"k": 3}]) is None
    assert _exists([{"k": 4}], [{"k": 1}]) is not None
    # a parent key 1 is not the text "1", a float or a bool
    for other in ("1", 1.0, True):
        assert _exists([{"k": other}], [{"k": 1}]) is not None
    assert _exists([{}], [{"k": None}]) is not None  # a missing field matches nothing, not even a null


@pytest.mark.parametrize(
    ("day", "start", "end", "matches"),
    [
        ("2026-02-28", "2026-03-01", "2026-03-31", False),  # start - 1
        ("2026-03-01", "2026-03-01", "2026-03-31", True),  # start
        ("2026-03-31", "2026-03-01", "2026-03-31", True),  # end: the expiry day is valid
        ("2026-04-01", "2026-03-01", "2026-03-31", False),  # end + 1
        ("2026-03-10", "2026-03-01", None, False),  # no expiry date is not an unlimited validity
        ("2026-03-10", "2026-03-01", "", False),
        ("2026-03-10", None, "2026-03-31", False),
        ("2026-03-10", "2026-03-01", "20260331", False),  # date.fromisoformat accepts it, the prompt does not
        ("2026-03-10", "2026-03-01", "2026-03-31 00:00:00", False),
        ("2026-03-10", "2026-03-01", "31.03.2026", False),
        ("2026-3-10", "2026-03-01", "2026-03-31", False),
        ("2026-02-30", "2026-02-01", "2026-03-31", False),  # not a day of the calendar
    ],
)
def test_row_exists_in_window_includes_both_bounds_and_needs_real_dates(
    day: str, start: str | None, end: str | None, matches: bool
) -> None:
    found = _exists([{"k": 1, "day": day}], [{"k": 1, "start": start, "end": end}], window=True)

    assert (found is None) is matches


def test_row_exists_in_window_takes_any_matching_target_row() -> None:
    targets = [
        {"k": 1, "start": "2026-01-01", "end": None},
        {"k": 1, "start": "2026-03-01", "end": "2026-03-31"},
        {"k": 2, "start": "2026-01-01", "end": "2026-12-31"},
    ]

    assert _exists([{"k": 1, "day": "2026-03-15"}], targets, window=True) is None
    # the window of another key does not count
    assert _exists([{"k": 1, "day": "2026-06-15"}], targets, window=True) is not None
    # a bound field that the target row lacks is no bound
    assert _exists([{"k": 1, "day": "2026-03-15"}], [{"k": 1, "start": "2026-03-01"}], window=True) is not None


def test_row_exists_in_reports_a_missing_product() -> None:
    check = RowExistsIn(kind="row_exists_in", product="c", target="t", fields=["k"])

    assert check.failure(Observed(None, None, {"c": [{"k": 1}]})) == "product t was not produced"
    assert check.label() == "row_exists_in:c->t"


def _dates(*values: object, missing: int = 0) -> str | None:
    check = DateRange(kind="date_range", product="p", field="d", min="2026-03-01", max="2026-03-31", missing=missing)
    return check.failure(Observed(None, None, {"p": [{"d": value} for value in values]}))


def test_date_range_includes_both_bounds() -> None:
    assert _dates("2026-03-01", "2026-03-31", "2026-03-15") is None
    for bad in ("2026-02-28", "2026-04-01", "2026-03-32", "20260315", "2026-03-15T00:00:00", 20260315, None):
        assert _dates("2026-03-01", bad) is not None, bad


def test_date_range_counts_the_null_values_exactly() -> None:
    assert _dates("2026-03-01", None, missing=1) is None
    assert _dates("2026-03-01", "2026-03-02", missing=1) is not None  # min - 1 nulls
    assert _dates(None, None, missing=1) is not None  # max + 1 nulls
    assert _dates("2026-03-01", "", missing=1) is not None  # an empty text is not a missing value
    check = DateRange(kind="date_range", product="p", field="d", min="2026-03-01", max="2026-03-31", missing=1)
    assert check.failure(Observed(None, None, {"p": [{"d": "2026-03-01"}, {}]})) is not None  # an absent field


def test_a_doubly_nested_product_is_captured_by_its_own_name(tmp_path: Path) -> None:
    """The engine names it ``inner|leaf``; the checks and Build name a product by its own name."""
    project = tmp_path / "project"
    project.mkdir()
    (project / _XML).write_text(
        """<setup rngSeed="1">
    <generate name="outer" count="1">
        <key name="a" constant="1"/>
        <generate name="inner" count="1">
            <key name="b" constant="2"/>
            <generate name="leaf" count="2">
                <key name="c" constant="3"/>
            </generate>
        </generate>
    </generate>
</setup>""",
        encoding="utf-8",
    )

    assert _capture(project).rows == {"outer": [{"a": "1"}], "inner": [{"b": "2"}], "leaf": [{"c": "3"}] * 2}


def test_seed_is_reads_the_entry_descriptor_not_the_agents_acceptance_file(tmp_path: Path) -> None:
    project = _reference(tmp_path, "e01")
    (project / _ACCEPTANCE).write_text('{"version": "5.0", "expectations": [], "seed": 1}', encoding="utf-8")
    (project / _XML).write_text(
        (project / _XML).read_text(encoding="utf-8").replace('rngSeed="10421"', 'rngSeed="10421 "'), encoding="utf-8"
    )

    assert "seed_is" in _failed(project, "e01")


# --- the subject runner: the isolation checks ------------------------------------------------------------------

_TOKEN = "canary-0123"
# The two lines a real 2.1.304 debug log holds with --safe-mode and the sandbox settings of the runner.
_SAFE_MODE_LINE = "[DEBUG] $.fs.ancestors (cc-plugin-agents-md): project memory is off\n"
_SANDBOX_LINE = (
    "[INFO] Sandbox: ignoring permission rules and sandbox.filesystem entries "
    "from disabled setting source userSettings\n"
)
_MARKERS = _SAFE_MODE_LINE + _SANDBOX_LINE


@dataclass(frozen=True)
class _Run:
    base: Path
    run_dir: Path
    transcript: Path
    debug_log: Path

    @property
    def canary_files(self) -> list[Path]:
        return [self.base / "AGENTS.md", self.base / "CLAUDE.md"]


def _blind_run(tmp_path: Path, init: dict | None = None, result: dict | None = None, debug: str = "") -> _Run:
    """A transcript shaped like `claude -p --output-format stream-json` (key names from a real 2.1.304 run)."""
    run = _Run(tmp_path, tmp_path / "run", tmp_path / "transcript.jsonl", tmp_path / "debug.log")
    run.run_dir.mkdir()
    (run.run_dir / _XML).write_text("<setup/>", encoding="utf-8")
    records = [
        {
            "type": "system",
            "subtype": "init",
            "cwd": str(run.run_dir),
            "tools": ["Bash", "Edit", "Glob", "Grep", "Read", "Write"],
            "mcp_servers": [],
            "slash_commands": [],
            "skills": [],
            "plugins": [{"name": "installed-but-disabled"}],
        }
        | (init or {}),
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "terminal_reason": "completed",
            "permission_denials": [],
        }
        | (result or {}),
    ]
    run.transcript.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
    run.debug_log.write_text(_MARKERS + debug)
    return run


def _problems(run: _Run) -> list[str]:
    return isolation_problems(run.transcript, run.debug_log, run.run_dir, _TOKEN, run.canary_files)


def test_a_blind_run_has_no_isolation_problems(tmp_path: Path) -> None:
    assert _problems(_blind_run(tmp_path)) == []


@pytest.mark.parametrize(
    "change",
    [
        {"init": {"tools": ["Bash", "Edit", "Glob", "Grep", "Read", "Write", "WebFetch"]}},
        {"init": {"skills": ["generate-test-data"]}},
        {"init": {"mcp_servers": [{"name": "datamimic"}]}},
        {"init": {"slash_commands": ["compact"]}},
        {"init": {"subtype": "status"}},  # no init message at all
        {"result": {"is_error": True, "terminal_reason": "api_error"}},
        {"result": {"permission_denials": [{"tool_name": "Write"}]}},
        {"result": {"type": "assistant"}},  # no result message at all
        {"debug": '[DEBUG] "Hook SessionStart:startup success: {"additionalContext": "..."}"\n'},
    ],
)
def test_isolation_problem_is_reported(change: dict, tmp_path: Path) -> None:
    assert _problems(_blind_run(tmp_path, **change)) != []


def test_a_canary_file_named_in_the_debug_log_is_an_isolation_problem(tmp_path: Path) -> None:
    run = _blind_run(tmp_path, debug=f"[DEBUG] no CLAUDE.md found; AGENTS.md loaded: {tmp_path}/AGENTS.md\n")

    assert _problems(run) == ["the CLI found AGENTS.md"]


def test_a_canary_file_is_found_under_the_other_spelling_of_its_path(tmp_path: Path) -> None:
    """/var and /private/var name the same place on macOS; the CLI logs one, the runner may hold the other."""
    real = tmp_path / "real"
    real.mkdir()
    (tmp_path / "link").symlink_to(real)
    run = _blind_run(real, debug=f"[DEBUG] AGENTS.md loaded: {real}/AGENTS.md\n")
    linked = [tmp_path / "link" / "AGENTS.md"]

    assert isolation_problems(run.transcript, run.debug_log, run.run_dir, _TOKEN, linked) == ["the CLI found AGENTS.md"]


@pytest.mark.parametrize("log", [None, "", _SANDBOX_LINE, _SAFE_MODE_LINE])
def test_a_debug_log_without_both_markers_is_an_isolation_problem(log: str | None, tmp_path: Path) -> None:
    """Missing, empty, without safe mode, without the sandbox: the debug-log checks cannot pass silently."""
    run = _blind_run(tmp_path)
    if log is None:
        run.debug_log.unlink()
    else:
        run.debug_log.write_text(log, encoding="utf-8")

    assert _problems(run) != []


def test_a_debug_log_that_is_not_utf8_is_a_problem_and_is_still_read(tmp_path: Path) -> None:
    run = _blind_run(tmp_path)
    run.debug_log.write_bytes(_MARKERS.encode() + b"\xff\xfe AGENTS.md loaded: " + str(tmp_path / "AGENTS.md").encode())

    assert _problems(run) == ["the debug log is not UTF-8", "the CLI found AGENTS.md"]


def test_a_transcript_line_that_is_not_json_is_a_finding_not_a_crash(tmp_path: Path) -> None:
    run = _blind_run(tmp_path)
    with run.transcript.open("a", encoding="utf-8") as transcript:
        transcript.write('not json\n{"type": "assistant", "message": {"role": "assi')

    assert _problems(run) == []
    assert _audit(run.transcript, run.run_dir, tmp_path / "venv") == [FindingKind.UNREADABLE] * 2


def test_the_canary_in_a_file_of_the_run_directory_is_an_isolation_problem(tmp_path: Path) -> None:
    run = _blind_run(tmp_path)
    (run.run_dir / "notes.txt").write_text(f"code word {_TOKEN}", encoding="utf-8")

    assert _problems(run) != []


def test_a_cwd_other_than_the_run_directory_is_an_isolation_problem(tmp_path: Path) -> None:
    assert _problems(_blind_run(tmp_path, init={"cwd": str(tmp_path)})) != []


def test_the_brief_fills_every_placeholder(tmp_path: Path) -> None:
    text = brief("e01", tmp_path / "venv", tmp_path / "run")

    assert (CASES / "e01" / "prompt.md").read_text(encoding="utf-8") in text
    assert f"{tmp_path}/venv/bin/datamimic" in text
    assert not re.search(r"<(venv|run-dir|turn-limit|task)>", text)


# --- the subject runner end to end, with a stand-in for the claude CLI ----------------------------------------

_FAKE_CLAUDE = """#!{python}
import json, os, subprocess, sys, time
from pathlib import Path
args = sys.argv[1:]
debug = Path(args[args.index("--debug-file") + 1])
debug.write_text({markers!r})
(debug.parent / "argv.json").write_text(json.dumps(args))
tools = ["Bash", "Edit", "Glob", "Grep", "Read", "Write"]
init = {{"type": "system", "subtype": "init", "cwd": os.getcwd(), "tools": tools, "session_id": {session!r}}}
print(json.dumps(init | {{"mcp_servers": [], "slash_commands": [], "skills": []}}))
print(json.dumps({{"type": "result", "subtype": "success", "is_error": False, "permission_denials": []}}), flush=True)
{tail}
"""


def _fake_claude(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tail: str) -> str:
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))  # the run's base directory, not the system's
    path = tmp_path / "claude"
    script = _FAKE_CLAUDE.format(python=sys.executable, markers=_MARKERS, session=_SESSION, tail=tail)
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)
    return str(path)


def test_a_clean_run_is_reported_clean_and_starts_the_cli_with_the_bash_sandbox(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report = run_subject.run("e01", tmp_path / "venv", "haiku", _fake_claude(tmp_path, monkeypatch, "sys.exit(0)"))

    assert (report["problems"], report["findings"]) == ([], [])
    argv = json.loads((Path(str(report["run_dir"])).parent / "argv.json").read_text(encoding="utf-8"))
    sandbox = json.loads(argv[argv.index("--settings") + 1])["sandbox"]
    assert sandbox["enabled"] is True
    assert sandbox["failIfUnavailable"] is True
    assert sandbox["allowUnsandboxedCommands"] is False
    assert str(run_subject.REPO_ROOT) in sandbox["filesystem"]["denyRead"]


def test_a_run_that_reads_its_own_saved_tool_output_is_clean(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    tail = (
        "import re\n"
        "slug = re.sub('[^A-Za-z0-9]', '-', os.path.realpath(os.getcwd()))\n"
        f"saved = f'{tmp_path}/home/.claude/projects/{{slug}}/{_SESSION}/tool-results/x.txt'\n"
        "call = {'type': 'tool_use', 'id': 't', 'name': 'Read', 'input': {'file_path': saved}}\n"
        "print(json.dumps({'type': 'assistant', 'message': {'role': 'assistant', 'content': [call]}}))"
    )

    report = run_subject.run("e01", tmp_path / "venv", "haiku", _fake_claude(tmp_path, monkeypatch, tail))

    assert (report["problems"], report["findings"]) == ([], [])


def test_a_cli_exit_code_other_than_zero_is_a_problem(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report = run_subject.run("e01", tmp_path / "venv", "haiku", _fake_claude(tmp_path, monkeypatch, "sys.exit(3)"))

    assert report["problems"] == ["the CLI exited with 3"]


def test_a_timeout_is_a_problem_and_kills_the_children_of_the_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(run_subject, "_TIMEOUT_SECONDS", 2)
    tail = (
        'child = subprocess.Popen(["sleep", "60"])\n'
        '(debug.parent / "child.pid").write_text(str(child.pid))\n'
        "time.sleep(60)"
    )

    report = run_subject.run("e01", tmp_path / "venv", "haiku", _fake_claude(tmp_path, monkeypatch, tail))

    assert report["problems"] == ["the CLI did not finish in 2 s"]
    child = int((Path(str(report["run_dir"])).parent / "child.pid").read_text(encoding="utf-8"))
    deadline = time.monotonic() + 5
    while _alive(child) and time.monotonic() < deadline:
        time.sleep(0.1)
    assert not _alive(child)


def _alive(pid: int) -> bool:
    """A zombie is dead. os.kill(pid, 0) succeeds on a zombie; the slim CI image has /proc but no ps."""
    if Path("/proc").is_dir():
        try:
            return Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").rsplit(")", 1)[1].split()[0] != "Z"
        except FileNotFoundError:
            return False
    state = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, check=False).stdout
    return bool(state.strip()) and not state.strip().startswith("Z")


def test_a_killed_process_that_no_one_reaps_is_not_alive() -> None:
    """The killed child stays a zombie when its new parent never reaps it: PID 1 of the CI container is `tail`."""
    child = subprocess.Popen(["sleep", "60"])
    try:
        assert _alive(child.pid)
        child.kill()  # no wait(): the process stays a zombie
        deadline = time.monotonic() + 5
        while _alive(child.pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        assert not _alive(child.pid)
    finally:
        child.kill()
        child.wait()


def test_a_double_leading_slash_names_the_same_place_as_a_single_one(tmp_path):
    from benchmarks.authoring_eval.audit_transcript import _under

    assert _under(f"/{tmp_path}/x", [tmp_path])
    assert not _under("//etc/passwd", [tmp_path])
