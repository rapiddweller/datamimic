# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""The global namespace of DSL script expressions.

Under ``<setup rngSeed>`` no name reachable from a script expression may draw uncontrolled entropy:

- controlled (replays with the seed): ``random.*`` and ``random.Random()`` without a seed, ``uuid.uuid4()``,
  ``fake``, and the clock: ``datetime.datetime.now/utcnow/today``, ``datetime.date.today``,
  ``pd.Timestamp.now/utcnow/today`` return the deterministic anchor
- rejected (raise): ``random.SystemRandom``, ``np.random``, ``os.urandom``, ``os.getrandom``, ``uuid.uuid1``
- outside the contract (not entropy, not controlled): external input such as ``requests`` or
  ``os.environ``, ``"now"`` string literals (``np.datetime64("now")``, ``pd.to_datetime("now")``), and the
  iteration order of sets of strings across processes (``PYTHONHASHSEED``)

Mirrors DATAMIMIC EE's per-request evaluation proxies (EE ADR-031). Unseeded runs keep the raw modules.

``base64`` pairs a binary payload with its b64/hex form. ``__builtins__`` is an empty dict rather than
None: it still blocks every builtin, but an unresolvable name raises a NameError carrying the
identifier, which evaluate_python_expression turns into an error naming the missing name.
"""

from __future__ import annotations

import base64
import calendar
import collections
import datetime
import functools
import hashlib
import itertools
import json
import math
import os
import random
import re
import statistics
import uuid
from collections.abc import Callable
from random import Random
from types import ModuleType
from typing import NamedTuple

import numpy as np
import pandas as pd
import requests
from faker import Faker

from datamimic_ce.domains.api import resolve_clock, uuid4_from_random
from datamimic_ce.errors import IssueCode, task_config_error
from datamimic_ce.randomness import RandomSource

SAFE_GLOBALS: dict[str, object] = {
    "math": math,
    "random": random,
    "datetime": datetime,
    "uuid": uuid,
    "json": json,
    "os": os,
    "pd": pd,
    "np": np,
    "re": re,
    "calendar": calendar,
    "itertools": itertools,
    "functools": functools,
    "collections": collections,
    "statistics": statistics,
    "requests": requests,
    "fake": Faker(),
    "len": len,
    "range": range,
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "sum": sum,
    "abs": abs,
    "max": max,
    "min": min,
    "round": round,
    "sorted": sorted,
    "map": map,
    "filter": filter,
    "reduce": functools.reduce,
    "all": all,
    "any": any,
    "bin": bin,
    "hex": hex,
    "oct": oct,
    "type": type,
    "hashlib": hashlib,
    "base64": base64,
    "__builtins__": {},
}


class _EvalProxy:
    """Stands in for a module or class a DSL expression knows by name: ``overrides`` win, every
    other attribute and call goes to ``target``."""

    def __init__(self, target: ModuleType | type | RandomSource, overrides: dict[str, object]) -> None:
        self._target = target
        self._overrides = overrides

    def __getattr__(self, name: str) -> object:
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._target, name)

    def __call__(self, *args: object, **kwargs: object) -> object:
        if not callable(self._target):
            raise TypeError(f"'{type(self._target).__name__}' object is not callable")
        return self._target(*args, **kwargs)

    # A proxied class stays a class for type checks: isinstance(x, datetime.datetime) must not change under a seed.
    def __instancecheck__(self, instance: object) -> bool:
        return isinstance(self._target, type) and isinstance(instance, self._target)

    def __subclasscheck__(self, subclass: type) -> bool:
        return isinstance(self._target, type) and issubclass(subclass, self._target)

    # A copied proxy would fork or lose the run's stream; generator= keys deep-copy the script namespace.
    def __deepcopy__(self, memo: dict[int, object]) -> _EvalProxy:
        return self


class _Uncontrolled:
    """An entropy source a seeded run must not reach: using it in any way raises."""

    def __init__(self, name: str) -> None:
        self._name = name

    def _refuse(self) -> ValueError:
        return task_config_error(
            code=IssueCode.TASK_EXPRESSION_EVAL_FAILED,
            expr=self._name,
            error=(
                f"'{self._name}' draws entropy that <setup rngSeed> cannot replay; "
                "use random.* or a generator instead"
            ),
        )

    def __getattr__(self, attr: str) -> object:
        raise self._refuse()

    def __call__(self, *args: object, **kwargs: object) -> object:
        raise self._refuse()


class _OmittedRandomSeed:
    """Distinguishes Random() from Random(None), whose seed semantics differ."""


_OMITTED_RANDOM_SEED = _OmittedRandomSeed()
_RandomSeed = int | float | str | bytes | bytearray | None | _OmittedRandomSeed


def _random_seed(rng: RandomSource, x: _RandomSeed) -> int | float | str | bytes | bytearray | None:
    """A seeded run's Random() without a seed starts from the run's stream; an explicit seed is kept."""
    return rng.getrandbits(64) if isinstance(x, _OmittedRandomSeed) else x


class _SeededFaker:
    """``fake`` under a seed: every provider access reseeds the run's Faker from the rng, so a Faker
    value costs one rng draw and expressions without ``fake`` draw nothing."""

    def __init__(self, rng: RandomSource, faker_supplier: Callable[[], Faker]) -> None:
        self._rng = rng
        self._faker_supplier = faker_supplier

    def __getattr__(self, name: str) -> object:
        faker = self._faker_supplier()
        faker.seed_instance(self._rng.getrandbits(64))
        return getattr(faker, name)


# Values an expression may not return: they are namespace helpers, not data.
NON_VALUE_TYPES = frozenset({Faker, _EvalProxy, _Uncontrolled, _SeededFaker})


def _ignore_seed(*_args: object, **_kwargs: object) -> None:
    """random.seed() inside an expression would rewind the run's seeded stream, so it is a no-op."""


class _SeededObjects(NamedTuple):
    """The seeded stand-ins of one expression scope; built once, shared by expression globals and scripts."""

    random: _EvalProxy
    uuid: _EvalProxy
    uuid4: Callable[[], uuid.UUID]
    datetime: _EvalProxy
    anchored_datetime: _EvalProxy
    anchored_date: _EvalProxy
    pd: _EvalProxy
    np: _EvalProxy
    os: _EvalProxy
    fake: _SeededFaker


def _seeded_objects(rng: RandomSource, seeded_faker_supplier: Callable[[], Faker]) -> _SeededObjects:
    anchor = resolve_clock(deterministic=True)

    def now(tz: datetime.tzinfo | None = None) -> datetime.datetime:
        return anchor if tz is None else anchor.replace(tzinfo=datetime.UTC).astimezone(tz)

    def seeded_random(x: _RandomSeed = _OMITTED_RANDOM_SEED) -> Random:
        return Random(_random_seed(rng, x))

    def uuid4() -> uuid.UUID:
        return uuid.UUID(uuid4_from_random(rng))

    random_overrides = {
        "seed": _ignore_seed,
        "Random": seeded_random,
        "SystemRandom": _Uncontrolled("random.SystemRandom"),
    }
    anchored_datetime = _EvalProxy(datetime.datetime, {"now": now, "utcnow": lambda: anchor, "today": lambda: anchor})
    anchored_date = _EvalProxy(datetime.date, {"today": anchor.date})
    anchored_timestamp = _EvalProxy(
        pd.Timestamp,
        {
            "now": lambda tz=None: pd.Timestamp(now(tz)),
            "utcnow": lambda: pd.Timestamp(anchor, tz="UTC"),
            "today": lambda tz=None: pd.Timestamp(now(tz)),
        },
    )
    return _SeededObjects(
        random=_EvalProxy(rng, random_overrides),
        uuid=_EvalProxy(uuid, {"uuid4": uuid4, "uuid1": _Uncontrolled("uuid.uuid1")}),
        uuid4=uuid4,
        datetime=_EvalProxy(datetime, {"datetime": anchored_datetime, "date": anchored_date}),
        anchored_datetime=anchored_datetime,
        anchored_date=anchored_date,
        pd=_EvalProxy(pd, {"Timestamp": anchored_timestamp}),
        np=_EvalProxy(np, {"random": _Uncontrolled("np.random")}),
        os=_EvalProxy(os, {"urandom": _Uncontrolled("os.urandom"), "getrandom": _Uncontrolled("os.getrandom")}),
        fake=_SeededFaker(rng, seeded_faker_supplier),
    )


def expression_globals(
    is_seeded: bool,
    rng: RandomSource | None,
    seeded_faker_supplier: Callable[[], Faker],
) -> dict[str, object]:
    """Globals for one expression, using explicit dependencies for seeded behavior."""
    if not is_seeded:
        return SAFE_GLOBALS
    assert rng is not None
    seeded = _seeded_objects(rng, seeded_faker_supplier)
    return {
        **SAFE_GLOBALS,
        "random": seeded.random,
        "uuid": seeded.uuid,
        "datetime": seeded.datetime,
        "pd": seeded.pd,
        "np": seeded.np,
        "os": seeded.os,
        "fake": seeded.fake,
    }


def rebind_seeded_script_names(
    namespace: dict[str, object], rng: RandomSource, seeded_faker_supplier: Callable[[], Faker]
) -> frozenset[str]:
    """Give a seeded project script the seeded stand-ins instead of the raw modules, so its helpers replay (#357).

    Names bound to raw random/uuid/datetime/numpy/pandas/os (or random.Random, datetime.datetime, datetime.date,
    uuid.uuid4) are
    rebound by identity; helpers resolve globals at call time. The names expressions also know (random, uuid,
    datetime, pd, np, os) are set to the seeded stand-ins and returned: they stay private to the scripts, so
    expressions keep their own seeded globals. Other names, such as aliases, remain shared.
    Members imported by name (``from random import randint``) stay raw; deterministic replay detects them.
    """
    seeded = _seeded_objects(rng, seeded_faker_supplier)

    # Built here, not per expression: a class definition costs several times an expression evaluation.
    class SeededRandom(Random):
        """random.Random for project scripts, seeded like the expression override, and still a real Random
        subclass, so annotations, isinstance and subclassing keep working."""

        def __init__(self, x: _RandomSeed = _OMITTED_RANDOM_SEED) -> None:
            Random.__init__(self, _random_seed(rng, x))

    counterparts: tuple[tuple[object, object], ...] = (
        (random, seeded.random),
        (Random, SeededRandom),
        (uuid, seeded.uuid),
        (uuid.uuid4, seeded.uuid4),
        (datetime, seeded.datetime),
        (datetime.datetime, seeded.anchored_datetime),
        (datetime.date, seeded.anchored_date),
        (pd, seeded.pd),
        (np, seeded.np),
        (os, seeded.os),
    )
    for name, value in list(namespace.items()):
        for raw, stand_in in counterparts:
            if value is raw:
                namespace[name] = stand_in
    shared_with_expressions: tuple[tuple[str, object], ...] = (
        ("random", seeded.random),
        ("uuid", seeded.uuid),
        ("datetime", seeded.datetime),
        ("pd", seeded.pd),
        ("np", seeded.np),
        ("os", seeded.os),
    )
    private = set()
    for name, stand_in in shared_with_expressions:
        if name not in namespace or namespace[name] is stand_in:
            namespace[name] = stand_in
            private.add(name)
    return frozenset(private)
