# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Declarative constraint vocabulary for element attribute rules.

This module defines the constraint types that capture cross-field validation facts
declared on models. Each constraint is a frozen dataclass capturing:

- The attributes involved
- Optional truthiness gates (when_true: some rules apply only when an attr is truthy)
- Optional lint-only flags (facts the engine doesn't hard-enforce)
- Optional message overrides (exact error strings from the validators being migrated)

The JSON schema exposure is derived by a shared callable (constraints_schema_extra)
used by models via `model_config = ConfigDict(json_schema_extra=constraints_schema_extra)`.
This ensures one declaration, all consumers derive consistently.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

# Attribute constants (imported at module level to avoid circular imports)
from datamimic_ce.constants.attribute_constants import (
    ATTR_COUNT,
    ATTR_CYCLIC,
    ATTR_DEFAULT_VALUE,
    ATTR_ENTITY,
    ATTR_GENERATOR,
    ATTR_MAX_COUNT,
    ATTR_MIN_COUNT,
    ATTR_SCRIPT,
    ATTR_SELECTOR,
    ATTR_SEPARATOR,
    ATTR_SOURCE,
    ATTR_SOURCE_SCRIPTED,
    ATTR_UNIQUE,
    ATTR_VALUES,
    ATTR_WEIGHT_COLUMN,
    ATTR_WEIGHTS,
)


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
    """
    attr: str
    excludes: frozenset[str]
    when_true: bool = False
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


# Type alias for any constraint in the vocabulary
Constraint = RequiredOneOf | MutuallyExclusive | Requires | AllOrNone | Forbids | ValidValues


def resolved_values(fact: ValidValues) -> frozenset[str]:
    """The fact's valid-value set with a lazy callable resolved — the ONE typed API for
    consumers that need the concrete set (validators, lint rules), so the
    static-or-callable union is narrowed here once instead of ad-hoc at every call site."""
    values = fact.values
    return frozenset(values() if callable(values) else values)


# ============================================================================
# Module-level constraint constants used by multiple models and delegating
# ModelUtil methods (shared vocabulary, drift-proof by single source)
# ============================================================================

# Fact 2: weights requires values (check_weights_require_values in model_util:109-113)
WEIGHTS_REQUIRE_VALUES = Requires(
    ATTR_WEIGHTS,
    frozenset((ATTR_VALUES,)),
    message="'weights' is only allowed together with 'values'",
)

# Fact 1: at least one count-like attribute must exist (check_exist_count in model_util:95-106)
EXIST_COUNT = RequiredOneOf(
    frozenset((ATTR_SOURCE, ATTR_SCRIPT, ATTR_COUNT, ATTR_MIN_COUNT, ATTR_MAX_COUNT)),
    message="Missing attribute 'count' ('count' might be optional in case 'source and script are not defined')",
)

# Fact 3a: unique requires values or source (check_unique_constraints, part 1)
UNIQUE_REQUIRES_POOL = Requires(
    ATTR_UNIQUE,
    frozenset((ATTR_VALUES, ATTR_SOURCE)),
    when_true=True,
    message="'unique' requires 'values' or 'source' (a finite pool)",
)

# Fact 3b: unique forbids weights (check_unique_constraints, part 2)
UNIQUE_FORBIDS_WEIGHTS = Forbids(
    ATTR_UNIQUE,
    frozenset((ATTR_WEIGHTS,)),
    when_true=True,
    message="'unique' cannot be combined with 'weights'",
)

# Fact 3c: count XOR minCount (check_min_max_count, part 1 — minCount>maxCount ordering stays imperative)
COUNT_XOR_MIN = MutuallyExclusive(
    frozenset((ATTR_COUNT, ATTR_MIN_COUNT)),
    # Message is parameterized by element_tag in delegate; declared here for schema only
    message=None,
)

# Fact 3d: count XOR maxCount (check_min_max_count, part 2)
COUNT_XOR_MAX = MutuallyExclusive(
    frozenset((ATTR_COUNT, ATTR_MAX_COUNT)),
    # Message is parameterized by element_tag in delegate; declared here for schema only
    message=None,
)

# Fact 5a-e: companion attributes require source (check_valid_additional_source_attributes)
# Ordered to match original list at model_util.py:207-213 for consistent error ordering.
# Messages reproduce the original _check_valid_additional_attributes f-string output exactly,
# including its quoted-tuple rendering of main_attributes: '('source',)'.
CYCLIC_REQUIRES_SOURCE = Requires(
    ATTR_CYCLIC,
    frozenset((ATTR_SOURCE,)),
    message="'cyclic' is only allowed when one of '('source',)' is defined",
)
SELECTOR_REQUIRES_SOURCE = Requires(
    ATTR_SELECTOR,
    frozenset((ATTR_SOURCE,)),
    message="'selector' is only allowed when one of '('source',)' is defined",
)
SEPARATOR_REQUIRES_SOURCE = Requires(
    ATTR_SEPARATOR,
    frozenset((ATTR_SOURCE,)),
    message="'separator' is only allowed when one of '('source',)' is defined",
)
SOURCE_SCRIPTED_REQUIRES_SOURCE = Requires(
    ATTR_SOURCE_SCRIPTED,
    frozenset((ATTR_SOURCE,)),
    message="'sourceScripted' is only allowed when one of '('source',)' is defined",
)
WEIGHT_COLUMN_REQUIRES_SOURCE = Requires(
    ATTR_WEIGHT_COLUMN,
    frozenset((ATTR_SOURCE,)),
    message="'weightColumn' is only allowed when one of '('source',)' is defined",
)

# Tuple of all source companions (used by both check_valid_additional_source_attributes
# and check_valid_additional_source_attributes_without_cyclic)
SOURCE_COMPANIONS_WITH_CYCLIC: tuple[Requires, ...] = (
    CYCLIC_REQUIRES_SOURCE,
    SELECTOR_REQUIRES_SOURCE,
    SEPARATOR_REQUIRES_SOURCE,
    SOURCE_SCRIPTED_REQUIRES_SOURCE,
    WEIGHT_COLUMN_REQUIRES_SOURCE,
)

SOURCE_COMPANIONS_WITHOUT_CYCLIC: tuple[Requires, ...] = (
    SELECTOR_REQUIRES_SOURCE,
    SEPARATOR_REQUIRES_SOURCE,
    SOURCE_SCRIPTED_REQUIRES_SOURCE,
    WEIGHT_COLUMN_REQUIRES_SOURCE,
)

# Fact 6: addon attributes require generator OR entity (check_valid_additional_generator_entity_attributes)
# Messages reproduce the original _check_valid_additional_attributes f-string output exactly.
DATASET_REQUIRES_GENERATOR_OR_ENTITY = Requires(
    "dataset",
    frozenset((ATTR_GENERATOR, ATTR_ENTITY)),
    message="'dataset' is only allowed when one of '('generator', 'entity')' is defined",
)
LOCALE_REQUIRES_GENERATOR_OR_ENTITY = Requires(
    "locale",
    frozenset((ATTR_GENERATOR, ATTR_ENTITY)),
    message="'locale' is only allowed when one of '('generator', 'entity')' is defined",
)
AGE_MIN_REQUIRES_GENERATOR_OR_ENTITY = Requires(
    "ageMin",
    frozenset((ATTR_GENERATOR, ATTR_ENTITY)),
    message="'ageMin' is only allowed when one of '('generator', 'entity')' is defined",
)
AGE_MAX_REQUIRES_GENERATOR_OR_ENTITY = Requires(
    "ageMax",
    frozenset((ATTR_GENERATOR, ATTR_ENTITY)),
    message="'ageMax' is only allowed when one of '('generator', 'entity')' is defined",
)
CONDITIONS_INCLUDE_REQUIRES_GENERATOR_OR_ENTITY = Requires(
    "conditionsInclude",
    frozenset((ATTR_GENERATOR, ATTR_ENTITY)),
    message="'conditionsInclude' is only allowed when one of '('generator', 'entity')' is defined",
)
CONDITIONS_EXCLUDE_REQUIRES_GENERATOR_OR_ENTITY = Requires(
    "conditionsExclude",
    frozenset((ATTR_GENERATOR, ATTR_ENTITY)),
    message="'conditionsExclude' is only allowed when one of '('generator', 'entity')' is defined",
)
RNG_SEED_REQUIRES_GENERATOR_OR_ENTITY = Requires(
    "rngSeed",
    frozenset((ATTR_GENERATOR, ATTR_ENTITY)),
    message="'rngSeed' is only allowed when one of '('generator', 'entity')' is defined",
)

GENERATOR_ENTITY_ADDONS: tuple[Requires, ...] = (
    DATASET_REQUIRES_GENERATOR_OR_ENTITY,
    LOCALE_REQUIRES_GENERATOR_OR_ENTITY,
    AGE_MIN_REQUIRES_GENERATOR_OR_ENTITY,
    AGE_MAX_REQUIRES_GENERATOR_OR_ENTITY,
    CONDITIONS_INCLUDE_REQUIRES_GENERATOR_OR_ENTITY,
    CONDITIONS_EXCLUDE_REQUIRES_GENERATOR_OR_ENTITY,
    RNG_SEED_REQUIRES_GENERATOR_OR_ENTITY,
)

# Fact 7: default value requires script (check_valid_default_value)
DEFAULT_VALUE_REQUIRES_SCRIPT = Requires(
    ATTR_DEFAULT_VALUE,
    frozenset((ATTR_SCRIPT,)),
    message="Attribute 'defaultValue' must be defined along with 'script'",
)


def serialize_constraints(constraints: tuple[Constraint, ...]) -> list[dict[str, Any]]:
    """Serialize a tuple of constraints to a list of dicts with kind discriminators.

    Used by:
    - constraints_schema_extra: inject into Pydantic model JSON schemas
    - capabilities_manifest: expose constraints in the DSL reference
    - element_reference: render prose descriptions

    Each constraint becomes a dict with a "kind" discriminator and fact-specific fields.

    Args:
        constraints: A tuple of Constraint instances (from a model's __constraints__)

    Returns:
        A list of serialized constraint dicts, empty if constraints is empty
    """
    if not constraints:
        return []

    serialized = []
    for fact in constraints:
        serialized_fact: dict[str, Any] = {"kind": _constraint_kind(fact)}

        if isinstance(fact, RequiredOneOf | MutuallyExclusive):
            serialized_fact["attrs"] = sorted(fact.attrs)
        elif isinstance(fact, Requires):
            serialized_fact["attr"] = fact.attr
            serialized_fact["needs"] = sorted(fact.needs)
            serialized_fact["when_true"] = fact.when_true
        elif isinstance(fact, AllOrNone):
            serialized_fact["attrs"] = sorted(fact.attrs)
        elif isinstance(fact, Forbids):
            serialized_fact["attr"] = fact.attr
            serialized_fact["excludes"] = sorted(fact.excludes)
            serialized_fact["when_true"] = fact.when_true
        elif isinstance(fact, ValidValues):
            serialized_fact["attr"] = fact.attr
            # Evaluate callable values to sorted list; static sets are already sorted
            if callable(fact.values):
                serialized_fact["values"] = sorted(fact.values())
            else:
                serialized_fact["values"] = sorted(fact.values)

        # Only serialize lint_only if True (non-default)
        if fact.lint_only:
            serialized_fact["lint_only"] = True

        # Only serialize message if present (non-default)
        if fact.message is not None:
            serialized_fact["message"] = fact.message

        serialized.append(serialized_fact)

    return serialized


def constraints_schema_extra(schema: dict[str, Any], model_class: type) -> None:
    """Inject declared constraints into a Pydantic model's JSON schema.

    This callable is used as every model's:
        model_config = ConfigDict(json_schema_extra=constraints_schema_extra)

    It reads __constraints__ (if present and non-empty) from the model class and
    injects a "constraints" key into the schema with serialized constraint dicts.

    Args:
        schema: The JSON schema dict being built (mutated in place)
        model_class: The model class being schematized
    """
    constraints = getattr(model_class, "__constraints__", None)
    if not constraints:
        return

    schema["constraints"] = serialize_constraints(constraints)


def _constraint_kind(fact: Constraint) -> str:
    """Map a constraint instance to its kind discriminator string."""
    if isinstance(fact, RequiredOneOf):
        return "required_one_of"
    elif isinstance(fact, MutuallyExclusive):
        return "mutually_exclusive"
    elif isinstance(fact, Requires):
        return "requires"
    elif isinstance(fact, AllOrNone):
        return "all_or_none"
    elif isinstance(fact, Forbids):
        return "forbids"
    elif isinstance(fact, ValidValues):
        return "valid_values"
    else:
        raise TypeError(f"Unknown constraint type: {type(fact)}")
