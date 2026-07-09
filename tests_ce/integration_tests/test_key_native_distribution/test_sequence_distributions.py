# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Legacy sequence parity for distribution= on numeric range keys. Expected orders follow the
documented legacy-DSL sequence semantics, not invented:
- step/increment: min, min+d, ... (d = granularity, int keys d=1); ENDS past max, never wraps
- shuffle (increment=2 grid steps): 1,3,5,2,4 over 1..5 - unique until exhausted
- wedge: min,max,min+d,max-d,... ending at the middle: 1,5,2,4,3 over 1..5
- bitreverse: bit-reversed counter: 0,4,2,6,1,5,3,7 over 0..7
- fibonacci/padovan: recurrence VALUES clipped to [min,max]; ends when the next value exceeds max
- randomWalk: starts at min, each row advances by a seeded random step in [1,2] (legacy-DSL
  default), saturating at max
"""

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_dir = Path(__file__).resolve().parent


def _run(filename: str):
    engine = DataMimicTest(_dir, filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_deterministic_sequences_match_legacy_order():
    result = _run("test_sequences.xml")
    five = result["five"]
    assert [r["step"] for r in five] == [1, 2, 3, 4, 5]
    assert [r["increment"] for r in five] == [1, 2, 3, 4, 5]
    assert [r["shuffle"] for r in five] == [1, 3, 5, 2, 4]
    assert [r["wedge"] for r in five] == [1, 5, 2, 4, 3]
    assert [r["v"] for r in result["bitrev"]] == [0, 4, 2, 6, 1, 5, 3, 7]


def test_recurrence_sequences_stay_in_range():
    result = _run("test_sequences.xml")
    assert [r["v"] for r in result["fib"]] == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
    assert [r["v"] for r in result["padovan"]] == [1, 1, 1, 2, 2, 3, 4, 5, 7, 9]


def test_random_walk_rises_by_bounded_steps_and_saturates():
    walk = [r["v"] for r in _run("test_sequences.xml")["walk"]]
    assert walk[0] == 1
    assert all(1 <= v <= 10 for v in walk)
    diffs = [b - a for a, b in zip(walk, walk[1:], strict=False)]
    # monotone, step 1..2 until the walk saturates at max (then 0)
    assert all(d in (0, 1, 2) for d in diffs), diffs
    assert walk[-1] == 10, "30 steps of >=1 must saturate a 1..10 walk"


def test_float_and_decimal_sequences_use_the_granularity_grid():
    result = _run("test_sequences.xml")
    five = result["float_five"]
    assert [r["step"] for r in five] == [0.5, 1.0, 1.5, 2.0, 2.5]
    assert [r["wedge"] for r in five] == [0.5, 2.5, 1.0, 2.0, 1.5]
    assert [float(r["dec"]) for r in five] == [0.01, 0.02, 0.03, 0.04, 0.05]


def test_sequences_replay_identically_under_a_seed():
    w1 = [r["v"] for r in _run("test_sequences.xml")["walk"]]
    w2 = [r["v"] for r in _run("test_sequences.xml")["walk"]]
    assert w1 == w2


def test_exhausted_sequence_caps_the_row_count():
    result = _run("test_sequence_exhaustion.xml")
    assert [r["v"] for r in result["rows"]] == [1, 2, 3]  # count=5 requested, 3 available


def test_positional_sequence_under_multiprocessing_is_rejected():
    """Worker chunks would restart the sequence and duplicate its values - fail loudly."""
    import pytest

    engine = DataMimicTest(_dir, "test_sequence_mp_rejected.xml", capture_test_result=True)
    with pytest.raises(ValueError, match="(?i)positional sequence.*multiprocessing"):
        engine.test_with_timer()
