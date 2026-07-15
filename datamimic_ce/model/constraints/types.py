# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Frozen dataclass constraint vocabulary, the Constraint union, and value-resolution helpers."""

from collections.abc import Callable
from dataclasses import dataclass

# Attribute constants (imported at module level to avoid circular imports)


@dataclass(frozen=True)
class RequiredOneOf:
    """At least one of these XML attributes must be present.

    Example: a <key> must define one of type/source/values/script/generator/constant/pattern/string.
    """

    attrs: frozenset[str]
    message: str | None = None
    lint_only: bool = False


@dataclass(frozen=True)
class MutuallyExclusive:
    """At most one of these attributes may be present.

    Design note: count vs minCount/maxCount is XOR-decomposed as TWO pairwise constraints
    (count ⊕ minCount, count ⊕ maxCount) rather than a single 3-member set, to permit
    the legal minCount+maxCount combination.
    """

    attrs: frozenset[str]
    message: str | None = None
    lint_only: bool = False


@dataclass(frozen=True)
class MutuallyExclusiveWhen:
    """At most one of ``attrs`` may be present when ``when_attr`` is set/truthy.

    Example: with ``source=`` present, ``type=`` and ``selector=`` are alternative
    source entity/query selectors and must not be combined.
    """

    when_attr: str
    attrs: frozenset[str]
    when_true: bool = False
    message: str | None = None
    lint_only: bool = False


@dataclass(frozen=True)
class Requires:
    """If attr is present (or truthy when when_true=True), at least one of needs must be present.

    Design note: when_true=True gates on _attr_true() to match the engine's existing
    unique/cyclic checks, which permit <key unique="false" weights=...> (presence-based
    checks would wrongly reject this as a violation). Use when_true=True only for
    boolean-valued attributes that have legitimate false states.
    """

    attr: str
    needs: frozenset[str]
    when_true: bool = False
    message: str | None = None
    lint_only: bool = False


@dataclass(frozen=True)
class RequiresWhenValue:
    """When ``when_attr`` has one of ``when_values``, require one of ``needs``.

    ``unless`` provides explicit escape attributes. This captures mode rules such
    as ``nestedKey type=list`` needing a count unless a source supplies the size.
    """

    when_attr: str
    when_values: frozenset[str]
    needs: frozenset[str]
    unless: frozenset[str] = frozenset()
    message: str | None = None
    lint_only: bool = False


@dataclass(frozen=True)
class AllOrNone:
    """Either all of these attributes are present, or none are.

    Example: <key> with all-or-none {min, max, granularity} for numeric ranges
    (though technically max alone is valid for an upper bound; this captures tighter
    invariants where they must be a group).
    """

    attrs: frozenset[str]
    message: str | None = None
    lint_only: bool = False


@dataclass(frozen=True)
class Forbids:
    """If attr is present (or truthy when when_true=True), none of excludes may be present.

    Design note: same when_true semantics as Requires, gated on _attr_true().
    When excludes_when_true=True, an excluded attr must ALSO be truthy for violation.
    Example: unique forbids cyclic when BOTH are truthy (not just presence-based).
    """

    attr: str
    excludes: frozenset[str]
    when_true: bool = False
    excludes_when_true: bool = False
    message: str | None = None
    lint_only: bool = False


@dataclass(frozen=True)
class ForbidsWhenValue:
    """When ``when_attr`` has one of ``when_values``, forbid ``excludes``."""

    when_attr: str
    when_values: frozenset[str]
    excludes: frozenset[str]
    message: str | None = None
    lint_only: bool = False


@dataclass(frozen=True)
class ValidValues:
    """The value of attr must be in the set of valid values.

    The values set may be:
    - A frozenset[str] or tuple[str, ...] (static)
    - A zero-arg Callable[[], set[str]] (lazy, evaluated at check time)

    Lazy callables enable drift-proof enum/registry-derived sources: the fact
    references the registry supplier, not a snapshot of its contents. When the
    registry changes, all consumers (lint, parse, agents) re-evaluate and see
    the new set.

    Design note: this constraint only validates when attr IS present. If attr
    is absent (None), validation is skipped — this preserves optional attributes.
    """

    attr: str
    values: frozenset[str] | tuple[str, ...] | Callable[[], set[str]]
    message: str | None = None
    lint_only: bool = False


@dataclass(frozen=True)
class AllowedValuesWhen:
    """When when_attr is present (or truthy when when_true=True), attr if PRESENT
    must be in the set of allowed values.

    Design note: Similar to ValidValues but gated on another attribute's presence/truthiness.
    Presence-based check: when_attr is present -> attr must be in allowed (if attr is present).
    Truthiness-based check: when_true=True gates on _attr_true(when_attr) -> attr must be in allowed.
    Absent attr is always fine (the constraint only applies when both conditions are true).

    Example: unique=true pins distribution to 'random' — when unique is true and distribution
    is present, distribution must be 'random'. Missing distribution is fine (defaults to random).
    """

    attr: str
    allowed: frozenset[str] | tuple[str, ...] | Callable[[], set[str]]
    when_attr: str
    when_true: bool = False
    message: str | None = None
    lint_only: bool = False


# Type alias for any constraint in the vocabulary
Constraint = (
    RequiredOneOf
    | MutuallyExclusive
    | MutuallyExclusiveWhen
    | Requires
    | RequiresWhenValue
    | AllOrNone
    | Forbids
    | ForbidsWhenValue
    | ValidValues
    | AllowedValuesWhen
)


def resolved_values(fact: ValidValues) -> frozenset[str]:
    """The fact's valid-value set with a lazy callable resolved — the ONE typed API for
    consumers that need the concrete set (validators, lint rules), so the
    static-or-callable union is narrowed here once instead of ad-hoc at every call site."""
    values = fact.values
    return frozenset(values() if callable(values) else values)


def resolved_allowed(fact: AllowedValuesWhen) -> frozenset[str]:
    """The fact's allowed-value set with a lazy callable resolved — similar to resolved_values
    but for AllowedValuesWhen constraints."""
    allowed = fact.allowed
    return frozenset(allowed() if callable(allowed) else allowed)
