# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Declarative constraint vocabulary and central CE element-rule registry.

This module is the SPOT for business rules that can be expressed from XML
attributes. Models execute these facts, while authoring schema/reference/lint
derive from the same tuples. Each constraint is a frozen dataclass capturing:

- The attributes involved
- Optional truthiness gates (when_true: some rules apply only when an attr is truthy)
- Optional lint-only flags (facts the engine doesn't hard-enforce)
- Optional message overrides (exact error strings from the validators being migrated)

The JSON schema exposure is derived by a shared callable factory
(``constraints_schema_extra``) bound explicitly to each model's central tuple.
This ensures one declaration, all consumers derive consistently.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any

# Attribute constants (imported at module level to avoid circular imports)
from datamimic_ce.constants.attribute_constants import (
    ATTR_CONDITION,
    ATTR_CONSTANT,
    ATTR_COUNT,
    ATTR_CYCLIC,
    ATTR_DEFAULT_VALUE,
    ATTR_DISTRIBUTION,
    ATTR_END,
    ATTR_ENTITY,
    ATTR_GENERATOR,
    ATTR_INTERVAL,
    ATTR_MAX,
    ATTR_MAX_COUNT,
    ATTR_MIN,
    ATTR_MIN_COUNT,
    ATTR_OFFSET,
    ATTR_OUT_DATE_FORMAT,
    ATTR_PATTERN,
    ATTR_SCRIPT,
    ATTR_SELECTOR,
    ATTR_SEPARATOR,
    ATTR_SOURCE,
    ATTR_SOURCE_ENTITY,
    ATTR_SOURCE_SCRIPTED,
    ATTR_START,
    ATTR_STORAGE,
    ATTR_STRING,
    ATTR_TYPE,
    ATTR_UNIQUE,
    ATTR_URI,
    ATTR_VALUES,
    ATTR_WEIGHT_COLUMN,
    ATTR_WEIGHTS,
)
from datamimic_ce.constants.data_type_constants import (
    DATA_TYPE_BINARY,
    DATA_TYPE_BOOL,
    DATA_TYPE_DECIMAL,
    DATA_TYPE_DICT,
    DATA_TYPE_FLOAT,
    DATA_TYPE_INT,
    DATA_TYPE_LIST,
    DATA_TYPE_LITERAL,
    DATA_TYPE_STRING,
)
from datamimic_ce.constants.element_constants import (
    EL_ARRAY,
    EL_ASSERT,
    EL_CONDITION,
    EL_DATABASE,
    EL_DEMOGRAPHICS,
    EL_ECHO,
    EL_ELEMENT,
    EL_ELSE,
    EL_ELSE_IF,
    EL_EXECUTE,
    EL_FIELD,
    EL_GENERATE,
    EL_GENERATOR,
    EL_ID,
    EL_IF,
    EL_INCLUDE,
    EL_ITEM,
    EL_ITERATE,
    EL_KEY,
    EL_LIST,
    EL_MEMSTORE,
    EL_MONGODB,
    EL_NESTED_KEY,
    EL_REFERENCE,
    EL_SETUP,
    EL_STATE_MACHINE,
    EL_TRANSITION,
    EL_VALUE,
    EL_VARIABLE,
    EL_WHILE,
)


class DynamicSourceKind(StrEnum):
    PYTHON_EXPRESSION = "python_expression"
    BRACED_EXPRESSION = "braced_expression"


class SourceFileFormat(StrEnum):
    """Canonical runtime file formats accepted by ``source=`` consumers."""

    DBUNIT_XML = ".dbunit.xml"
    WEIGHTED_ENTITY_CSV = ".wgt.ent.csv"
    WEIGHTED_CSV = ".wgt.csv"
    CSV = ".csv"
    JSON = ".json"
    XLSX = ".xlsx"
    XML = ".xml"
    FIXED_WIDTH = ".fcw"


@dataclass(frozen=True)
class SourceCapability:
    """One runtime-supported ``source=`` context.

    ``source_type`` narrows shape-sensitive consumers such as ``nestedKey``.
    File-loader implementations stay in their runtime tasks; this fact owns only
    which source kinds and suffixes each element is allowed to dispatch.
    """

    element: str
    file_formats: tuple[SourceFileFormat, ...] = ()
    source_type: str | None = None
    allows_memstore: bool = False
    allows_client: bool = False
    dynamic_source: DynamicSourceKind | None = None


_SOURCE_CAPABILITIES: tuple[SourceCapability, ...] = (
    SourceCapability(
        EL_GENERATE,
        (
            SourceFileFormat.DBUNIT_XML,
            SourceFileFormat.CSV,
            SourceFileFormat.JSON,
            SourceFileFormat.XLSX,
            SourceFileFormat.XML,
            SourceFileFormat.FIXED_WIDTH,
        ),
        allows_memstore=True,
        allows_client=True,
    ),
    SourceCapability(
        EL_ITERATE,
        (
            SourceFileFormat.DBUNIT_XML,
            SourceFileFormat.CSV,
            SourceFileFormat.JSON,
            SourceFileFormat.XLSX,
            SourceFileFormat.XML,
            SourceFileFormat.FIXED_WIDTH,
        ),
        allows_memstore=True,
        allows_client=True,
    ),
    SourceCapability(
        EL_VARIABLE,
        (
            SourceFileFormat.WEIGHTED_ENTITY_CSV,
            SourceFileFormat.CSV,
            SourceFileFormat.JSON,
            SourceFileFormat.XLSX,
            SourceFileFormat.FIXED_WIDTH,
        ),
        allows_memstore=True,
        allows_client=True,
        dynamic_source=DynamicSourceKind.PYTHON_EXPRESSION,
    ),
    SourceCapability(
        EL_NESTED_KEY,
        allows_memstore=True,
        dynamic_source=DynamicSourceKind.BRACED_EXPRESSION,
    ),
    SourceCapability(
        EL_NESTED_KEY,
        (SourceFileFormat.CSV, SourceFileFormat.JSON),
        source_type=DATA_TYPE_LIST,
    ),
    SourceCapability(EL_NESTED_KEY, (SourceFileFormat.JSON,), source_type=DATA_TYPE_DICT),
    SourceCapability(EL_KEY, (SourceFileFormat.WEIGHTED_CSV,)),
    SourceCapability(EL_ID, (SourceFileFormat.WEIGHTED_CSV,)),
    SourceCapability(EL_ELEMENT, (SourceFileFormat.WEIGHTED_CSV,)),
    SourceCapability(EL_REFERENCE, allows_client=True),
)


def source_capabilities() -> tuple[SourceCapability, ...]:
    """Return the immutable runtime source-capability catalog."""

    return _SOURCE_CAPABILITIES


def serialize_source_capability(capability: SourceCapability) -> dict[str, object]:
    """Project one source-capability fact to reference/capabilities JSON."""

    return {
        "element": capability.element,
        "source_type": capability.source_type,
        "file_suffixes": [file_format.value for file_format in capability.file_formats],
        "allows_memstore": capability.allows_memstore,
        "allows_client": capability.allows_client,
        "dynamic_source": capability.dynamic_source.value if capability.dynamic_source is not None else None,
    }


def _source_capabilities_for(element: str, source_type: str | None = None) -> tuple[SourceCapability, ...]:
    return tuple(
        capability
        for capability in _SOURCE_CAPABILITIES
        if capability.element == element and capability.source_type in (None, source_type)
    )


def supported_source_file_formats(
    element: str,
    source_type: str | None = None,
) -> tuple[SourceFileFormat, ...]:
    """File formats accepted by one element/shape, longest suffix first."""

    formats = {
        file_format
        for capability in _source_capabilities_for(element, source_type)
        for file_format in capability.file_formats
    }
    return tuple(sorted(formats, key=lambda file_format: (-len(file_format.value), file_format.value)))


def recognized_source_file_formats() -> tuple[SourceFileFormat, ...]:
    """All file formats known anywhere in CE, for unsupported-context diagnostics."""

    formats = {file_format for capability in _SOURCE_CAPABILITIES for file_format in capability.file_formats}
    return tuple(sorted(formats, key=lambda file_format: (-len(file_format.value), file_format.value)))


def source_file_format(source: str) -> SourceFileFormat | None:
    """Return a file format recognized by any runtime source context, if present."""

    return next(
        (file_format for file_format in recognized_source_file_formats() if source.endswith(file_format.value)),
        None,
    )


def source_file_format_for(
    element: str,
    source: str,
    source_type: str | None = None,
) -> SourceFileFormat | None:
    """Return the typed format this concrete runtime source context dispatches."""

    return next(
        (
            file_format
            for file_format in supported_source_file_formats(element, source_type)
            if source.endswith(file_format.value)
        ),
        None,
    )


def is_source_file(source: str, element: str, source_type: str | None = None) -> bool:
    """Whether one concrete runtime source context supports ``source`` as a file."""

    return source_file_format_for(element, source, source_type) is not None


def source_allows_memstore(element: str, source_type: str | None = None) -> bool:
    return any(capability.allows_memstore for capability in _source_capabilities_for(element, source_type))


def source_allows_client(element: str, source_type: str | None = None) -> bool:
    return any(capability.allows_client for capability in _source_capabilities_for(element, source_type))


def source_dynamic_kind(element: str, source_type: str | None = None) -> DynamicSourceKind | None:
    return next(
        (
            capability.dynamic_source
            for capability in _source_capabilities_for(element, source_type)
            if capability.dynamic_source is not None
        ),
        None,
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

# A <key source="...wgt.csv"> is a legacy weighted-source mode implemented by
# KeyVariableTask with replacement; it deliberately rejects unique selection at
# runtime.  Keep that business rule in the model contract so authoring/lint fails
# before task construction.  Source-backed unique selection belongs to <variable>,
# <generate>, <nestedKey>, and <reference>.
KEY_UNIQUE_REQUIRES_VALUES = Requires(
    ATTR_UNIQUE,
    frozenset((ATTR_VALUES,)),
    when_true=True,
    message="'unique' on <key> requires 'values'; key source= is weighted with replacement",
)

# Fact 3b: unique forbids weights (check_unique_constraints, part 2)
UNIQUE_FORBIDS_WEIGHTS = Forbids(
    ATTR_UNIQUE,
    frozenset((ATTR_WEIGHTS,)),
    when_true=True,
    message="'unique' cannot be combined with 'weights'",
)

# Fact 3c: unique forbids cyclic (both truthy) (check_unique_constraints, part 3)
UNIQUE_FORBIDS_CYCLIC = Forbids(
    ATTR_UNIQUE,
    frozenset((ATTR_CYCLIC,)),
    when_true=True,
    excludes_when_true=True,
    message="'unique' cannot be combined with 'cyclic' (no-repeat vs repeat)",
)

# Fact 3d: source-backed unique pins source selection to 'random'. The generic
# executor renders ``actual_value`` from this same fact, so runtime, lint and
# authoring all consume one declaration.
UNIQUE_DISTRIBUTION_RANDOM = AllowedValuesWhen(
    ATTR_DISTRIBUTION,
    frozenset(("random",)),  # SourceDistribution.RANDOM.value
    ATTR_UNIQUE,
    when_true=True,
    message="'unique' only combines with distribution='random' (it implies distinct random order), "
    "not '{actual_value}'",
)

# A <key> uses distribution= for NumberDistribution over a numeric range, not
# SourceDistribution for source-row selection. Combining that independent
# numeric shape with unique pool selection is therefore always invalid.
KEY_UNIQUE_FORBIDS_DISTRIBUTION = Forbids(
    ATTR_UNIQUE,
    frozenset((ATTR_DISTRIBUTION,)),
    when_true=True,
    message="'unique' cannot be combined with 'distribution' on <key> "
    "(key distribution shapes a numeric range, not source selection)",
)

# Fact 3e: count XOR minCount (check_min_max_count, part 1 — minCount>maxCount ordering stays imperative)
COUNT_XOR_MIN = MutuallyExclusive(
    frozenset((ATTR_COUNT, ATTR_MIN_COUNT)),
    # Message is parameterized by element_tag in delegate; declared here for schema only
    message=None,
)

# Fact 3f: count XOR maxCount (check_min_max_count, part 2)
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
SOURCE_ENTITY_REQUIRES_SOURCE = Requires(
    ATTR_SOURCE_ENTITY,
    frozenset((ATTR_SOURCE,)),
    message="'sourceEntity' requires 'source'",
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

# Element-specific projections. A rule exposed for a tag must never mention an
# attribute that tag cannot accept; otherwise CLI/MCP would recommend invalid XML.
GENERATE_SOURCE_COMPANIONS: tuple[Requires, ...] = (
    CYCLIC_REQUIRES_SOURCE,
    SELECTOR_REQUIRES_SOURCE,
    SEPARATOR_REQUIRES_SOURCE,
    SOURCE_SCRIPTED_REQUIRES_SOURCE,
    SOURCE_ENTITY_REQUIRES_SOURCE,
)
KEY_SOURCE_COMPANIONS: tuple[Requires, ...] = (
    SELECTOR_REQUIRES_SOURCE,
    SEPARATOR_REQUIRES_SOURCE,
)
VARIABLE_SOURCE_COMPANIONS: tuple[Requires, ...] = (
    CYCLIC_REQUIRES_SOURCE,
    SELECTOR_REQUIRES_SOURCE,
    SEPARATOR_REQUIRES_SOURCE,
    SOURCE_SCRIPTED_REQUIRES_SOURCE,
    WEIGHT_COLUMN_REQUIRES_SOURCE,
    SOURCE_ENTITY_REQUIRES_SOURCE,
)
NESTED_KEY_SOURCE_COMPANIONS: tuple[Requires, ...] = (
    SEPARATOR_REQUIRES_SOURCE,
    SOURCE_SCRIPTED_REQUIRES_SOURCE,
    SOURCE_ENTITY_REQUIRES_SOURCE,
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

# ---------------------------------------------------------------------------
# Element-specific rule facts.  Keep the instances here, never in model files:
# this module is the rule SPOT; models only select/execute these declarations.

SOURCE_MODE_EXCLUSIVE = MutuallyExclusiveWhen(
    ATTR_SOURCE,
    frozenset((ATTR_TYPE, ATTR_SELECTOR)),
    message="Only one of 'type' or 'selector' can be defined together with 'source'",
)

TIMESERIES_ALL_OR_NONE = AllOrNone(frozenset((ATTR_START, ATTR_END, ATTR_INTERVAL)))
GENERATE_OFFSET_REQUIRES_SOURCE = Requires(
    ATTR_OFFSET,
    frozenset((ATTR_SOURCE,)),
    message="'offset' requires a 'source' - it skips the first N source rows",
)
ITERATE_REQUIRES_SOURCE = RequiredOneOf(
    frozenset((ATTR_SOURCE,)),
    message="<iterate> requires a 'source' to iterate over; use <generate> for synthetic data",
)

KEY_GENERATION_REQUIRED = RequiredOneOf(
    frozenset(
        (
            ATTR_TYPE,
            ATTR_SOURCE,
            ATTR_VALUES,
            ATTR_SCRIPT,
            ATTR_GENERATOR,
            ATTR_CONSTANT,
            ATTR_PATTERN,
            ATTR_STRING,
        )
    )
)
KEY_GENERATION_EXCLUSIVE = MutuallyExclusive(
    frozenset((ATTR_SOURCE, ATTR_VALUES, ATTR_SCRIPT, ATTR_GENERATOR, ATTR_CONSTANT, ATTR_PATTERN))
)
KEY_TYPE_VALUES = ValidValues(
    ATTR_TYPE,
    frozenset(
        (
            DATA_TYPE_STRING,
            DATA_TYPE_INT,
            DATA_TYPE_FLOAT,
            DATA_TYPE_DECIMAL,
            DATA_TYPE_BOOL,
            DATA_TYPE_BINARY,
        )
    ),
)
KEY_UNIQUE_CONSTRAINTS: tuple[Constraint, ...] = (
    KEY_UNIQUE_REQUIRES_VALUES,
    UNIQUE_FORBIDS_WEIGHTS,
    KEY_UNIQUE_FORBIDS_DISTRIBUTION,
)
KEY_DISTRIBUTION_REQUIRES_TYPE = Requires(
    ATTR_DISTRIBUTION,
    frozenset((ATTR_TYPE,)),
    message="'distribution' on a <key> requires a numeric type",
)
KEY_DISTRIBUTION_REQUIRES_RANGE = Requires(
    ATTR_DISTRIBUTION,
    frozenset((ATTR_MIN, ATTR_MAX)),
    message="'distribution' on a <key> needs a range - add min= and/or max=",
)
KEY_DISTRIBUTION_NUMERIC_TYPE = AllowedValuesWhen(
    ATTR_TYPE,
    frozenset((DATA_TYPE_INT, DATA_TYPE_FLOAT, DATA_TYPE_DECIMAL)),
    ATTR_DISTRIBUTION,
    message="'distribution' on a <key> requires type='int', 'float', or 'decimal', not '{actual_value}'",
)
OUT_DATE_FORMAT_STRING_TYPE = AllowedValuesWhen(
    ATTR_TYPE,
    frozenset((DATA_TYPE_STRING,)),
    ATTR_OUT_DATE_FORMAT,
    message="when 'outDateFormat' is defined, 'type' must be omitted or 'string', not '{actual_value}'",
)


def _source_distribution_values() -> set[str]:
    """Resolve the CE source-selection vocabulary lazily from its runtime enum."""
    from datamimic_ce.enums.distribution_enums import SourceDistribution

    return {member.value for member in SourceDistribution}


def _number_distribution_values() -> set[str]:
    """Resolve the CE numeric-range vocabulary lazily from its runtime enum."""
    from datamimic_ce.enums.distribution_enums import NumberDistribution

    return {member.value for member in NumberDistribution}


SOURCE_DISTRIBUTION_VALUES = ValidValues(ATTR_DISTRIBUTION, _source_distribution_values)
KEY_DISTRIBUTION_VALUES = ValidValues(ATTR_DISTRIBUTION, _number_distribution_values)

VARIABLE_GENERATION_REQUIRED = RequiredOneOf(
    frozenset(
        (
            ATTR_SOURCE,
            ATTR_ENTITY,
            ATTR_SCRIPT,
            ATTR_GENERATOR,
            ATTR_VALUES,
            ATTR_CONSTANT,
            ATTR_TYPE,
            ATTR_PATTERN,
            ATTR_STRING,
        )
    )
)
VARIABLE_GENERATION_EXCLUSIVE = MutuallyExclusive(
    frozenset(
        (
            ATTR_SOURCE,
            ATTR_ENTITY,
            ATTR_SCRIPT,
            ATTR_GENERATOR,
            ATTR_VALUES,
            ATTR_CONSTANT,
            ATTR_PATTERN,
            ATTR_STRING,
        )
    )
)
VARIABLE_STORAGE_VALUES = ValidValues(ATTR_STORAGE, ("value", "data", "iterator"))
ITERATION_SELECTOR_REQUIRES_SOURCE = Requires(
    "iterationSelector",
    frozenset((ATTR_SOURCE,)),
    lint_only=True,
    message="'iterationSelector' requires 'source'",
)

NESTED_CYCLIC_REQUIRES_SOURCE_OR_SCRIPT = Requires(
    ATTR_CYCLIC,
    frozenset((ATTR_SOURCE, ATTR_SCRIPT)),
    message="'cyclic' is only allowed when one of ('source', 'script') is defined",
)
NESTED_CYCLIC_REQUIRES_COUNT = Requires(
    ATTR_CYCLIC,
    frozenset((ATTR_COUNT, ATTR_MIN_COUNT, ATTR_MAX_COUNT)),
    message="'cyclic' on <nestedKey> requires count, minCount, or maxCount to avoid an infinite loop",
)
NESTED_LIST_REQUIRES_COUNT = RequiresWhenValue(
    ATTR_TYPE,
    frozenset((DATA_TYPE_LIST,)),
    frozenset((ATTR_COUNT, ATTR_MIN_COUNT, ATTR_MAX_COUNT)),
    unless=frozenset((ATTR_SOURCE,)),
    message="type='list' on <nestedKey> requires count, minCount, or maxCount unless source supplies the size",
)
NESTED_SCRIPT_FORBIDDEN_ATTRS: tuple[str, ...] = (
    ATTR_TYPE,
    ATTR_SOURCE,
    ATTR_SOURCE_SCRIPTED,
    ATTR_SEPARATOR,
)
NESTED_SCRIPT_FORBIDS = Forbids(ATTR_SCRIPT, frozenset(NESTED_SCRIPT_FORBIDDEN_ATTRS))
NESTED_CONDITION_RECOMMENDS_DEFAULT = Requires(
    ATTR_CONDITION,
    frozenset((ATTR_DEFAULT_VALUE,)),
    lint_only=True,
    message="conditional <nestedKey> should define defaultValue= so the output shape remains stable",
)
NESTED_SCRIPT_RECOMMENDS_DEFAULT = Requires(
    ATTR_SCRIPT,
    frozenset((ATTR_DEFAULT_VALUE,)),
    lint_only=True,
    message="scripted <nestedKey> should define defaultValue= as an explicit failure fallback",
)

ARRAY_TYPE_VALUES = ValidValues(
    ATTR_TYPE,
    frozenset((DATA_TYPE_STRING, DATA_TYPE_INT, DATA_TYPE_BOOL, DATA_TYPE_FLOAT, DATA_TYPE_LITERAL)),
)
ARRAY_VALUE_MODE_REQUIRED = RequiredOneOf(
    frozenset((ATTR_SCRIPT, ATTR_TYPE)),
    message="<array> requires script= or type=",
)
ARRAY_SCRIPT_FORBIDS_GENERATED_MODE = Forbids(
    ATTR_SCRIPT,
    frozenset((ATTR_COUNT, ATTR_TYPE)),
    message="script= on <array> cannot combine with count= or type=",
)
ARRAY_LITERAL_FORBIDS_GENERATED_MODE = ForbidsWhenValue(
    ATTR_TYPE,
    frozenset((DATA_TYPE_LITERAL,)),
    frozenset((ATTR_COUNT, ATTR_SCRIPT)),
    message="type='literal' on <array> cannot combine with count= or script=",
)
ARRAY_GENERATED_MODE_REQUIRES_COUNT = RequiresWhenValue(
    ATTR_TYPE,
    frozenset((DATA_TYPE_STRING, DATA_TYPE_INT, DATA_TYPE_BOOL, DATA_TYPE_FLOAT)),
    frozenset((ATTR_COUNT,)),
    message="non-literal <array> type requires count=",
)

EXECUTE_TYPE_VALUES = ValidValues(ATTR_TYPE, frozenset(("python", "bash", "sql")))
EXECUTE_URI_SCRIPT_EXCLUSIVE = MutuallyExclusive(
    frozenset((ATTR_URI, ATTR_SCRIPT)),
    message="<execute> accepts exactly one of uri=, inline text, or script=",
)
EXECUTE_SCRIPT_REQUIRES_TYPE = Requires(
    ATTR_SCRIPT,
    frozenset((ATTR_TYPE,)),
    message="script= on <execute> requires type=",
)

GENERATE_UNIQUE_REQUIRES_SOURCE = Requires(
    ATTR_UNIQUE,
    frozenset((ATTR_SOURCE,)),
    when_true=True,
    message="'unique' on <generate>/<iterate> requires 'source'",
)
GENERATE_UNIQUE_CONSTRAINTS: tuple[Constraint, ...] = (
    GENERATE_UNIQUE_REQUIRES_SOURCE,
    UNIQUE_FORBIDS_CYCLIC,
    UNIQUE_DISTRIBUTION_RANDOM,
)


_GENERATE_RULES: tuple[Constraint, ...] = (
    EXIST_COUNT,
    COUNT_XOR_MIN,
    COUNT_XOR_MAX,
    *GENERATE_UNIQUE_CONSTRAINTS,
    *GENERATE_SOURCE_COMPANIONS,
    SOURCE_MODE_EXCLUSIVE,
    TIMESERIES_ALL_OR_NONE,
    GENERATE_OFFSET_REQUIRES_SOURCE,
    SOURCE_DISTRIBUTION_VALUES,
)
_KEY_RULES: tuple[Constraint, ...] = (
    WEIGHTS_REQUIRE_VALUES,
    *KEY_UNIQUE_CONSTRAINTS,
    *KEY_SOURCE_COMPANIONS,
    KEY_GENERATION_REQUIRED,
    KEY_GENERATION_EXCLUSIVE,
    KEY_TYPE_VALUES,
    KEY_DISTRIBUTION_REQUIRES_TYPE,
    KEY_DISTRIBUTION_REQUIRES_RANGE,
    KEY_DISTRIBUTION_NUMERIC_TYPE,
    KEY_DISTRIBUTION_VALUES,
    DEFAULT_VALUE_REQUIRES_SCRIPT,
    OUT_DATE_FORMAT_STRING_TYPE,
)
_VARIABLE_RULES: tuple[Constraint, ...] = (
    WEIGHTS_REQUIRE_VALUES,
    UNIQUE_REQUIRES_POOL,
    UNIQUE_FORBIDS_WEIGHTS,
    UNIQUE_FORBIDS_CYCLIC,
    UNIQUE_DISTRIBUTION_RANDOM,
    *VARIABLE_SOURCE_COMPANIONS,
    SOURCE_MODE_EXCLUSIVE,
    *GENERATOR_ENTITY_ADDONS,
    DEFAULT_VALUE_REQUIRES_SCRIPT,
    OUT_DATE_FORMAT_STRING_TYPE,
    VARIABLE_GENERATION_REQUIRED,
    VARIABLE_GENERATION_EXCLUSIVE,
    VARIABLE_STORAGE_VALUES,
    ITERATION_SELECTOR_REQUIRES_SOURCE,
    SOURCE_DISTRIBUTION_VALUES,
)
_NESTED_KEY_RULES: tuple[Constraint, ...] = (
    COUNT_XOR_MIN,
    COUNT_XOR_MAX,
    *NESTED_KEY_SOURCE_COMPANIONS,
    NESTED_CYCLIC_REQUIRES_SOURCE_OR_SCRIPT,
    NESTED_CYCLIC_REQUIRES_COUNT,
    NESTED_LIST_REQUIRES_COUNT,
    NESTED_SCRIPT_FORBIDS,
    NESTED_CONDITION_RECOMMENDS_DEFAULT,
    NESTED_SCRIPT_RECOMMENDS_DEFAULT,
    SOURCE_DISTRIBUTION_VALUES,
)
_ARRAY_RULES: tuple[Constraint, ...] = (
    ARRAY_TYPE_VALUES,
    ARRAY_VALUE_MODE_REQUIRED,
    ARRAY_SCRIPT_FORBIDS_GENERATED_MODE,
    ARRAY_LITERAL_FORBIDS_GENERATED_MODE,
    ARRAY_GENERATED_MODE_REQUIRES_COUNT,
)
_EXECUTE_RULES: tuple[Constraint, ...] = (
    EXECUTE_TYPE_VALUES,
    EXECUTE_URI_SCRIPT_EXCLUSIVE,
    EXECUTE_SCRIPT_REQUIRES_TYPE,
)
_REFERENCE_RULES: tuple[Constraint, ...] = (
    UNIQUE_FORBIDS_CYCLIC,
    UNIQUE_DISTRIBUTION_RANDOM,
    SOURCE_DISTRIBUTION_VALUES,
)

# Explicit entry for every CE registry tag. Empty tuples are intentional and make
# omissions review-visible: a new built-in element must decide its rule contract.
_ELEMENT_CONSTRAINTS: dict[str, tuple[Constraint, ...]] = {
    EL_SETUP: (),
    EL_GENERATE: _GENERATE_RULES,
    EL_ITERATE: (*_GENERATE_RULES, ITERATE_REQUIRES_SOURCE),
    EL_KEY: _KEY_RULES,
    EL_ID: _KEY_RULES,
    EL_ELEMENT: _KEY_RULES,
    EL_VARIABLE: _VARIABLE_RULES,
    EL_NESTED_KEY: _NESTED_KEY_RULES,
    EL_ARRAY: _ARRAY_RULES,
    EL_VALUE: (),
    EL_LIST: (),
    EL_ITEM: (),
    EL_REFERENCE: _REFERENCE_RULES,
    EL_FIELD: (),
    EL_INCLUDE: (),
    EL_MEMSTORE: (),
    EL_EXECUTE: _EXECUTE_RULES,
    EL_DATABASE: (),
    EL_MONGODB: (),
    EL_IF: (),
    EL_ELSE_IF: (),
    EL_ELSE: (),
    EL_CONDITION: (),
    EL_ECHO: (),
    EL_GENERATOR: (),
    EL_DEMOGRAPHICS: (),
    EL_STATE_MACHINE: (),
    EL_TRANSITION: (),
    EL_WHILE: (),
    EL_ASSERT: (),
}

_EXTENSION_CONSTRAINTS: dict[str, tuple[Constraint, ...]] = {}
_RULE_REGISTRY_REVISION = 0


def element_constraints(tag: str) -> tuple[Constraint, ...]:
    """Return the centrally registered rule facts for one CE DSL tag."""
    return _EXTENSION_CONSTRAINTS.get(tag, _ELEMENT_CONSTRAINTS.get(tag, ()))


def register_element_constraints(tag: str, constraints: tuple[Constraint, ...]) -> None:
    """Register the business-rule contract for one extension element."""
    global _RULE_REGISTRY_REVISION

    if tag in _ELEMENT_CONSTRAINTS or tag in _EXTENSION_CONSTRAINTS:
        raise ValueError(f"business-rule contract for <{tag}> is already registered")
    _EXTENSION_CONSTRAINTS[tag] = constraints
    _RULE_REGISTRY_REVISION += 1


def unregister_element_constraints(tag: str) -> None:
    """Remove an extension rule contract; built-in contracts are immutable."""
    global _RULE_REGISTRY_REVISION

    if tag not in _EXTENSION_CONSTRAINTS:
        raise KeyError(f"extension business-rule contract for <{tag}> is not registered")
    del _EXTENSION_CONSTRAINTS[tag]
    _RULE_REGISTRY_REVISION += 1


def rule_registry_revision() -> int:
    """Return a monotonic revision used by authoring projections."""
    return _RULE_REGISTRY_REVISION


def registered_rule_tags() -> frozenset[str]:
    """Tags with an explicit rule-registry decision, including intentional empties."""
    return frozenset((*_ELEMENT_CONSTRAINTS, *_EXTENSION_CONSTRAINTS))


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

    serialized: list[dict[str, Any]] = []
    for fact in constraints:
        serialized_fact: dict[str, Any] = {"kind": _constraint_kind(fact)}
        serialized_fact.update(_serialized_constraint_fields(fact))

        # Only serialize lint_only if True (non-default)
        if fact.lint_only:
            serialized_fact["lint_only"] = True

        # Only serialize message if present (non-default)
        if fact.message is not None:
            serialized_fact["message"] = fact.message

        serialized.append(serialized_fact)

    return serialized


def _serialized_constraint_fields(fact: Constraint) -> dict[str, Any]:
    if isinstance(fact, RequiredOneOf | MutuallyExclusive | AllOrNone):
        return {"attrs": sorted(fact.attrs)}
    if isinstance(fact, MutuallyExclusiveWhen):
        return {
            "when_attr": fact.when_attr,
            "attrs": sorted(fact.attrs),
            "when_true": fact.when_true,
        }
    if isinstance(fact, Requires):
        return {
            "attr": fact.attr,
            "needs": sorted(fact.needs),
            "when_true": fact.when_true,
        }
    if isinstance(fact, RequiresWhenValue):
        return {
            "when_attr": fact.when_attr,
            "when_values": sorted(fact.when_values),
            "needs": sorted(fact.needs),
            "unless": sorted(fact.unless),
        }
    if isinstance(fact, Forbids):
        return {
            "attr": fact.attr,
            "excludes": sorted(fact.excludes),
            "when_true": fact.when_true,
            "excludes_when_true": fact.excludes_when_true,
        }
    if isinstance(fact, ForbidsWhenValue):
        return {
            "when_attr": fact.when_attr,
            "when_values": sorted(fact.when_values),
            "excludes": sorted(fact.excludes),
        }
    if isinstance(fact, ValidValues):
        return {"attr": fact.attr, "values": sorted(resolved_values(fact))}
    if isinstance(fact, AllowedValuesWhen):
        return {
            "attr": fact.attr,
            "allowed": sorted(resolved_allowed(fact)),
            "when_attr": fact.when_attr,
            "when_true": fact.when_true,
        }
    raise TypeError(f"Unknown constraint type: {type(fact)}")


def constraints_schema_extra(
    constraints: tuple[Constraint, ...],
) -> Callable[[dict[str, Any]], None]:
    """Bind one explicit rule tuple to a Pydantic JSON-schema projector."""

    def inject(schema: dict[str, Any]) -> None:
        if constraints:
            schema["constraints"] = serialize_constraints(constraints)

    return inject


def _constraint_kind(fact: Constraint) -> str:
    """Map a constraint instance to its kind discriminator string."""
    if isinstance(fact, RequiredOneOf):
        return "required_one_of"
    elif isinstance(fact, MutuallyExclusive):
        return "mutually_exclusive"
    elif isinstance(fact, MutuallyExclusiveWhen):
        return "mutually_exclusive_when"
    elif isinstance(fact, Requires):
        return "requires"
    elif isinstance(fact, RequiresWhenValue):
        return "requires_when_value"
    elif isinstance(fact, AllOrNone):
        return "all_or_none"
    elif isinstance(fact, Forbids):
        return "forbids"
    elif isinstance(fact, ForbidsWhenValue):
        return "forbids_when_value"
    elif isinstance(fact, ValidValues):
        return "valid_values"
    elif isinstance(fact, AllowedValuesWhen):
        return "allowed_values_when"
    else:
        raise TypeError(f"Unknown constraint type: {type(fact)}")
