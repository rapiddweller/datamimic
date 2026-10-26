# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The blind-agent eval oracle and transcript audit (#412): each reference project passes, each deliberately
broken variant fails exactly the checks it should, and the audit flags forbidden actions."""

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pytest

from benchmarks.authoring_eval.audit_transcript import FindingKind, audit
from benchmarks.authoring_eval.oracle import (
    CASES,
    ExactRows,
    Observed,
    Repeatable,
    Unique,
    WholeNumber,
    evaluate,
    json_outputs,
)

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
_FLAG = "list({'alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf', 'hotel'}).index('bravo') % 2"


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
        frozenset({"unique:tickets.ticket_id", "whole_number:tickets.ticket_id"}),  # constant= is text
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
        frozenset({"unique:slots.slot_id", "build_ready"}),
    ),
    Broken(
        "e03",
        "token_in_output",
        {_XML: [('<variable name="token"', '<key name="token"')]},
        frozenset({"exact_fields:slots", "build_ready"}),
    ),
    Broken(
        "e03",
        "wrong_state",
        {_XML: [('constant="FREE"', 'constant="BUSY"')]},
        frozenset({"value_in:slots.state"}),
    ),
    Broken(
        "e04",
        "total_left_as_text",
        {_XML: [('script="int(source_row.total_cents)"', 'script="source_row.total_cents"')]},
        frozenset({"exact_rows:priced_orders"}),
    ),
    Broken(
        "e04",
        "wrong_priority_threshold",
        {_XML: [(">= 5000", ">= 4000")]},
        frozenset({"exact_rows:priced_orders"}),
    ),
    Broken(
        "e04",
        "no_json_target",
        {_XML: [(' target="JSON"', "")]},
        frozenset({"output_rows:priced_orders"}),
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
    # interpreter's hash seed, so only a second run in a fresh interpreter shows it.
    Broken(
        "e01",
        "hash_ordered_hours",
        {_XML: [('name="estimate_hours" type="int" min="1" max="40"', f'name="estimate_hours" script="1 + {_FLAG}"')]},
        frozenset({"repeatable"}),
    ),
    Broken(
        "e02",
        "hash_ordered_amount",
        {
            _XML: [
                ('name="amount_cents" type="int" min="500" max="20000"', f'name="amount_cents" script="500 + {_FLAG}"')
            ]
        },
        frozenset({"repeatable"}),
    ),
    Broken(
        "e03",
        "hash_ordered_slot_ids",
        {
            _XML: [
                ('script="parent.depot_id * 100 + token"', f'script="parent.depot_id * 100 + token + 50 * ({_FLAG})"')
            ]
        },
        frozenset({"repeatable"}),
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
        frozenset({"repeatable"}),
    ),
    Broken(
        "e05",
        "hash_ordered_sale_price",
        {_XML: [("list_price * 8 // 10", f"list_price * 8 // 10 + {_FLAG}")]},
        frozenset({"repeatable"}),
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
        frozenset({"whole_number:slots.slot_id"}),
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
]


def _failed(project: Path, case: str) -> set[str]:
    return {result.check for result in evaluate(case, project).checks if not result.passed}


def _reference(tmp_path: Path, case: str) -> Path:
    return shutil.copytree(CASES / case / "reference", tmp_path / "project")


@pytest.mark.parametrize("case", _ALL_CASES)
def test_reference_passes_every_check(case: str, tmp_path: Path) -> None:
    verdict = evaluate(case, _reference(tmp_path, case))

    assert [result for result in verdict.checks if not result.passed] == []
    assert verdict.passed


@pytest.mark.parametrize("broken", _BROKEN, ids=lambda broken: f"{broken.case}-{broken.name}")
def test_broken_variant_fails_exactly_the_expected_checks(broken: Broken, tmp_path: Path) -> None:
    project = _reference(tmp_path, broken.case)
    for filename, edits in broken.edits.items():
        text = (project / filename).read_text(encoding="utf-8")
        for old, new in edits:
            assert old in text, f"edit target missing from {filename}: {old}"
            text = text.replace(old, new)
        (project / filename).write_text(text, encoding="utf-8")

    assert _failed(project, broken.case) == broken.fails
    assert not evaluate(broken.case, project).passed


def test_output_file_left_by_the_agents_own_run_does_not_count(tmp_path: Path) -> None:
    project = _reference(tmp_path, "e04")
    stale = project / "output" / "earlier-run"
    stale.mkdir(parents=True)
    (stale / "priced_orders.json").write_text(json.dumps([{}] * 6), encoding="utf-8")
    (project / _XML).write_text((project / _XML).read_text(encoding="utf-8").replace(' target="JSON"', ""))

    assert _failed(project, "e04") == {"output_rows:priced_orders"}


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


def test_every_case_has_broken_variants() -> None:
    assert {broken.case for broken in _BROKEN} == set(_ALL_CASES)


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


def _audit(transcript: Path, run: Path, venv: Path) -> list[FindingKind]:
    return [finding.kind for finding in audit(transcript, allow=[run, venv], forbid=[Path("/repo")])]


def test_clean_transcript_has_no_findings(tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"
    transcript = _transcript(
        tmp_path,
        _line(_call("Bash", command=f"cd {run} && {venv}/bin/datamimic authoring build . | head -c 500")),
        _line(_call("Write", file_path=f"{run}/datamimic.xml", content="<setup/>")),
        _line(_call("Read", file_path=f"{venv}/lib/python3.11/site-packages/datamimic_ce/__init__.py")),
        _line({"type": "text", "text": "I read AGENTS.md"}),
    )

    assert _audit(transcript, run, venv) == []


def test_skill_use_is_flagged(tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"

    assert _audit(_transcript(tmp_path, _line(_call("Skill", skill="generate-test-data"))), run, venv) == [
        FindingKind.SKILL
    ]


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


def test_repeatable_compares_the_second_run_in_order() -> None:
    check = Repeatable(kind="repeatable")
    rows = {"p": [{"a": 1}, {"a": 2}]}

    assert check.failure(Observed(None, None, rows, second_rows={"p": [{"a": 1}, {"a": 2}]})) is None
    assert check.failure(Observed(None, None, rows, second_rows={"p": [{"a": 2}, {"a": 1}]})) is not None
    assert check.failure(Observed(None, None, rows, second_error="Timeout")) is not None


def test_seed_is_reads_the_entry_descriptor_not_the_agents_acceptance_file(tmp_path: Path) -> None:
    project = _reference(tmp_path, "e01")
    (project / _ACCEPTANCE).write_text('{"version": "5.0", "expectations": [], "seed": 1}', encoding="utf-8")
    (project / _XML).write_text(
        (project / _XML).read_text(encoding="utf-8").replace('rngSeed="10421"', 'rngSeed="10421 "'), encoding="utf-8"
    )

    assert "seed_is" in _failed(project, "e01")
