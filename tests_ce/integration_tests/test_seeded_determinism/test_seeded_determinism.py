# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# See LICENSE file for the full text of the license.

"""Determinism under <setup rngSeed>: literal random generators and shuffled sources replay identically —
same run to run, AND regardless of the requested worker count (the single-process policy collapses seeded
worker-count-dependent generation so the output does not depend on the machine's core count)."""

from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str, gen: str = "g") -> list[dict]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()[gen]


def _col(filename: str, key: str) -> list:
    return [row[key] for row in _run(filename)]


def _run_twice(filename: str, keys: list[str]) -> tuple[list, list]:
    """The determinism primitive: run the SAME model TWICE (two independent engine runs) and return both
    projections. A seeded model must return equal results; an unseeded one must differ."""

    def project() -> list:
        return [tuple(r[k] for k in keys) for r in _run(filename)]

    return project(), project()


# Every seeded model, run TWICE and compared — the explicit "reproducible across two runs" check that
# answers 'where is each model executed twice?': here, one row per model, first-run == second-run.
@pytest.mark.parametrize(
    "filename,keys",
    [
        ("int_generator.xml", ["n"]),  # literal IntegerGenerator
        ("float_generator.xml", ["f"]),  # literal FloatGenerator
        ("two_generators.xml", ["n", "f"]),  # two literal generators, independent per-field rng
        ("source_random.xml", ["v"]),  # shuffled <generate source>
        ("entity_values.xml", ["v"]),  # entity field (<key values>)
        ("domain_generators.xml", ["given", "email", "phone"]),  # domain generators (names/email/phone)
        ("datetime_generator.xml", ["d"]),  # DateTimeGenerator (seed threaded through its special parsing)
    ],
)
def test_seeded_model_is_reproducible_across_two_runs(filename, keys):
    first, second = _run_twice(filename, keys)
    assert first == second


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


def test_seeded_entity_generation_core_count_independent():
    # <key values=...> (weighted choice) draws on the per-row rng — not a literal generator or a source,
    # yet must still be reproducible regardless of core count. numProcess=4 == numProcess=1.
    single = _col("entity_values.xml", "v")
    multi = _col("entity_values_mp.xml", "v")
    assert multi == single
    assert single == _col("entity_values.xml", "v")  # and stable run to run


def test_seeded_domain_generators_reproducible_and_core_count_independent():
    """The flagship case: realistic-entity generators — a leaf domain generator (GivenName) AND composite
    ones (Email, Phone, which thread their rng to child generators at construction) — must replay
    identically under a seed, run to run AND regardless of worker count. This is the test that the earlier
    literal-only determinism suite missed."""
    single = [(r["given"], r["email"], r["phone"]) for r in _run("domain_generators.xml")]
    assert single == [(r["given"], r["email"], r["phone"]) for r in _run("domain_generators.xml")]
    multi = [(r["given"], r["email"], r["phone"]) for r in _run("domain_generators_mp.xml")]
    assert multi == single


# --- the symmetric check: WITHOUT a seed, generation must be random (two runs differ) -----------------


@pytest.mark.parametrize(
    "filename,keys",
    [
        ("unseeded_integer.xml", ["n"]),  # literal random generator
        ("unseeded_domain.xml", ["given", "email"]),  # domain generators (names/emails)
        ("unseeded_entity.xml", ["v"]),  # entity field (<key values>)
        ("unseeded_source.xml", ["v"]),  # shuffled <generate source>
        ("unseeded_datetime.xml", ["d"]),  # DateTimeGenerator without a seed
    ],
)
def test_unseeded_generation_is_random(filename, keys):
    """Same _run_twice-and-compare primitive as the determinism tests, inverted: with NO <setup rngSeed>,
    two runs must DIFFER (10+ samples so a coincidental match is negligible). Guards against a seed
    leaking in and silently making 'random' output fixed."""
    first, second = _run_twice(filename, keys)
    assert first != second
