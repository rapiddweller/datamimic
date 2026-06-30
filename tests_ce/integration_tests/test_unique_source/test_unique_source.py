# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# See LICENSE file for the full text of the license.

"""unique="true" on <variable source>: distinct rows without replacement, across
datasources. unique is a modifier on the random permutation (dedupe + strict
exhaustion); it stays datasource-agnostic (csv/json here; sqlite/memstore use the
same _distributed_iter path).
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


@pytest.mark.parametrize("src", ["csv", "json"])
def test_unique_distinct_from_source_and_seed_reproducible(src):
    codes = _run(f"unique_source_{src}.xml")
    assert len(codes) == 5
    assert len(set(codes)) == 5  # distinct rows, no replacement
    assert set(codes) == {"A", "B", "C", "D", "E"}
    assert _run(f"unique_source_{src}.xml") == codes  # seed-reproducible order


def test_duplicate_source_values_are_deduped():
    codes = _run("unique_source_duplicate.xml")  # source A,A,B,C,C
    assert len(codes) == 3
    assert set(codes) == {"A", "B", "C"}


def test_exhaustion_is_a_hard_error():
    # 8 requested, only 5 distinct -> strict error (not a silent 5).
    with pytest.raises(Exception, match="unique"):
        _run("unique_source_exhausted.xml", gen="x")


def test_unique_with_cyclic_rejected():
    with pytest.raises(Exception, match="unique|cyclic"):
        _run("unique_source_cyclic.xml", gen="x")


def test_empty_source_raises_not_silent_zero():
    # unlucky data: an empty source can't satisfy 3 unique rows -> strict error.
    with pytest.raises(Exception, match="unique"):
        _run("unique_source_empty.xml", gen="x")


# --- <generate source unique="true"> : distinct entities straight from the source ---


def test_generate_source_unique_distinct_and_reproducible():
    codes = _run("generate_unique_csv.xml")
    assert len(codes) == 5
    assert set(codes) == {"A", "B", "C", "D", "E"}  # distinct rows, no replacement
    assert _run("generate_unique_csv.xml") == codes  # seed-reproducible


def test_generate_source_unique_exhaustion_is_a_hard_error():
    with pytest.raises(Exception, match="unique"):
        _run("generate_unique_exhausted.xml")


def test_generate_source_unique_with_cyclic_rejected():
    with pytest.raises(Exception, match="unique|cyclic"):
        _run("generate_unique_cyclic.xml")


# --- multiprocessing: unique must hold across ray workers (with input duplicates) ---


def test_generate_source_unique_holds_across_workers():
    # 12 source rows (8 distinct), 4 workers -> each worker takes a disjoint window of the
    # same global deduped order, so the result is still 8 distinct (no cross-worker overlap).
    codes = _run("generate_unique_mp.xml")
    assert len(codes) == 8
    assert len(set(codes)) == 8


def test_key_unique_holds_across_workers():
    # dup values {a,a,b,c,c,d,e} -> 5 distinct; a unique <key> forces single-process.
    codes = _run("key_unique_mp.xml")
    assert len(codes) == 5
    assert set(codes) == {"a", "b", "c", "d", "e"}


def test_variable_source_unique_holds_across_pages():
    # count(5) > pageSize(2) -> 3 pages. The full unique pool is cached once, so distinctness
    # holds across pages (regression for the per-page-seed cross-page bug in sub-tasks).
    codes = _run("unique_source_paged.xml")
    assert len(codes) == 5
    assert set(codes) == {"A", "B", "C", "D", "E"}
