# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Distribution × source matrix for DATAMIMIC source reads.

Surface: engine (datamimic_ce). One DSL model per source kind, each running all three
SourceDistributions side by side (products ``ordered`` / ``random`` / ``cumulated``):

    source\\dist     ordered   random    cumulated
    CSV              ✓         ✓         ✓
    JSON             ✓         ✓         ✓
    SQLite (DB)      ✓         ✓         ✓
    memstore         ✓         ✓         ✓
    python-expr      ✓         ✓         ✓   (lazy/script branch)

Plus consumer coverage that <generate source> and <nestedKey source> honor the same
three distributions. Every source holds 27 distinct values (CSV/JSON/DB/expr = 0..26,
memstore = 1..27 via IncrementGenerator), so each distribution has a discriminating
invariant:

    ordered    -> output equals source order
    random     -> a seeded permutation of the source (every value once, not in order)
    cumulated  -> bell over the load order, mean = middle, with replacement

All under <setup rngSeed=42>, so random/cumulated replay identically.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent

# (model file, base offset of the 27 source values)
SOURCE_CASES = [
    ("variable_csv.xml", 0),
    # Same source/distributions but pageSize < count: the distribution invariants (permutation,
    # bell) must still hold ACROSS pages — a stable per-statement seed makes random/cumulated/unique
    # paginate consistently instead of re-shuffling / re-belling per page.
    ("variable_csv_paged.xml", 0),
    ("variable_json.xml", 0),
    ("variable_sqlite.xml", 0),
    ("variable_memstore.xml", 1),
    ("variable_lazy.xml", 0),
    ("generate_source.xml", 0),
    # <generate source> paged (pageSize < count): the worker-level selection must use a stable
    # per-statement seed too, else random/cumulated/unique repeat/miss values across pages.
    ("generate_source_paged.xml", 0),
]


def _run(filename: str) -> dict:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def _vals(result: dict, product: str) -> list[int]:
    return [int(row["v"]) for row in result[product]]


@pytest.mark.parametrize("filename,lo", SOURCE_CASES)
def test_distribution_invariants(filename: str, lo: int):
    res = _run(filename)
    src = list(range(lo, lo + 27))

    # ordered: source order, verbatim
    assert _vals(res, "ordered") == src

    # random: a permutation (every value exactly once), genuinely shuffled
    rnd = _vals(res, "random")
    assert sorted(rnd) == src
    assert rnd != src  # would fail if "random" were silently treated as "ordered"

    # cumulated: bell over the load order, with replacement
    cum = _vals(res, "cumulated")
    assert len(cum) == 6000
    assert all(lo <= v <= lo + 26 for v in cum)  # with replacement, never leaves source range
    counts = Counter(cum)
    centre = lo + 13
    assert counts[centre] > counts[lo] and counts[centre] > counts[lo + 26]  # middle favored
    assert abs(sum(cum) / len(cum) - centre) < 1.0  # mean = middle of the load order


@pytest.mark.parametrize("filename", [case[0] for case in SOURCE_CASES])
def test_replays_identically_under_seed(filename: str):
    a, b = _run(filename), _run(filename)
    for product in ("ordered", "random", "cumulated"):
        assert _vals(a, product) == _vals(b, product)


def _nested_vals(result: dict, product: str) -> list[int]:
    return [int(item["v"]) for row in result["outer"] for item in row[product]]


def test_nested_key_all_distributions():
    """<nestedKey source> honors all three distributions: runs, stays in range,
    deterministic. (Bell shape is proven on the <variable>/<generate> cells.)"""
    res = _run("nestedkey_source.xml")
    for product in ("ordered", "random", "cumulated"):
        vals = _nested_vals(res, product)
        assert len(vals) == 50 * 10
        assert all(1 <= v <= 27 for v in vals)  # memstore IncrementGenerator -> 1..27

    res2 = _run("nestedkey_source.xml")
    for product in ("ordered", "random", "cumulated"):
        assert _nested_vals(res, product) == _nested_vals(res2, product)
