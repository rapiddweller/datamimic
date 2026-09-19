# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# See LICENSE file for the full text of the license.

"""<reference> distribution/cyclic: ordered rotation, cumulated bell selection —
the legacy reference modifiers, reusing the shared SourceDistribution dispatch."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class ReferenceMatrixCase:
    descriptor: str
    selection: str
    cyclic: bool
    unique: bool
    nested: bool = False
    valid: bool = True


REFERENCE_CASES = (
    ReferenceMatrixCase("ref_random.xml", "random", False, False),
    ReferenceMatrixCase("ref_ordered.xml", "ordered", False, False),
    ReferenceMatrixCase("ref_ordered_exhausted.xml", "ordered", False, False, valid=False),
    ReferenceMatrixCase("ref_cyclic.xml", "ordered", True, False),
    ReferenceMatrixCase("ref_cyclic_nested.xml", "ordered", True, False, nested=True),
    ReferenceMatrixCase("ref_cumulated.xml", "cumulated", False, False),
    ReferenceMatrixCase("ref_unique.xml", "random", False, True),
    ReferenceMatrixCase("ref_unique_cyclic_invalid.xml", "random", True, True, valid=False),
)


def _run(filename: str) -> list[dict]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()["events"]


def test_cyclic_reference_rotates_in_source_order():
    ids = [r["fk"] for r in _run("ref_cyclic.xml")]
    assert ids == [1, 2, 3, 4, 1, 2, 3, 4, 1, 2]  # stable fetch order, wrapped
    assert ids == [r["fk"] for r in _run("ref_cyclic.xml")]  # seeded-reproducible


def test_ordered_reference_within_pool():
    assert [r["fk"] for r in _run("ref_ordered.xml")] == [1, 2, 3]


def test_ordered_reference_exhausted_raises():
    with pytest.raises(Exception, match=r"ordered.*only has|only 4|cyclic"):
        _run("ref_ordered_exhausted.xml")


def test_cumulated_reference_bell_shaped_and_reproducible():
    ids = [r["fk"] for r in _run("ref_cumulated.xml")]
    assert len(ids) == 40
    assert set(ids) <= {1, 2, 3, 4}
    counts = Counter(ids)
    # Bell over indices 0..3 (mean 1.5): the middle rows must dominate the extremes combined-wise.
    assert counts[2] + counts[3] > counts[1] + counts[4]
    assert ids == [r["fk"] for r in _run("ref_cumulated.xml")]  # seeded-reproducible


def test_random_reference_is_seeded_and_uses_only_source_keys():
    ids = [row["fk"] for row in _run("ref_random.xml")]
    assert len(ids) == 12
    assert set(ids) <= {1, 2, 3, 4}
    assert ids == [row["fk"] for row in _run("ref_random.xml")]


def test_unique_reference_selects_every_source_key_once():
    ids = [row["fk"] for row in _run("ref_unique.xml")]
    assert sorted(ids) == [1, 2, 3, 4]
    assert ids == [row["fk"] for row in _run("ref_unique.xml")]


def test_unique_with_cyclic_is_a_parse_error():
    with pytest.raises(Exception, match=r"unique.*cyclic|cyclic.*unique"):
        _run("ref_unique_cyclic_invalid.xml")


def test_cyclic_reference_nested_in_condition_still_rotates():
    # Nested tasks get pagination=None: rotation must advance, not pin to row 0.
    ids = [r["fk"] for r in _run("ref_cyclic_nested.xml")]
    assert ids == [1, 2, 3, 4, 1, 2]


def test_reference_matrix_manifest_is_complete_and_uses_committed_descriptors():
    assert {(case.selection, case.cyclic, case.unique, case.nested, case.valid) for case in REFERENCE_CASES} == {
        ("random", False, False, False, True),
        ("ordered", False, False, False, True),
        ("ordered", False, False, False, False),
        ("ordered", True, False, False, True),
        ("ordered", True, False, True, True),
        ("cumulated", False, False, False, True),
        ("random", False, True, False, True),
        ("random", True, True, False, False),
    }
    assert all((_TEST_DIR / case.descriptor).is_file() for case in REFERENCE_CASES)
