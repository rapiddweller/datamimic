# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# For questions and support, contact: info@rapiddweller.com

"""<variable type=... source=mongodb> across the full distribution x cyclic x unique x
numProcess (SP/MP) matrix DATAMIMIC's own model validation allows. See
test_mongodb_variable_matrix.xml for the exact combinations and why each is valid."""

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


def _run() -> dict:
    test_dir = Path(__file__).resolve().parent
    engine = DataMimicTest(test_dir=test_dir, filename="test_mongodb_variable_matrix.xml", capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_random_distribution_reads_full_pool_single_process():
    """Regression: distribution="random" (loads_all=True) must sample from the WHOLE 20-row
    collection, not just the first pageSize=5 page - the exact bug reproduced and fixed in
    variable_task.py this session (previously silently truncated to 5 rows)."""
    result = _run()
    ids = [r["row_id"] for r in result["random_sp"]]
    assert len(ids) == 20
    assert sorted(ids) == list(range(1, 21)), f"expected the full 1..20 pool, got {sorted(ids)}"


def test_random_distribution_reads_full_pool_multi_process():
    """Same regression, under numProcess=2 - loads_all must hold per-worker too, not just SP."""
    result = _run()
    ids = [r["row_id"] for r in result["random_mp"]]
    assert len(ids) == 20
    assert sorted(ids) == list(range(1, 21)), f"expected the full 1..20 pool, got {sorted(ids)}"


def test_cumulated_distribution_reads_full_pool():
    """Same regression class for distribution="cumulated" (also loads_all=True). Unlike random,
    cumulated draws WITH replacement, bell-weighted toward the middle of the load order
    (SourceDistribution docstring) - the count/pool-membership/spread checks below are the
    correct invariants, not "no duplicates" (repeats are the whole point of a bell shape)."""
    result = _run()
    ids = [r["row_id"] for r in result["cumulated_sp"]]
    assert len(ids) == 20
    assert set(ids) <= set(range(1, 21)), f"every id must come from the seeded 1..20 pool: {set(ids)}"
    # bell-weighted with replacement over 20 draws from 20 keys: repeats are expected, and a full
    # 1..20 permutation (what the pre-fix truncation bug's "successful" 5-item case would NOT
    # produce anyway) would indicate this collapsed to uniform-without-replacement instead.
    assert len(set(ids)) < 20


def test_ordered_distribution_multi_process_uneven_pages():
    """distribution="ordered" (loads_all=False, the original pagination-fix target) under
    numProcess=2 with a page count (17) not evenly divisible by pageSize (5) - both the
    multiprocess split and the ragged last page must not duplicate or drop rows."""
    result = _run()
    ids = [r["row_id"] for r in result["ordered_mp"]]
    assert len(ids) == 17
    assert sorted(ids) == list(range(1, 18)), f"expected the full 1..17 pool, got {sorted(ids)}"


def test_cyclic_random_wraps_with_repeats():
    """cyclic=true + distribution=random: count (25) exceeds the pool (10), so wrapping is
    required - every value must be a real pool member, and repeats are expected/required."""
    result = _run()
    ids = [r["row_id"] for r in result["cyclic_random"]]
    assert len(ids) == 25
    assert set(ids) <= set(range(1, 11)), f"every id must come from the seeded 1..10 pool: {set(ids)}"
    assert len(set(ids)) < 25, "count > pool with cyclic=true must produce repeats"


def test_cyclic_ordered_wraps_in_stable_order():
    """cyclic=true + distribution=ordered, paginated (pageSize=4): count (11) exceeds the pool
    (7), so the stable order must wrap exactly: 1..7 then 1..4."""
    result = _run()
    ids = [r["row_id"] for r in result["cyclic_ordered"]]
    assert ids == [*range(1, 8), 1, 2, 3, 4], ids


def _run_selector() -> dict:
    test_dir = Path(__file__).resolve().parent
    engine = DataMimicTest(
        test_dir=test_dir, filename="test_mongodb_selector_distribution_matrix.xml", capture_test_result=True
    )
    engine.test_with_timer()
    return engine.capture_result()


def test_selector_random_is_a_permutation():
    """<variable selector=...> (not type=): default distribution="random" is a shuffle
    (permutation, no replacement) - same DataSourceRegistry.get_distributed_data dispatch as
    type=, exercised through the selector= entry point (client.get_by_page_with_query), which
    had zero matrix coverage before this."""
    result = _run_selector()
    ids = [r["row_id"] for r in result["selector_random"]]
    assert len(ids) == 15
    assert set(ids) == set(range(1, 16)), f"expected a permutation of 1..15, got {sorted(ids)}"


def test_selector_cyclic_random_wraps_with_repeats():
    result = _run_selector()
    ids = [r["row_id"] for r in result["selector_cyclic_random"]]
    assert len(ids) == 30
    assert set(ids) <= set(range(1, 16)), f"every id must come from the seeded 1..15 pool: {set(ids)}"
    assert len(set(ids)) < 30, "count > pool with cyclic=true must produce repeats"


def test_selector_cumulated_reads_full_pool():
    result = _run_selector()
    ids = [r["row_id"] for r in result["selector_cumulated"]]
    assert len(ids) == 15
    assert set(ids) <= set(range(1, 16)), f"every id must come from the seeded pool: {set(ids)}"
    assert len(set(ids)) < 15, "bell-weighted with-replacement draw should not collapse to a full permutation"


def test_selector_unique_draws_distinct_pool_exactly():
    result = _run_selector()
    ids = [r["row_id"] for r in result["selector_unique"]]
    assert len(ids) == 15
    assert set(ids) == set(range(1, 16)), f"expected all 15 pool values exactly once, got {sorted(ids)}"


def test_unique_random_draws_distinct_pool_exactly():
    """unique="true" + distribution="random" (the only distribution unique is allowed to combine
    with per ModelUtil.check_unique_constraints): count == pool size, every value distinct."""
    result = _run()
    ids = [r["row_id"] for r in result["unique_random"]]
    assert len(ids) == 15
    assert set(ids) == set(range(1, 16)), f"expected all 15 pool values exactly once, got {sorted(ids)}"
