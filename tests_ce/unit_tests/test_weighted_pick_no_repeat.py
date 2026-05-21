"""Unit tests for pick_one_weighted_no_repeat helper.

TDD: these tests were written BEFORE the implementation exists.
They prove:
  (a) Never returns `last` when ≥2 distinct values exist.
  (b) Deterministic for a fixed random.Random seed.
  (c) Returns the sole value when only one distinct value in pool.
"""
from __future__ import annotations

import random

from datamimic_ce.domains.utils.dataset_loader import pick_one_weighted_no_repeat

VALUES_MULTI = ["A", "B", "C"]
WEIGHTS_MULTI = [1.0, 2.0, 3.0]
VALUES_SINGLE = ["X"]
WEIGHTS_SINGLE = [1.0]


# (a) Never returns last when ≥2 distinct values
def test_no_repeat_never_returns_last_over_many_seeds() -> None:
    """Over 200 different seeds the result must never equal last."""
    for seed in range(200):
        rng = random.Random(seed)
        for last in VALUES_MULTI:
            result = pick_one_weighted_no_repeat(rng, VALUES_MULTI, WEIGHTS_MULTI, last=last)
            assert result != last, (
                f"seed={seed}: got {result!r} == last={last!r}; helper must exclude last"
            )


# (b) Deterministic for a fixed seed
def test_no_repeat_deterministic_for_fixed_seed() -> None:
    """Two calls with the same seed and state must return identical results."""
    rng1 = random.Random(42)
    rng2 = random.Random(42)
    result1 = pick_one_weighted_no_repeat(rng1, VALUES_MULTI, WEIGHTS_MULTI, last="A")
    result2 = pick_one_weighted_no_repeat(rng2, VALUES_MULTI, WEIGHTS_MULTI, last="A")
    assert result1 == result2


# (c) Falls back to full pool when only one distinct value
def test_no_repeat_single_value_returns_it() -> None:
    """When only one distinct value, return it regardless of last."""
    rng = random.Random(0)
    result = pick_one_weighted_no_repeat(rng, VALUES_SINGLE, WEIGHTS_SINGLE, last="X")
    assert result == "X"


# Additional: last=None should work without filtering
def test_no_repeat_last_none_no_filter() -> None:
    """When last is None, all values are eligible."""
    rng = random.Random(7)
    # Should not raise; just picks from full pool
    result = pick_one_weighted_no_repeat(rng, VALUES_MULTI, WEIGHTS_MULTI, last=None)
    assert result in VALUES_MULTI


# Additional: when last not in values, should pick from full pool
def test_no_repeat_last_not_in_values() -> None:
    rng = random.Random(99)
    result = pick_one_weighted_no_repeat(rng, VALUES_MULTI, WEIGHTS_MULTI, last="Z")
    assert result in VALUES_MULTI
