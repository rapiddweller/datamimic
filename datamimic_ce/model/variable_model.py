# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import (
    ATTR_CONSTANT,
    ATTR_CONVERTER,
    ATTR_CYCLIC,
    ATTR_DATABASE,
    ATTR_DATASET,
    ATTR_DEFAULT_VALUE,
    ATTR_DISTRIBUTION,
    ATTR_ENTITY,
    ATTR_GENERATOR,
    ATTR_IN_DATE_FORMAT,
    ATTR_ITERATION_SELECTOR,
    ATTR_LOCALE,
    ATTR_NAME,
    ATTR_OUT_DATE_FORMAT,
    ATTR_PATTERN,
    ATTR_RNG_SEED,
    ATTR_SCRIPT,
    ATTR_SELECTOR,
    ATTR_SEPARATOR,
    ATTR_SOURCE,
    ATTR_SOURCE_ENTITY,
    ATTR_SOURCE_SCRIPTED,
    ATTR_STORAGE,
    ATTR_STRING,
    ATTR_TYPE,
    ATTR_UNIQUE,
    ATTR_VALUES,
    ATTR_VARIABLE_PREFIX,
    ATTR_VARIABLE_SUFFIX,
    ATTR_WEIGHT_COLUMN,
    ATTR_WEIGHTS,
)
from datamimic_ce.constants.element_constants import EL_VARIABLE
from datamimic_ce.model.constraints import (
    SOURCE_DISTRIBUTION_VALUES,
    VARIABLE_GENERATION_EXCLUSIVE,
    VARIABLE_GENERATION_REQUIRED,
    VARIABLE_STORAGE_VALUES,
    Constraint,
    constraints_schema_extra,
    element_constraints,
    resolved_values,
)
from datamimic_ce.model.model_util import ModelUtil


class VariableModel(BaseModel):
    # Declared cross-field constraints
    __constraints__: ClassVar[tuple[Constraint, ...]] = element_constraints(EL_VARIABLE)
    model_config = ConfigDict(json_schema_extra=constraints_schema_extra)

    name: str = Field(
        ...,
        description="Variable name — how this <variable>'s value is referenced by later script=/"
        "condition= expressions in the same record scope (e.g. script=\"<name>.field\" for an "
        "entity variable, bare script=\"<name>\" for a scalar).",
        examples=["p", "row", "customer_id"],
    )
    type: str | None = Field(
        None,
        description="Normally a scalar cast for a generated value (e.g. 'int', 'string'). When "
        "'source' is also set, this instead selects which source-backed statement's rows to read "
        "(a producer name, not a type) — see StatementUtil.resolve_source_entity's "
        "sourceEntity -> type -> name fallback.",
    )
    source: str | None = Field(
        None,
        description="Read rows from a declared source: a <memstore>/<database>/<mongodb> id, or a "
        "file path. Combine with 'type' to pick which produced entity/table to read when the "
        "source holds more than one.",
    )
    # Explicit physical entity to read (sourceEntity -> type -> name). See resolve_source_entity.
    source_entity: str | None = Field(
        None,
        alias=ATTR_SOURCE_ENTITY,
        description="Explicit physical entity to read (table/collection/product), taking precedence "
        "over name/type. See resolve_source_entity's sourceEntity -> type -> name fallback.",
        examples=["customers", "public.customers"],
    )
    selector: str | None = Field(
        None,
        description="Query/selector used to read from 'source' (e.g. SQL for a database client, or a "
        "MongoDB find/aggregate expression). At most one of type or selector may be combined with "
        "source.",
        examples=["SELECT id FROM public.users", "find: orders, filter: {status: completed}"],
    )
    separator: str | None = Field(
        None,
        description="Field separator for delimited file sources (default '|'); set separator=\",\" to "
        "read a comma-separated CSV.",
        examples=[",", ";", "|"],
    )
    cyclic: bool | None = Field(
        None,
        description="Wrap around and re-read the source from the start once exhausted, instead of "
        "stopping when the source is exhausted.",
        examples=[True, False],
    )
    entity: str | None = Field(
        None,
        description="Built-in domain entity to generate (e.g. Person, Company, Address, Order); "
        "validated against the entity registry. Combine with dataset/locale.",
        examples=["Person", "Company", "Address", "Order"],
    )
    script: str | None = Field(
        None,
        description="Python expression evaluated to compute the variable's value.",
        examples=["random.randint(0, 100)", "fake.name()"],
    )
    weight_column: str | None = Field(
        None,
        alias=ATTR_WEIGHT_COLUMN,
        description="Weight column in a '.wgt.ent.csv' source. Rows are sampled with replacement "
        "according to that column; this is a legacy weighted-entity source format, not a "
        "distribution='weighted' mode.",
        examples=["weight", "population"],
    )
    source_script: bool | None = Field(
        None,
        alias=ATTR_SOURCE_SCRIPTED,
        description="Evaluate 'source' as a Python script expression rather than a literal path/id "
        "(advanced; requires source).",
        examples=[True, False],
    )
    generator: str | None = Field(
        None,
        description="Predefined generator constructor used to produce the variable's value; validated "
        "against the generator registry.",
        examples=["IncrementGenerator", "DateTimeGenerator(random=True)"],
    )
    dataset: str | None = Field(
        None,
        description="Dataset (country code) for an entity/generator variable.",
        examples=["DE", "US", "BR", "BE", "FR"],
    )
    locale: str | None = Field(
        None,
        description="Locale for an entity/generator variable.",
        examples=["de_DE", "en_US", "fr_FR"],
    )
    in_date_format: str | None = Field(
        None,
        alias=ATTR_IN_DATE_FORMAT,
        description="Input date format used to parse a source/script date value before converting it "
        "to outDateFormat.",
        examples=["%Y-%m-%d", "%d-%b-%Y", "%d.%m.%Y %H:%M:%S.%f", "epoch"],
    )
    out_date_format: str | None = Field(
        None,
        alias=ATTR_OUT_DATE_FORMAT,
        description="Output date format the variable's date value is rendered in.",
        examples=["%Y-%m-%d", "%d-%b-%Y", "%d.%m.%Y %H:%M:%S.%f", "epoch"],
    )
    converter: str | None = Field(
        None,
        description="Converter(s) applied to transform the generated variable value; validated against "
        "the converter registry.",
        examples=["UpperCase", "LowerCase", "DateFormat", "Mask", "MiddleMask", "CutLength", "Append", "Hash"],
    )
    values: str | None = Field(
        None,
        description="Comma-separated list of literal values to pick from for the variable.",
        examples=["'A','B','C'", "1,2,3"],
    )
    weights: str | None = Field(
        None,
        description="Comma-separated relative weights, one per 'values' entry, for weighted random "
        "selection. Requires 'values'.",
        examples=["0.7,0.2,0.1", "5,3,2"],
    )
    unique: bool | None = Field(
        None,
        description="Emit each value at most once (distinct picks from 'values' or 'source', without "
        "replacement). Requires 'values' or 'source', cannot combine with 'weights', and only combines "
        "with the default random distribution.",
        examples=[True, False],
    )
    constant: str | None = Field(
        None,
        description="Constant, literal value for the variable (same value every record).",
        examples=["Constant Value"],
    )
    iteration_selector: str | None = Field(
        None,
        alias=ATTR_ITERATION_SELECTOR,
        description="Selector re-evaluated per iteration (instead of cached once at setup); overrides "
        "sourceEntity/type in this mode and is incompatible with 'storage' (no stable pool to index "
        "into).",
        examples=["SELECT id FROM public.users", "SELECT product_id FROM products"],
    )
    default_value: str | None = Field(
        None,
        alias=ATTR_DEFAULT_VALUE,
        description="Fallback value used when 'script' evaluates to None/fails. Requires 'script'.",
        examples=["None", "unknown"],
    )
    pattern: str | None = Field(
        None,
        description="Regular-expression pattern used to generate the variable's string value.",
        examples=["[A-Z][a-z]{5,12}", "[0-9]{5}"],
    )
    distribution: str | None = Field(
        None,
        description="Distribution/order for reading the source pool: 'random' (default, whole pool "
        "loaded into memory), 'ordered' (source order, streams page by page), or 'cumulated' "
        "(bell-shaped weighted draw; loads the whole pool).",
        examples=["random", "ordered", "cumulated"],
    )
    database: str | None = Field(
        None,
        description="Database client id when source equals 'database'.",
        examples=["db"],
    )
    variable_prefix: str | None = Field(
        None,
        alias=ATTR_VARIABLE_PREFIX,
        description="Prefix before field's name for query select data in selector element",
        examples=["${", "++", "--", "@", "{"],
    )
    variable_suffix: str | None = Field(
        None,
        alias=ATTR_VARIABLE_SUFFIX,
        description="Suffix after field's name for query select data in selector element",
        examples=["++", "--", "@", "}"],
    )
    string: str | None = Field(
        None,
        alias=ATTR_STRING,
        description="String for the variable data generation.",
        examples=["find: __var_name__, filter: status : active"],
    )
    # Storage strategy for a source-backed pool: "value" (always the pool's first row, fixed -
    # distinct from the unset default, which advances one row per generated record), "data" (the
    # whole materialized pool, same list every row), "iterator" (a position-indexed proxy).
    storage: str | None = Field(
        None,
        alias=ATTR_STORAGE,
        description="Storage strategy for a source-backed pool: 'value' (always the pool's first row, "
        "fixed - distinct from the unset default, which advances one row per generated record), 'data' "
        "(the whole materialized pool, same list every row), 'iterator' (a position-indexed proxy). "
        "Requires 'source' and is incompatible with 'iterationSelector' and a weighted-entity source.",
        examples=["value", "data", "iterator"],
    )
    # Demographic and RNG extensions for entity variables
    age_min: int | None = Field(
        None,
        alias="ageMin",
        description="Minimum age when generating entity data. Requires 'entity' or 'generator'.",
        examples=[18],
    )
    age_max: int | None = Field(
        None,
        alias="ageMax",
        description="Maximum age when generating entity data. Requires 'entity' or 'generator'.",
        examples=[90],
    )
    conditions_include: str | None = Field(
        None,
        alias="conditionsInclude",
        description="Comma-separated condition tags that must be included when generating entity data. "
        "Requires 'entity' or 'generator'.",
        examples=["diabetes,asthma"],
    )
    conditions_exclude: str | None = Field(
        None,
        alias="conditionsExclude",
        description="Comma-separated condition tags that must be excluded when generating entity data. "
        "Requires 'entity' or 'generator'.",
        examples=["pregnant"],
    )
    rng_seed: int | None = Field(
        None,
        alias=ATTR_RNG_SEED,
        description="Deterministic RNG seed for this variable.",
        examples=[12345],
    )

    @model_validator(mode="before")
    @classmethod
    def check_attribute_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={
                ATTR_NAME,
                ATTR_TYPE,
                ATTR_SOURCE,
                ATTR_SOURCE_ENTITY,
                ATTR_SELECTOR,
                ATTR_SOURCE_SCRIPTED,
                ATTR_SEPARATOR,
                ATTR_CYCLIC,
                ATTR_ENTITY,
                ATTR_SCRIPT,
                ATTR_WEIGHT_COLUMN,
                ATTR_GENERATOR,
                ATTR_DATASET,
                ATTR_LOCALE,
                ATTR_OUT_DATE_FORMAT,
                ATTR_IN_DATE_FORMAT,
                ATTR_CONVERTER,
                ATTR_CONSTANT,
                ATTR_VALUES,
                ATTR_WEIGHTS,
                ATTR_UNIQUE,
                ATTR_ITERATION_SELECTOR,
                ATTR_DEFAULT_VALUE,
                ATTR_PATTERN,
                ATTR_DISTRIBUTION,
                ATTR_DATABASE,
                ATTR_VARIABLE_PREFIX,
                ATTR_VARIABLE_SUFFIX,
                ATTR_STRING,
                ATTR_STORAGE,
                # Demographic + RNG extensions (entity/generator add-ons)
                "ageMin",
                "ageMax",
                "conditionsInclude",
                "conditionsExclude",
                ATTR_RNG_SEED,
            },
        )

    @model_validator(mode="before")
    @classmethod
    def validate_weights_require_values(cls, values: dict):
        return ModelUtil.check_weights_require_values(values)

    @model_validator(mode="before")
    @classmethod
    def validate_unique_constraints(cls, values: dict):
        return ModelUtil.check_unique_constraints(values)

    @model_validator(mode="before")
    @classmethod
    def validate_storage_constraints(cls, values: dict):
        return ModelUtil.check_storage_constraints(values)

    @model_validator(mode="before")
    @classmethod
    def validate_additional_source_attributes(cls, values: dict):
        return ModelUtil.check_valid_additional_source_attributes(values=values)

    @model_validator(mode="before")
    @classmethod
    def validate_additional_generator_entity_attributes(cls, values: dict):
        return ModelUtil.check_valid_additional_generator_entity_attributes(values=values)

    @model_validator(mode="before")
    @classmethod
    def validate_generator_mode(cls, values: dict):
        """
        Check if <variable> define only one valid generation option.

        Reads the declared facts _GENERATION_REQUIRED / _GENERATION_EXCLUSIVE;
        message construction stays here (it interpolates the clashing modes).
        """
        key_set = set(values.keys())
        generator_option = set(VARIABLE_GENERATION_REQUIRED.attrs)
        # Check if at least one of following attribute is existed to generate <variable> value
        if all(key not in key_set for key in generator_option):
            raise ValueError(f"Must defined one of following attributes {generator_option}")
        # Check if at most one generation mode is defined
        generation_mode = set(VARIABLE_GENERATION_EXCLUSIVE.attrs)
        # Check if only one generation mode is defined
        first_mode = None
        for mode in generation_mode:
            if mode in key_set:
                if first_mode is None:
                    # Set first found mode
                    first_mode = mode
                else:
                    # Raise error if finding 2 modes in same element
                    raise ValueError(
                        f"Must defined only one of following attributes {generation_mode}, "
                        f"but got: {first_mode} and {mode}"
                    )
        return values

    @model_validator(mode="before")
    @classmethod
    def validate_in_out_date_format(cls, values: dict):
        """
        Validate attribute "inDateFormat" and "outDateFormat"
        :param values:
        :return:
        """
        return ModelUtil.check_valid_in_out_date_format(values=values)

    @model_validator(mode="before")
    @classmethod
    def validate_generator_mode_of_source(cls, values: dict):
        """
        Validate at most "type" or "selector" can be defined with "source"
        :param value:
        :return:
        """
        return ModelUtil.check_generation_mode_of_source(values)

    @model_validator(mode="before")
    @classmethod
    def validate_default_value(cls, values: dict):
        """
        Validate attribute "fallback"
        :param values:
        :return:
        """
        return ModelUtil.check_valid_default_value(values)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        return ModelUtil.check_not_empty(value=value)

    @field_validator("storage")
    @classmethod
    def validate_storage(cls, value):
        # Reads the declared _STORAGE_VALUES fact; the message interpolates the
        # rejected value, so it is constructed here (options rendered in the
        # fact's declared tuple order).
        if value is not None and value not in VARIABLE_STORAGE_VALUES.values:
            options = "/".join(f"'{v}'" for v in VARIABLE_STORAGE_VALUES.values)
            raise ValueError(f"'{ATTR_STORAGE}' must be one of {options}, got '{value}'")
        return value

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, value):
        """
        Validate attribute "pattern"
        :param value:
        :return:
        """
        return ModelUtil.check_valid_pattern(value)

    @field_validator("distribution")
    @classmethod
    def validate_distribution(cls, value: str | None) -> str | None:
        if value is not None:
            ModelUtil.check_valid_data_value(value, set(resolved_values(SOURCE_DISTRIBUTION_VALUES)))
        return value
