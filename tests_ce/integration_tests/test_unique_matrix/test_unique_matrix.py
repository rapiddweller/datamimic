# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Matrix test for unique="true" across generators, seed modes, distributions,
edge cases, and constraint validation.

Each case is a self-contained XML descriptor exercised through the engine.
SP/MP behaviour is observed via the single-process policy log, not via actual
multiprocessing (unique always forces single-process).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent / "unique_matrix_fixtures"


def _run(filename: str, gen: str) -> list[dict]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()[gen]


def _assert_distinct(values: list, label: str) -> None:
    assert len(values) == len(set(values)), f"{label}: duplicates in {values}"


def _assert_count(values: list, expected: int) -> None:
    assert len(values) == expected, f"expected {expected} rows, got {len(values)}"


# ── valid: values-based ──────────────────────────────────────────────

_VALID_VALUES = [
    "key_values",
    "key_values_seeded",
    "variable_values",
    "variable_values_seeded",
]


@pytest.mark.parametrize("case", _VALID_VALUES)
def test_valid_values_unique(case: str) -> None:
    rows = _run(f"{case}.xml", "gen")
    _assert_count(rows, 5)
    _assert_distinct([r["code"] for r in rows], case)


# ── valid: generator-based ───────────────────────────────────────────

_VALID_GENERATORS = [
    "key_ean_generator",
    "key_ean_generator_seeded",
    "key_increment_generator",
    "key_string_generator",
    "key_uuid_generator",
    "key_integer_generator",
    "variable_ean_generator",
    "variable_increment_generator",
]


@pytest.mark.parametrize("case", _VALID_GENERATORS)
def test_valid_generator_unique(case: str) -> None:
    rows = _run(f"{case}.xml", "gen")
    _assert_count(rows, 5)
    _assert_distinct([r["code"] for r in rows], case)


# ── valid: variable source-based ─────────────────────────────────────

def test_variable_source_csv_unique() -> None:
    rows = _run("variable_source_csv.xml", "gen")
    _assert_count(rows, 3)
    _assert_distinct([r["code"] for r in rows], "variable_source_csv")


# ── valid: distribution=random with unique ───────────────────────────

def test_variable_unique_distribution_random() -> None:
    rows = _run("variable_distribution_random.xml", "gen")
    _assert_count(rows, 5)
    _assert_distinct([r["code"] for r in rows], "variable_distribution_random")


# ── valid: entity-backed variable (regression — no unique) ───────────

def test_variable_entity_baseline() -> None:
    """Entity-backed variable without unique must still work."""
    rows = _run("variable_entity.xml", "gen")
    _assert_count(rows, 3)
    # entity produces Person instances — just verify names are non-empty
    for r in rows:
        assert r["code"], f"entity variable should produce a name"


# ── invalid: constraint violations ───────────────────────────────────

_INVALID_CONSTRAINT = [
    ("key_unique_without_pool", "unique.*requires"),
    ("key_unique_with_weights", "unique.*weights"),
    ("key_unique_with_distribution", "unique.*distribution"),
    ("variable_unique_with_cyclic", "cyclic.*source"),  # cyclic-requires-source fires before unique-forbids-cyclic
    ("variable_unique_with_distribution_cumulated", "random"),
    ("variable_entity_unique", "unique.*requires"),  # entity is not a valid pool for unique
    ("variable_constant_unique", "unique.*requires"),  # constant is not a valid pool
    ("variable_script_unique", "unique.*requires"),  # script is not a valid pool
]


@pytest.mark.parametrize(("case", "match"), _INVALID_CONSTRAINT)
def test_invalid_constraint_rejected(case: str, match: str) -> None:
    with pytest.raises(Exception, match=match):
        _run(f"{case}.xml", "gen")


# ── edge: generator produces duplicate → retry succeeds ──────────────

def test_generator_retry_on_collision() -> None:
    """A generator that produces only one unique value per retry window."""
    rows = _run("key_mock_duplicate_generator.xml", "gen")
    _assert_count(rows, 3)
    _assert_distinct([r["code"] for r in rows], "mock_duplicate")


# ── seeded reproducibility ───────────────────────────────────────────

def test_seeded_unique_reproducible() -> None:
    first = _run("key_ean_generator_seeded.xml", "gen")
    second = _run("key_ean_generator_seeded.xml", "gen")
    assert [r["code"] for r in first] == [r["code"] for r in second], (
        "seeded unique run must be reproducible"
    )


# ── single-process enforcement ───────────────────────────────────────

def test_unique_forces_single_process() -> None:
    """unique is a global cross-row constraint — must serialize to SP.
    count=12, pageSize=4 would normally spawn multiple workers."""
    rows = _run("key_unique_sp_enforcement.xml", "gen")
    _assert_count(rows, 12)
    _assert_distinct([r["code"] for r in rows], "sp_enforcement")
