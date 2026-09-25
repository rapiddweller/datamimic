# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Negative determinism gate for script expressions: under <setup rngSeed> no reachable name may draw
uncontrolled entropy. Every known entropy source either replays with the seed or raises. Python rather
than DSL because each rejected source aborts a run; the positive replay is covered by the DSL model
tests_ce/integration_tests/test_determinism_seed_scenarios/script_globals_seeded.xml."""

from random import Random
from types import SimpleNamespace

import pytest
from faker import Faker

from datamimic_ce.engine.runtime.contexts.expression_globals import SAFE_GLOBALS, expression_globals

# Every name reviewed for entropy and external state (policy: expression_globals module docstring).
# A new SAFE_GLOBALS name fails this gate until it is classified there.
_REVIEWED_NAMES = {
    "math", "random", "datetime", "uuid", "json", "os", "pd", "np", "re", "calendar", "itertools",
    "functools", "collections", "statistics", "requests", "fake", "len", "range", "int", "float", "str",
    "bool", "list", "dict", "set", "tuple", "sum", "abs", "max", "min", "round", "sorted", "map", "filter",
    "reduce", "all", "any", "bin", "hex", "oct", "type", "hashlib", "base64", "__builtins__",
}  # fmt: skip

_CONTROLLED = [
    "random.randint(1, 10**9)",
    "random.Random().randint(1, 10**9)",
    "str(uuid.uuid4())",
    "fake.name()",
]
_ANCHORED_CLOCK = [
    "datetime.datetime.now()",
    "datetime.datetime.utcnow()",
    "datetime.datetime.today()",
    "datetime.date.today()",
    "pd.Timestamp.now()",
    "pd.Timestamp.today()",
]
_REJECTED = [
    "random.SystemRandom().randint(1, 9)",
    "np.random.randint(1, 9)",
    "np.random.default_rng()",
    "os.urandom(8)",
    "uuid.uuid1()",
]


def _context(seed: int | None) -> SimpleNamespace:
    root = SimpleNamespace(is_seeded=seed is not None, seeded_faker=Faker())
    return SimpleNamespace(root=root, rng=Random(seed))


def _evaluate(expr: str, context: SimpleNamespace):
    return eval(expr, expression_globals(context), {})  # noqa: S307 - the expression namespace under test


def test_every_global_is_reviewed() -> None:
    assert set(SAFE_GLOBALS) == _REVIEWED_NAMES


@pytest.mark.parametrize("expr", _CONTROLLED)
def test_controlled_sources_replay_with_the_seed(expr: str) -> None:
    assert _evaluate(expr, _context(1)) == _evaluate(expr, _context(1))
    assert _evaluate(expr, _context(1)) != _evaluate(expr, _context(2))


@pytest.mark.parametrize("expr", _ANCHORED_CLOCK)
def test_clock_reads_return_the_anchor(expr: str) -> None:
    assert str(_evaluate(expr, _context(1))).startswith("2025-01-01")


@pytest.mark.parametrize("expr", _REJECTED)
def test_uncontrolled_sources_are_rejected_when_seeded(expr: str) -> None:
    with pytest.raises(ValueError, match="rngSeed> cannot replay"):
        _evaluate(expr, _context(1))


@pytest.mark.parametrize("expr", _REJECTED)
def test_unseeded_runs_keep_the_raw_modules(expr: str) -> None:
    _evaluate(expr, _context(None))


def test_random_seed_in_an_expression_does_not_rewind_the_run() -> None:
    context = _context(1)
    first = _evaluate("random.seed(7) or random.randint(1, 10**9)", context)
    assert first != _evaluate("random.seed(7) or random.randint(1, 10**9)", context)


def test_runs_sharing_a_process_keep_their_own_faker() -> None:
    run_a, run_b = _context(1), _context(2)
    interleaved = []
    for _ in range(3):
        interleaved.append(_evaluate("fake.name()", run_a))
        _evaluate("fake.name()", run_b)
    alone = _context(1)
    assert interleaved == [_evaluate("fake.name()", alone) for _ in range(3)]
