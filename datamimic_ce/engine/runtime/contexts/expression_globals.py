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
from random import Random
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
import requests
from faker import Faker

from datamimic_ce.domains.domain_core.runtime.clock import resolve_clock
from datamimic_ce.domains.utils.rng_uuid import uuid4_from_random

if TYPE_CHECKING:
    from datamimic_ce.engine.runtime.contexts.context import Context

SAFE_GLOBALS: dict[str, Any] = {
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

    def __init__(self, target: Any, overrides: dict[str, Any]) -> None:
        self._target = target
        self._overrides = overrides

    def __getattr__(self, name: str) -> Any:
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._target, name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._target(*args, **kwargs)


class _Uncontrolled:
    """An entropy source a seeded run must not reach: using it in any way raises."""

    def __init__(self, name: str) -> None:
        self._name = name

    def _refuse(self) -> ValueError:
        return ValueError(
            f"'{self._name}' draws entropy that <setup rngSeed> cannot replay; use random.* or a generator instead"
        )

    def __getattr__(self, attr: str) -> Any:
        raise self._refuse()

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        raise self._refuse()


class _SeededFaker:
    """``fake`` under a seed: every provider access reseeds the run's Faker from the rng, so a Faker
    value costs one rng draw and expressions without ``fake`` draw nothing."""

    def __init__(self, context: Context) -> None:
        self._context = context

    def __getattr__(self, name: str) -> Any:
        faker = self._context.root.seeded_faker
        faker.seed_instance(self._context.rng.getrandbits(64))
        return getattr(faker, name)


# Values an expression may not return: they are namespace helpers, not data.
NON_VALUE_TYPES = frozenset({Faker, _EvalProxy, _Uncontrolled, _SeededFaker})


def _ignore_seed(*_args: Any, **_kwargs: Any) -> None:
    """random.seed() inside an expression would rewind the run's seeded stream, so it is a no-op."""


def expression_globals(context: Context) -> dict[str, Any]:
    """Globals for one expression evaluated in ``context``."""
    if not context.root.is_seeded:
        return SAFE_GLOBALS
    rng = context.rng
    anchor = resolve_clock(deterministic=True)

    def now(tz: datetime.tzinfo | None = None) -> datetime.datetime:
        return anchor if tz is None else anchor.replace(tzinfo=datetime.timezone.utc).astimezone(tz)

    def seeded_random(*args: Any, **kwargs: Any) -> Random:
        return Random(*args, **kwargs) if args or kwargs else Random(rng.getrandbits(64))

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
    return {
        **SAFE_GLOBALS,
        "random": _EvalProxy(rng, random_overrides),
        "uuid": _EvalProxy(uuid, {"uuid4": uuid4, "uuid1": _Uncontrolled("uuid.uuid1")}),
        "datetime": _EvalProxy(datetime, {"datetime": anchored_datetime, "date": anchored_date}),
        "pd": _EvalProxy(pd, {"Timestamp": anchored_timestamp}),
        "np": _EvalProxy(np, {"random": _Uncontrolled("np.random")}),
        "os": _EvalProxy(os, {"urandom": _Uncontrolled("os.urandom"), "getrandom": _Uncontrolled("os.getrandom")}),
        "fake": _SeededFaker(context),
    }
