# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Inline weighted value pick on <variable>: 'weights' as the companion of 'values'.

Surface: engine (datamimic_ce). Proves a <variable values weights> picks from the values
with the given relative weights, is seed-reproducible, and fails loudly on a
length mismatch or weights-without-values. Also tests the constraint that
unique=true cannot be combined with weights.
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
    grades = _run("weighted_values_variable.xml")
    assert set(grades) <= {"A", "B", "C"}
    dist = Counter(grades)
    total = len(grades)
    # weights 0.1/0.3/0.6 (relative) -> proportions within tolerance
    assert abs(dist["A"] / total - 0.1) < 0.05
    assert abs(dist["B"] / total - 0.3) < 0.05
    assert abs(dist["C"] / total - 0.6) < 0.05
    # same seed -> identical sequence
    assert _run("weighted_values_variable.xml") == grades


def test_none_can_be_a_weighted_value():
    grades = _run("weighted_none_value_variable.xml")
    total = len(grades)
    assert set(grades) == {"A", "B", None}
    # None is just the third choice with weight 0.2
    assert abs(grades.count(None) / total - 0.2) < 0.05
    assert abs(grades.count("A") / total - 0.5) < 0.05


def test_weighted_values_length_mismatch_raises():
    with pytest.raises(Exception, match="weights|values"):
        _run("weighted_values_mismatch_variable.xml", gen="x")


def test_weights_without_values_raises():
    with pytest.raises(Exception, match="weights|values"):
        _run("weights_without_values_variable.xml", gen="x")


def test_unique_and_weights_raises():
    with pytest.raises(Exception, match="unique.*cannot be combined with.*weights"):
        _run("unique_and_weights_variable.xml", gen="x")
