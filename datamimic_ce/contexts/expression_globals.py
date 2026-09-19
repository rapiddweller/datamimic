# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""The global namespace of DSL script expressions.

Under ``<setup rngSeed>`` the stochastic and time-sensitive names (``random``, ``uuid.uuid4``,
``datetime.datetime.now/utcnow/today``, ``datetime.date.today``, ``fake``) draw from the evaluating
context's seeded rng and the deterministic clock anchor, so script expressions replay like generators.
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
from typing import Any

import numpy as np
import pandas as pd
import requests
from faker import Faker

from datamimic_ce.domains.domain_core.runtime.clock import resolve_clock
from datamimic_ce.domains.utils.rng_uuid import uuid4_from_random

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

# A separate instance, so seeding it never leaks into the unseeded SAFE_GLOBALS["fake"].
_SEEDED_FAKER = Faker()


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


class _SeededFaker:
    """``fake`` under a seed: every provider access reseeds the dedicated Faker from the rng, so a
    Faker value costs one rng draw and expressions without ``fake`` draw nothing."""

    def __init__(self, rng: Random) -> None:
        self._rng = rng

    def __getattr__(self, name: str) -> Any:
        _SEEDED_FAKER.seed_instance(self._rng.getrandbits(64))
        return getattr(_SEEDED_FAKER, name)


# Values an expression may not return: they are namespace helpers, not data.
NON_VALUE_TYPES = frozenset({Faker, _EvalProxy, _SeededFaker})


def _ignore_seed(*_args: Any, **_kwargs: Any) -> None:
    """random.seed() inside an expression would rewind the run's seeded stream, so it is a no-op."""


def expression_globals(rng: Random | Any, seeded: bool) -> dict[str, Any]:
    """Globals for one expression evaluation; ``rng`` is the evaluating context's rng."""
    if not seeded:
        return SAFE_GLOBALS
    anchor = resolve_clock(deterministic=True)

    def now(tz: datetime.tzinfo | None = None) -> datetime.datetime:
        return anchor if tz is None else anchor.replace(tzinfo=datetime.timezone.utc).astimezone(tz)

    def uuid4() -> uuid.UUID:
        return uuid.UUID(uuid4_from_random(rng))

    anchored_datetime = _EvalProxy(datetime.datetime, {"now": now, "utcnow": lambda: anchor, "today": lambda: anchor})
    anchored_date = _EvalProxy(datetime.date, {"today": anchor.date})
    return {
        **SAFE_GLOBALS,
        "random": _EvalProxy(rng, {"seed": _ignore_seed, "Random": Random, "SystemRandom": random.SystemRandom}),
        "uuid": _EvalProxy(uuid, {"uuid4": uuid4}),
        "datetime": _EvalProxy(datetime, {"datetime": anchored_datetime, "date": anchored_date}),
        "fake": _SeededFaker(rng),
    }
