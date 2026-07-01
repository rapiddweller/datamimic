# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# See LICENSE file for the full text of the license.

"""Determinism under <setup rngSeed>: literal random generators and shuffled sources replay identically —
same run to run, AND regardless of the requested worker count (the single-process policy collapses seeded
worker-count-dependent generation so the output does not depend on the machine's core count)."""

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str, gen: str = "g") -> list[dict]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()[gen]


def _col(filename: str, key: str) -> list:
    return [row[key] for row in _run(filename)]


# --- literal random generators are seed-reproducible -------------------------------------------------


def test_seeded_integer_generator_reproducible():
    a = _col("int_generator.xml", "n")
    assert a == _col("int_generator.xml", "n")  # same seed -> same numbers
    assert len(a) == 8
    assert all(isinstance(n, int) and 1000 <= n <= 9999 for n in a)


def test_seeded_float_generator_reproducible():
    a = _col("float_generator.xml", "f")
    assert a == _col("float_generator.xml", "f")
    assert all(isinstance(f, float) and 0.0 <= f <= 1000.0 for f in a)


def test_two_seeded_generators_reproducible_and_independent():
    # two generators in one entity each draw from their own per-field seeded rng
    a = _run("two_generators.xml")
    b = _run("two_generators.xml")
    assert [(r["n"], r["f"]) for r in a] == [(r["n"], r["f"]) for r in b]
    ints = [r["n"] for r in a]
    floats = [r["f"] for r in a]
    assert all(1000 <= n <= 9999 for n in ints) and all(0.0 <= f <= 1.0 for f in floats)


# --- determinism is independent of the requested worker count (single-process policy) ----------------


def test_seeded_integer_generator_core_count_independent():
    # numProcess=4 is collapsed to single-process by the policy, so it MUST equal the numProcess=1 run.
    # (Without the policy, each worker restarts the seeded generator and emits duplicated chunks.)
    single = _col("int_generator.xml", "n")
    multi = _col("int_generator_mp.xml", "n")
    assert multi == single


def test_seeded_source_random_reproducible_and_permutation():
    a = _col("source_random.xml", "v")
    assert a == _col("source_random.xml", "v")
    assert len(a) == 12 and len(set(a)) == 12  # no-replacement permutation of the 12 source rows


def test_seeded_source_random_core_count_independent():
    single = _col("source_random.xml", "v")
    multi = _col("source_random_mp.xml", "v")
    assert multi == single
