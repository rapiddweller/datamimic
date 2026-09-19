# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""minCount/maxCount on <generate> (legacy-style random row count).

Surface: engine (datamimic_ce). Mirrors the existing <nestedKey> minCount/maxCount
behaviour; count resolution is the single shared StatementUtil.resolve_count.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str) -> dict:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_count_in_range_and_deterministic():
    first = _run("count_range.xml")["items"]
    assert 3 <= len(first) <= 7
    # seed-bound: same rngSeed -> same count
    second = _run("count_range.xml")["items"]
    assert len(first) == len(second)


def test_count_and_min_max_mutually_exclusive():
    with pytest.raises(Exception, match="minCount.*maxCount|maxCount.*minCount|count"):
        _run("count_conflict.xml")


def test_cascading_child_count_per_parent():
    # 3 parents, each with an independently-rolled child count in [2, 4].
    first = _run("count_range_cascade.xml")
    assert [r["oid"] for r in first["orders"]] == [1, 2, 3]
    total_lines = len(first["lines"])  # nested products captured flattened under their key
    assert 3 * 2 <= total_lines <= 3 * 4
    # seed-bound: identical across runs
    assert len(_run("count_range_cascade.xml")["lines"]) == total_lines


def test_min_max_with_source():
    first = _run("count_range_source.xml")["picked"]
    assert 3 <= len(first) <= 7
    source = {"a", "b", "c", "d", "e", "f", "g", "h", "i", "j"}
    assert all(row["v"] in source for row in first)
    # ordered + seed -> deterministic count and content
    second = _run("count_range_source.xml")["picked"]
    assert [r["v"] for r in first] == [r["v"] for r in second]
