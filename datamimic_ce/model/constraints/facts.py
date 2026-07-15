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
    DATA_TYPE_FLOAT,
    DATA_TYPE_INT,
    DATA_TYPE_LIST,
    DATA_TYPE_LITERAL,
    DATA_TYPE_STRING,
)
from datamimic_ce.model.constraints.types import (
    AllOrNone,
    AllowedValuesWhen,
    Constraint,
    Forbids,
    ForbidsWhenValue,
    MutuallyExclusive,
    MutuallyExclusiveWhen,
    RequiredOneOf,
    Requires,
    RequiresWhenValue,
    ValidValues,
)

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
