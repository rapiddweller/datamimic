# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""unique="true" on <key values>: a distinct value per row (no replacement).

Surface: engine (datamimic_ce). Scoped to finite 'values' (sampling without
replacement, like <reference unique>). Proves distinctness, seed reproducibility,
exhaustion error, and the conflicting-attribute guards.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str, gen: str = "people") -> list:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return [r["code"] for r in engine.capture_result()[gen]]


def test_values_are_distinct_and_seed_reproducible():
    codes = _run("unique_values.xml")
    assert len(codes) == 5
    assert len(set(codes)) == 5  # all distinct
    assert set(codes) == {"A", "B", "C", "D", "E"}
    assert _run("unique_values.xml") == codes  # seed-reproducible order


def test_duplicate_input_values_are_deduped():
    # values has duplicate 'A'/'C'; unique must still yield distinct output.
    codes = _run("unique_duplicate_values.xml")
    assert len(codes) == 3
    assert len(set(codes)) == 3  # distinct despite duplicate input
    assert set(codes) == {"A", "B", "C"}


def test_unique_supported_on_variable():
    codes = _run("unique_variable.xml")  # <variable values unique> feeding a <key script>
    assert len(set(codes)) == 3
    assert set(codes) == {"x", "y", "z"}


def test_exhaustion_raises():
    with pytest.raises(Exception, match="unique"):
        _run("unique_exhausted.xml", gen="x")


# --- edge cases: loose bool, None values, nullQuota ---


def test_loose_bool_yes_still_enforces_constraints():
    # unique="yes" coerces to True like pydantic does -> the weights conflict must still fire.
    with pytest.raises(Exception, match="unique|weights"):
        _run("unique_yes_with_weights.xml", gen="x")


def test_none_is_deduped_like_any_value():
    codes = _run("unique_none_value.xml")  # values None,'A',None,'B'
    assert len(codes) == 3
    assert set(codes) == {None, "A", "B"}  # the two Nones collapse to one


def test_unique_composes_with_null_quota():
    codes = _run("unique_null_quota.xml")
    non_null = [c for c in codes if c is not None]
    # nullQuota may null some rows; the non-null picks stay distinct and in the pool
    assert len(non_null) == len(set(non_null))
    assert set(non_null) <= {"A", "B", "C", "D", "E", "F"}


def test_unique_with_weights_raises():
    with pytest.raises(Exception, match="unique|weights"):
        _run("unique_with_weights.xml", gen="x")


def test_unique_without_values_raises():
    with pytest.raises(Exception, match="unique|values"):
        _run("unique_without_values.xml", gen="x")
