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


def _globals(context: SimpleNamespace):
    is_seeded = context.root.is_seeded
    return expression_globals(
        is_seeded,
        context.rng if is_seeded else None,
        lambda: context.root.seeded_faker,
    )


def _evaluate(expr: str, context: SimpleNamespace):
    return eval(expr, _globals(context), {})  # noqa: S307 - the expression namespace under test


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


class _TrackedRng:
    def __init__(self, events: list[str]) -> None:
        self.bits: list[int] = []
        self._events = events

    def getrandbits(self, bits: int) -> int:
        self.bits.append(bits)
        self._events.append("bits")
        return 17


class _TrackedRoot:
    def __init__(self, owner: "_TrackedSeededContext", seeded: bool) -> None:
        self._owner = owner
        self.is_seeded = seeded

    @property
    def seeded_faker(self) -> Faker:
        self._owner._faker_reads += 1
        self._owner.events.append("faker")
        return Faker()


class _TrackedSeededContext:
    def __init__(self, seeded: bool) -> None:
        self.rng_reads = 0
        self.events: list[str] = []
        self._rng = _TrackedRng(self.events)
        self._faker_reads = 0
        self.root = _TrackedRoot(self, seeded)

    @property
    def rng(self) -> _TrackedRng:
        self.rng_reads += 1
        return self._rng


def test_unseeded_expression_globals_are_the_raw_mapping_without_rng_access() -> None:
    context = _TrackedSeededContext(seeded=False)

    assert _globals(context) is SAFE_GLOBALS
    assert context.rng_reads == 0
    assert context._faker_reads == 0


def test_seeded_expression_globals_bind_rng_for_constant_expressions() -> None:
    context = _TrackedSeededContext(seeded=True)

    assert eval("1", _globals(context), {}) == 1  # noqa: S307 - globals under test
    assert context.rng_reads == 1
    assert context._rng.bits == []
    assert context._faker_reads == 0


def test_seeded_fake_provider_draws_one_64_bit_seed_lazily() -> None:
    context = _TrackedSeededContext(seeded=True)
    globals_ = _globals(context)

    fake = globals_["fake"]
    assert context._rng.bits == []
    assert context._faker_reads == 0

    assert callable(fake.name)
    assert context._rng.bits == [64]
    assert context._faker_reads == 1
    assert context.events == ["faker", "bits"]


def test_seeded_random_omitted_seed_draws_lazily_but_none_does_not() -> None:
    context = _TrackedSeededContext(seeded=True)
    random_proxy = _globals(context)["random"]

    random_proxy.Random()
    assert context._rng.bits == [64]

    random_proxy.Random(None)
    assert context._rng.bits == [64]
