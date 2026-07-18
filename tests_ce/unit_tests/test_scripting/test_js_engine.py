# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""PROTOTYPE spike, not wired into the DSL. The property that matters isn't "can we eval JS" -
it's whether a seeded engine's Math.random()/Date.now() are reproducible, since a JS engine
ships nondeterministic builtins by default inside a deterministic-first engine (AGENTS.md rule 6)."""

from random import Random

import pytest

pytest.importorskip("py_mini_racer")

from datamimic_ce.scripting.js_engine import JsEngine  # noqa: E402


def test_basic_eval():
    assert JsEngine().eval("1 + 1") == 2


def test_seeded_math_random_is_reproducible():
    seq1 = [JsEngine(rng=Random(42)).eval("Math.random()") for _ in range(5)]
    seq2 = [JsEngine(rng=Random(42)).eval("Math.random()") for _ in range(5)]
    assert seq1 == seq2


def test_seeded_math_random_sequence_within_one_engine_is_reproducible():
    """Not just the first draw - repeated calls on the SAME engine must also replay identically
    across two separately-constructed engines sharing a seed."""
    engine1 = JsEngine(rng=Random(7))
    engine2 = JsEngine(rng=Random(7))
    seq1 = [engine1.eval("Math.random()") for _ in range(10)]
    seq2 = [engine2.eval("Math.random()") for _ in range(10)]
    assert seq1 == seq2
    assert len(set(seq1)) > 1, "a real PRNG sequence, not a constant"


def test_different_seeds_diverge():
    a = JsEngine(rng=Random(1)).eval("Math.random()")
    b = JsEngine(rng=Random(2)).eval("Math.random()")
    assert a != b


def test_seeded_date_now_is_pinned():
    t1 = JsEngine(rng=Random(1)).eval("Date.now()")
    t2 = JsEngine(rng=Random(99)).eval("Date.now()")
    assert t1 == t2, "Date.now() must pin to the same DETERMINISTIC_ANCHOR regardless of seed value"


def test_unseeded_engine_is_not_forced_deterministic():
    """No rng passed -> native Math.random, left alone (AGENTS.md rule 6: no rngSeed means every
    run differs, by design)."""
    values = {JsEngine().eval("Math.random()") for _ in range(20)}
    assert len(values) > 1
