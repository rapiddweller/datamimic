# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Inline weighted value pick: 'weights' as the companion of 'values'.

Surface: engine (datamimic_ce). Proves a <key values weights> picks from the values
with the given relative weights, is seed-reproducible, and fails loudly on a
length mismatch or weights-without-values.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str, gen: str = "people") -> list[str]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return [r["grade"] for r in engine.capture_result()[gen]]


def test_weighted_distribution_and_seed_reproducible():
    grades = _run("weighted_values.xml")
    assert set(grades) <= {"A", "B", "C"}
    dist = Counter(grades)
    total = len(grades)
    # weights 0.1/0.3/0.6 (relative) -> proportions within tolerance
    assert abs(dist["A"] / total - 0.1) < 0.05
    assert abs(dist["B"] / total - 0.3) < 0.05
    assert abs(dist["C"] / total - 0.6) < 0.05
    # same seed -> identical sequence
    assert _run("weighted_values.xml") == grades


def test_weights_compose_with_null_quota():
    # nullQuota is an outer gate (~25% None); the rest is the weighted pick.
    grades = _run("weighted_null_quota.xml")
    total = len(grades)
    nulls = grades.count(None)
    assert abs(nulls / total - 0.25) < 0.05
    non_null = [g for g in grades if g is not None]
    assert set(non_null) == {"A", "B", "C"}
    n = len(non_null)
    # within the non-null rows the 0.1/0.3/0.6 split still holds
    dist = Counter(non_null)
    assert abs(dist["A"] / n - 0.1) < 0.05
    assert abs(dist["C"] / n - 0.6) < 0.05
    assert _run("weighted_null_quota.xml") == grades  # seed-reproducible


def test_none_can_be_a_weighted_value():
    grades = _run("weighted_none_value.xml")
    total = len(grades)
    assert set(grades) == {"A", "B", None}
    # None is just the third choice with weight 0.2
    assert abs(grades.count(None) / total - 0.2) < 0.05
    assert abs(grades.count("A") / total - 0.5) < 0.05


def test_length_mismatch_raises():
    with pytest.raises(Exception, match="weights|values"):
        _run("weighted_values_mismatch.xml", gen="x")


def test_weights_without_values_raises():
    with pytest.raises(Exception, match="weights|values"):
        _run("weights_without_values.xml", gen="x")
