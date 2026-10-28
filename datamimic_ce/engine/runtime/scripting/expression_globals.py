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
A ``where=`` condition refuses every controlled and rejected name above, seeded or not (``row_expression_globals``).

``base64`` pairs a binary payload with its b64/hex form. ``__builtins__`` is an empty dict rather than
None: it still blocks every builtin, but an unresolvable name raises a NameError carrying the
identifier, which evaluate_python_expression turns into an error naming the missing name.
"""

from __future__ import annotations

import ast
import base64
import builtins
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
import sys
import uuid
from collections.abc import Callable, Container, Iterable, MutableSequence, Sequence
from dataclasses import dataclass
from enum import StrEnum
from random import Random
from types import ModuleType
from typing import NamedTuple, NoReturn, TypeVar

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
# The Python builtins a script can use; a script that calls another one fails with I956.
SCRIPT_BUILTINS = tuple(sorted(SAFE_GLOBALS.keys() & set(dir(builtins))))
UNOFFERED_BUILTINS = frozenset(dir(builtins)) - SAFE_GLOBALS.keys()


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
    """An entropy source (or, in where=, a clock) an expression must not reach: using it in any way raises."""

    def __init__(self, name: str, error: str | None = None) -> None:
        self._name = name
        self._error = (
            f"'{name}' draws entropy that <setup rngSeed> cannot replay; use random.* or a generator instead"
            if error is None
            else error
        )

    def _refuse(self) -> ValueError:
        return task_config_error(code=IssueCode.TASK_EXPRESSION_EVAL_FAILED, expr=self._name, error=self._error)

    def __getattr__(self, attr: str) -> object:
        raise self._refuse()

    def __call__(self, *args: object, **kwargs: object) -> object:
        raise self._refuse()


_RandomSeed = int | float | str | bytes | bytearray | None


def _random_seed(rng: RandomSource, x: _RandomSeed) -> _RandomSeed:
    """Random() and Random(None) would seed from OS entropy; in a seeded run they start from the run's stream."""
    return rng.getrandbits(64) if x is None else x


def _seeded_random(rng: RandomSource, x: _RandomSeed = None) -> Random:
    return Random(_random_seed(rng, x))


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


def _refuse_keyed_seed(a: _RandomSeed = None, version: int = 2) -> None:
    """random.seed() in a seeded script: without a value it would draw OS entropy, so it is a no-op. With a value,
    later draws come from the run's stream, not from that key, so it is refused rather than silently ignored."""
    if a is None:
        return
    raise task_config_error(
        code=IssueCode.TASK_EXPRESSION_EVAL_FAILED,
        expr="random.seed",
        error="random.seed(x) in a script cannot reseed a <setup rngSeed> run; use random.Random(x) for a keyed stream",
    )


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


def _seeded_objects(
    rng: RandomSource,
    seeded_faker_supplier: Callable[[], Faker],
    random_constructor: Callable[..., Random],
    seed: Callable[..., None],
) -> _SeededObjects:
    anchor = resolve_clock(deterministic=True)

    def now(tz: datetime.tzinfo | None = None) -> datetime.datetime:
        return anchor if tz is None else anchor.replace(tzinfo=datetime.UTC).astimezone(tz)

    def uuid4() -> uuid.UUID:
        return uuid.UUID(uuid4_from_random(rng))

    random_overrides = {
        "seed": seed,
        "Random": random_constructor,
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
    seeded = _seeded_objects(rng, seeded_faker_supplier, functools.partial(_seeded_random, rng), _ignore_seed)
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


_T = TypeVar("_T")
ROW_DRAW_REFUSED = "where reads one row and must not read the clock or draw random values"


class _RefusedDraws:
    """The random source of a row condition: every draw raises, so the length pass and every worker keep the same
    rows. Keyed streams (random.Random(5)) stay deterministic and allowed."""

    def _refuse(self) -> NoReturn:
        raise task_config_error(code=IssueCode.TASK_EXPRESSION_EVAL_FAILED, expr="where", error=ROW_DRAW_REFUSED)

    def randint(self, a: int, b: int) -> int:
        self._refuse()

    def random(self) -> float:
        self._refuse()

    def uniform(self, a: float, b: float) -> float:
        self._refuse()

    def randbytes(self, n: int) -> bytes:
        self._refuse()

    def getrandbits(self, k: int) -> int:
        self._refuse()

    def choice(self, seq: Sequence[_T]) -> _T:
        self._refuse()

    def choices(
        self,
        population: Sequence[_T],
        weights: Sequence[float] | None = None,
        *,
        cum_weights: Sequence[float] | None = None,
        k: int = 1,
    ) -> list[_T]:
        self._refuse()

    def shuffle(self, x: MutableSequence[_T]) -> None:
        self._refuse()


def row_expression_globals() -> dict[str, object]:
    """Globals for a where= condition, in a seeded and an unseeded run alike: every random draw, entropy source and
    clock read raises with the row rule. A seeded anchor and an unseeded wall clock would keep other rows than the
    keys of the same run see."""
    refused = _RefusedDraws()
    no = _Uncontrolled("where", ROW_DRAW_REFUSED)
    return {
        **SAFE_GLOBALS,
        "random": _EvalProxy(
            refused, {"seed": _ignore_seed, "Random": functools.partial(_seeded_random, refused), "SystemRandom": no}
        ),
        "uuid": _EvalProxy(uuid, {"uuid1": no, "uuid4": no}),
        "datetime": _EvalProxy(
            datetime,
            {
                "datetime": _EvalProxy(datetime.datetime, {"now": no, "utcnow": no, "today": no}),
                "date": _EvalProxy(datetime.date, {"today": no}),
            },
        ),
        "pd": _EvalProxy(pd, {"Timestamp": _EvalProxy(pd.Timestamp, {"now": no, "utcnow": no, "today": no})}),
        "np": _EvalProxy(np, {"random": no}),
        "os": _EvalProxy(os, {"urandom": no, "getrandom": no}),
        "fake": no,
    }


def rebind_seeded_script_names(
    namespace: dict[str, object], rng: RandomSource, seeded_faker_supplier: Callable[[], Faker]
) -> frozenset[str]:
    """Give a seeded project script the seeded stand-ins instead of the raw modules, so its helpers replay (#357).

    Script-level names bound to the raw modules or to members imported by name (``from random import randint``,
    ``from datetime import datetime``) are rebound by identity; helpers resolve globals at call time. The names
    expressions also know (random, uuid, datetime, pd, np, os) are set to the seeded stand-ins and returned: they
    stay private to the scripts, so expressions keep their own seeded globals. Other names, such as aliases, remain
    shared.

    ``random.seed(x)`` with a value is refused: a keyed stream is ``random.Random(x)``.

    Outside this rebinding, and therefore not replayed: draws made while the script body itself executes
    (module-level values, default arguments), imports inside helper bodies, and members of uuid, datetime and os
    that are not listed below.
    A plain run does not detect them. Build refuses imports inside bodies and replays every seeded model that loads
    Python, which catches the rest when they change the captured rows (#332).
    """

    # Built here, not per expression: a class definition costs several times an expression evaluation.
    class SeededRandom(Random):
        """random.Random for project scripts, seeded like the expression override, and still a real Random
        subclass, so annotations, isinstance and subclassing keep working."""

        def __init__(self, x: _RandomSeed = None) -> None:
            Random.__init__(self, _random_seed(rng, x))

    # Scripts reach Random both directly and as random.Random; both must stay the class.
    seeded = _seeded_objects(rng, seeded_faker_supplier, SeededRandom, _refuse_keyed_seed)
    counterparts: tuple[tuple[object, object], ...] = (
        (random, seeded.random),
        (uuid, seeded.uuid),
        (uuid.uuid4, seeded.uuid4),
        (datetime, seeded.datetime),
        (datetime.datetime, seeded.anchored_datetime),
        (datetime.date, seeded.anchored_date),
        (pd, seeded.pd),
        (np, seeded.np),
        (os, seeded.os),
        # Members imported by name are the module's own objects, so identity finds them too. One pair for each name
        # in random.__all__ (#391); test_every_public_random_member_imported_by_name_is_rebound fails when a Python
        # version adds one. The stand-in is what an expression gets for random.<name>, with the Random, seed and
        # SystemRandom overrides.
        (random.Random, seeded.random.Random),
        (random.SystemRandom, seeded.random.SystemRandom),
        (random.betavariate, seeded.random.betavariate),
        (random.choice, seeded.random.choice),
        (random.choices, seeded.random.choices),
        (random.expovariate, seeded.random.expovariate),
        (random.gammavariate, seeded.random.gammavariate),
        (random.gauss, seeded.random.gauss),
        (random.getrandbits, seeded.random.getrandbits),
        (random.getstate, seeded.random.getstate),
        (random.lognormvariate, seeded.random.lognormvariate),
        (random.normalvariate, seeded.random.normalvariate),
        (random.paretovariate, seeded.random.paretovariate),
        (random.randbytes, seeded.random.randbytes),
        (random.randint, seeded.random.randint),
        (random.random, seeded.random.random),
        (random.randrange, seeded.random.randrange),
        (random.sample, seeded.random.sample),
        (random.seed, seeded.random.seed),
        (random.setstate, seeded.random.setstate),
        (random.shuffle, seeded.random.shuffle),
        (random.triangular, seeded.random.triangular),
        (random.uniform, seeded.random.uniform),
        (random.vonmisesvariate, seeded.random.vonmisesvariate),
        (random.weibullvariate, seeded.random.weibullvariate),
        (uuid.uuid1, seeded.uuid.uuid1),
        (os.urandom, seeded.os.urandom),
    )
    if sys.version_info >= (3, 12):
        counterparts += ((random.binomialvariate, seeded.random.binomialvariate),)
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


# Entropy a seeded <execute> script draws while it loads (#359). A script's names are rebound to the seeded
# stand-ins after its body has run, so a module-level call, a default argument or an import inside a function body
# is not seeded. The scan is static, recognises only unambiguous constructs and never reports source text.
class LoadTimeDraw(StrEnum):
    MODULE_LEVEL_CALL = "draws entropy while the script loads (module level or default argument)"
    IMPORT_IN_BODY = "imports an entropy module inside a function or class body and draws from it"


@dataclass(frozen=True)
class LoadTimeFinding:
    draw: LoadTimeDraw
    line: int


# Only the draws the run's seeded names stand in for, so that moving the draw into a function is a true remedy.
# module -> the attributes that draw; None means any attribute of the module does.
_DRAWING_ATTRIBUTES: dict[str, frozenset[str] | None] = {
    "random": None,
    "uuid": frozenset({"uuid1", "uuid4"}),
    "datetime": frozenset({"now", "utcnow", "today"}),
    "os": frozenset({"urandom"}),
}
# Given a seed value (not None) these build or seed a deterministic generator instead of drawing.
_SEEDED_WHEN_GIVEN_A_SEED = frozenset({"Random", "seed"})


def load_time_entropy(source: str) -> tuple[LoadTimeFinding, ...]:
    """Findings in source order. Unparseable source has none: the runtime reports its syntax error itself."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ()
    modules, members = _bindings(_module_scope_nodes(tree), _DRAWING_ATTRIBUTES)
    findings: list[LoadTimeFinding] = []
    for call in _load_time_calls(tree):
        if _draws(call, modules, members):
            findings.append(LoadTimeFinding(LoadTimeDraw.MODULE_LEVEL_CALL, call.lineno))
    for body in ast.walk(tree):
        if isinstance(body, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            local_modules, local_members = _bindings(ast.walk(body), _DRAWING_ATTRIBUTES)
            if any(
                isinstance(call, ast.Call) and _draws(call, local_modules, local_members) for call in ast.walk(body)
            ):
                for inner in ast.walk(body):
                    if isinstance(inner, ast.Import | ast.ImportFrom) and _imports_entropy(inner):
                        findings.append(LoadTimeFinding(LoadTimeDraw.IMPORT_IN_BODY, inner.lineno))
    return tuple(sorted(set(findings), key=lambda finding: (finding.line, finding.draw.value)))


def _root_module(name: str) -> str:
    return name.partition(".")[0]


def _imports_entropy(node: ast.Import | ast.ImportFrom) -> bool:
    if isinstance(node, ast.Import):
        return any(_root_module(alias.name) in _DRAWING_ATTRIBUTES for alias in node.names)
    return node.level == 0 and _root_module(node.module or "") in _DRAWING_ATTRIBUTES


def _module_scope_nodes(tree: ast.Module) -> list[ast.AST]:
    """The nodes of the module's own namespace: everything except function and lambda bodies, which have theirs."""
    nodes: list[ast.AST] = []
    pending: list[ast.AST] = list(tree.body)
    while pending:
        node = pending.pop()
        nodes.append(node)
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
            pending.extend(ast.iter_child_nodes(node))
    return nodes


def _bindings(nodes: Iterable[ast.AST], roots: Container[str]) -> tuple[dict[str, str], dict[str, tuple[str, str]]]:
    """Names bound to one of the ``roots`` modules (``import random as r``) and to one of its members
    (``from random import randint``, ``from datetime import datetime``) by the imports among ``nodes``."""
    modules: dict[str, str] = {}
    members: dict[str, tuple[str, str]] = {}
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = _root_module(alias.name)
                if root in roots:
                    modules[alias.asname or root] = root
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None and node.module in roots:
            for alias in node.names:
                members[alias.asname or alias.name] = (node.module, alias.name)
    return modules, members


# These only wrap a generator: it runs later, when something consumes it.
_LAZY_WRAPPERS = frozenset({"iter", "map", "zip", "filter", "enumerate", "reversed"})
# The stdlib does not mark which itertools are lazy, so this is a list; a name outside it stays reported. product,
# permutations and combinations consume their input at once.
LAZY_ITERTOOLS = frozenset(
    {
        "accumulate",
        "chain",
        "compress",
        "cycle",
        "dropwhile",
        "filterfalse",
        "groupby",
        "islice",
        "pairwise",
        "starmap",
        "takewhile",
        "tee",
        "zip_longest",
    }
)


def _callee_name(func: ast.expr) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    return func.attr if isinstance(func, ast.Attribute) else None


# A match star or mapping-rest capture binds a list or a dict, which no call consumes a generator through.
_Binder = (
    ast.Name
    | ast.ExceptHandler
    | ast.FunctionDef
    | ast.AsyncFunctionDef
    | ast.ClassDef
    | ast.Import
    | ast.ImportFrom
    | ast.MatchAs
)


def _bound_names(node: _Binder) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.asname or _root_module(alias.name) for alias in node.names]
    if isinstance(node, ast.ImportFrom):
        return [alias.asname or alias.name for alias in node.names]
    if isinstance(node, ast.Name):
        return [] if isinstance(node.ctx, ast.Load) else [node.id]
    return [node.name] if node.name else []


def _itertools_bindings(scope: list[ast.AST]) -> tuple[dict[str, str], dict[str, tuple[str, str]]]:
    """The itertools imports still bound once the module has loaded. The last binding of a name in source order
    wins: an assignment, del, def, class, loop or with target, except or match capture name, or another import
    after the import drops it, and the name stays reported (fail safe). One decision covers the whole file."""
    binders = sorted(
        (node for node in scope if isinstance(node, _Binder)), key=lambda node: (node.lineno, node.col_offset)
    )
    modules: dict[str, str] = {}
    members: dict[str, tuple[str, str]] = {}
    for node in binders:
        for name in _bound_names(node):
            if name in modules:
                del modules[name]
            if name in members:
                del members[name]
        imported_modules, imported_members = _bindings((node,), ("itertools",))
        modules |= imported_modules
        members |= imported_members
    return modules, members


def _wraps_lazily(func: ast.expr, modules: dict[str, str], members: dict[str, tuple[str, str]]) -> bool:
    """A builtin lazy wrapper, or a lazy itertools function reached through an import (never a bare name alone)."""
    if _callee_name(func) in _LAZY_WRAPPERS:
        return True
    if isinstance(func, ast.Name):
        return func.id in members and members[func.id][1] in LAZY_ITERTOOLS
    return (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id in modules
        and func.attr in LAZY_ITERTOOLS
    )


def _stored_generators(tree: ast.Module) -> set[int]:
    """Generator expressions the module only stores or tests for truth: alone, inside lazy wrappers or containers,
    as a branch of a conditional expression, or through a walrus (`g = (x for x in y)`, `m = map(f, (x for x in y))`,
    `gens = [(x for x in y)]`, `if (g := (x for x in y)):`). Any other position consumes the generator while the
    module loads: a call, a loop, an unpacking, a starred element, a comprehension, a membership test. A default
    argument stays reported, as a decorator argument does: a call at load consumes it unseeded. A generator stored
    and consumed later at module level is missed."""
    stored: set[int] = set()
    modules, members = _itertools_bindings(_module_scope_nodes(tree))

    def mark(value: ast.expr | None) -> None:
        if isinstance(value, ast.GeneratorExp):
            stored.add(id(value))
        elif isinstance(value, ast.Call) and _wraps_lazily(value.func, modules, members):
            for argument in value.args:
                mark(argument)
        elif isinstance(value, ast.List | ast.Tuple | ast.Set):
            for element in value.elts:
                mark(element)  # a starred element is no generator here: it stays consumed
        elif isinstance(value, ast.Dict):
            for key, item in zip(value.keys, value.values, strict=True):
                if key is not None:  # a None key is a ** unpacking
                    mark(key)
                    mark(item)
        elif isinstance(value, ast.IfExp):
            for part in (value.test, value.body, value.orelse):
                mark(part)
        elif isinstance(value, ast.NamedExpr):
            mark(value.value)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Tuple | ast.List | ast.Starred) for t in node.targets
        ):
            continue  # unpacking consumes the generator
        if isinstance(node, ast.Assign | ast.AnnAssign | ast.Expr):
            mark(node.value)
        elif isinstance(node, ast.If | ast.While):
            mark(node.test)
    return stored


def _generator_parts(generator: ast.GeneratorExp) -> list[ast.AST]:
    """The parts of a generator expression that run once something consumes it."""
    parts: list[ast.AST] = [generator.elt]
    for comprehension in generator.generators:
        parts.append(comprehension.iter)
        parts.extend(comprehension.ifs)
    return parts


def _load_time_calls(tree: ast.Module) -> list[ast.Call]:
    """Calls the module body runs while loading: everything except function and lambda bodies and the deferred
    parts of a generator expression. A function's decorators and default arguments run, a class body runs too.
    Annotations do not: the runtime compiles scripts with postponed annotations, so they stay strings."""
    calls: list[ast.Call] = []
    stored = _stored_generators(tree)
    pending: list[ast.AST] = list(tree.body)
    while pending:
        node = pending.pop()
        if isinstance(node, ast.Call):
            calls.append(node)
        if isinstance(node, ast.GeneratorExp):
            if id(node) in stored:
                pending.append(node.generators[0].iter)  # only the outermost iterable is evaluated eagerly
            else:
                pending.extend(_generator_parts(node))
            continue
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
            if not isinstance(node, ast.Lambda):
                pending.extend(node.decorator_list)
            pending.extend(node.args.defaults)
            for default in node.args.kw_defaults:
                if default is not None:
                    pending.append(default)
            continue
        pending.extend(ast.iter_child_nodes(node))
    return calls


def _draws(call: ast.Call, modules: dict[str, str], members: dict[str, tuple[str, str]]) -> bool:
    func = call.func
    if isinstance(func, ast.Name):
        bound = members.get(func.id)
        return bound is not None and _attribute_draws(bound[0], bound[1], call)
    if isinstance(func, ast.Attribute):
        root = func.value
        while isinstance(root, ast.Attribute):
            root = root.value
        if not isinstance(root, ast.Name):
            return False
        module = modules.get(root.id) or (members[root.id][0] if root.id in members else None)
        return module is not None and _attribute_draws(module, func.attr, call)
    return False


def _supplies_seed(call: ast.Call) -> bool:
    """``Random(7)`` and ``seed(a=7)`` supply a seed; ``Random()``, ``Random(None)`` and ``seed(version=2)`` do not."""
    if call.args:
        seed = call.args[0]
    else:
        seeds = [keyword.value for keyword in call.keywords if keyword.arg in ("x", "a")]
        if not seeds:
            return False
        seed = seeds[0]
    return not (isinstance(seed, ast.Constant) and seed.value is None)


def _attribute_draws(module: str, attribute: str, call: ast.Call) -> bool:
    if module == "random" and attribute in _SEEDED_WHEN_GIVEN_A_SEED and _supplies_seed(call):
        return False
    drawing = _DRAWING_ATTRIBUTES[module]
    return drawing is None or attribute in drawing
