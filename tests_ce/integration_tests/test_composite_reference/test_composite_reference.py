# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# See LICENSE file for the full text of the license.

"""Composite <reference>: <field> children map source columns to target fields, and
unique="true" draws distinct multi-column tuples (the EE concept/syntax ported to CE).
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str, gen: str = "events") -> list[dict]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()[gen]


def test_composite_reference_distinct_tuples_and_multiple_targets():
    rows = _run("composite_reference.xml")
    assert len(rows) == 6
    # each <field> target is set on the entity (mixed types: aisle TEXT, bin INT)
    tuples = [(r["aisle"], r["bin"]) for r in rows]
    assert all(isinstance(a, str) and isinstance(b, int) for a, b in tuples)
    # unique -> the 6 distinct (aisle, bin) combinations, no duplicate tuple (despite dup source rows)
    assert len(set(tuples)) == 6
    assert set(tuples) == {("A", 1), ("A", 2), ("B", 1), ("B", 2), ("C", 1), ("C", 2)}
    # seed-reproducible
    assert [(r["aisle"], r["bin"]) for r in _run("composite_reference.xml")] == tuples


def test_three_fields_three_types():
    rows = _run("composite_three_fields.xml", gen="rows")
    assert len(rows) == 4
    tuples = [(r["region"], r["yr"], r["price"]) for r in rows]
    # three component types: TEXT -> str, INTEGER -> int, REAL -> float
    assert all(isinstance(a, str) and isinstance(b, int) and isinstance(c, float) for a, b, c in tuples)
    assert len(set(tuples)) == 4  # the 4 distinct (region, year, price) combos


def test_composite_unique_exhaustion_raises():
    with pytest.raises(Exception, match="unique"):
        _run("composite_exhausted.xml", gen="x")


def test_composite_non_unique_allows_repeats():
    rows = _run("composite_nonunique.xml", gen="x")
    assert len(rows) == 20  # with replacement -> more rows than the 6 distinct combos
    valid = {("A", 1), ("A", 2), ("B", 1), ("B", 2), ("C", 1), ("C", 2)}
    assert {(r["aisle"], r["bin"]) for r in rows} <= valid


def test_legacy_single_field_reference_still_works():
    rows = _run("legacy_single.xml", gen="x")
    assert len(rows) == 3
    assert {r["aisle"] for r in rows} == {"A", "B", "C"}  # distinct aisles (deduped)


# --- Referential integrity against a SPARSE parent (the real-world composite-FK challenge) ---
# Web research framing: "referential integrity holds across the tuple, not on either column
# alone ... producers that generate columns independently break this without noticing."
# The full-grid fixtures above can't prove this (every cross is valid); a sparse parent can.

_VALID_PAIRS = {("EU", "E1"), ("EU", "E2"), ("US", "U1"), ("US", "U2"), ("US", "U3")}


def test_composite_fk_tuple_integrity_against_sparse_parent():
    # 30 children, fan-out (one-to-many) onto 5 sparse parent rows.
    rows = _run("fk_integrity.xml", gen="orders")
    pairs = {(r["region"], r["code"]) for r in rows}
    # Every (region, code) is a REAL parent row — never an invented cross like ('EU','U1').
    assert pairs <= _VALID_PAIRS
    # The columns are NOT generated independently: EU never carries a US code, and vice versa.
    assert not any(r["region"] == "EU" and r["code"].startswith("U") for r in rows)
    assert not any(r["region"] == "US" and r["code"].startswith("E") for r in rows)
    assert len(rows) == 30  # fan-out: far more children than the 5 distinct parents


def test_composite_fk_unique_assignment_no_double_booking():
    # unique="true" -> each parent tuple assigned at most once (1:1 slot assignment).
    rows = _run("fk_unique_assignment.xml", gen="assignments")
    pairs = [(r["region"], r["code"]) for r in rows]
    assert len(pairs) == len(set(pairs)) == 5  # no double-booking
    assert set(pairs) == _VALID_PAIRS  # the whole sparse parent, each exactly once


def test_composite_unique_holds_across_pages():
    # count(6) > pageSize(2): the full unique sequence is cached once, so distinctness holds
    # across pages (regression for the per-page-seed cross-page bug).
    rows = _run("composite_paged.xml")
    tuples = [(r["aisle"], r["bin"]) for r in rows]
    assert len(set(tuples)) == 6


def test_composite_unique_holds_under_multiprocessing():
    # CE policy: a composite unique <reference> is a global constraint -> forced single-process,
    # so it stays distinct even when numProcess > 1 (scaling these is an EE feature).
    rows = _run("composite_mp.xml")
    tuples = [(r["aisle"], r["bin"]) for r in rows]
    assert len(set(tuples)) == 6


def test_policy_logs_single_process_override():
    # The CE single-process policy informs the user (testable log) when it overrides a
    # multiprocess request (composite_mp.xml asks for numProcess=4). The DATAMIMIC logger has
    # its own handler (propagate=False), so capture by attaching directly to it.
    messages: list[str] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            messages.append(record.getMessage())

    handler = _Capture()
    dm_logger = logging.getLogger("DATAMIMIC")
    dm_logger.addHandler(handler)
    try:
        _run("composite_mp.xml")
    finally:
        dm_logger.removeHandler(handler)
    assert any("single-process" in m and "Enterprise" in m for m in messages)
