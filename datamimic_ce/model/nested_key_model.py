# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import (
    ATTR_CONDITION,
    ATTR_CONVERTER,
    ATTR_COUNT,
    ATTR_CYCLIC,
    ATTR_DEFAULT_VALUE,
    ATTR_DISTRIBUTION,
    ATTR_MAX_COUNT,
    ATTR_MIN_COUNT,
    ATTR_NAME,
    ATTR_SCRIPT,
    ATTR_SEPARATOR,
    ATTR_SOURCE,
    ATTR_SOURCE_ENTITY,
    ATTR_SOURCE_SCRIPTED,
    ATTR_TYPE,
    ATTR_VARIABLE_PREFIX,
    ATTR_VARIABLE_SUFFIX,
)
from datamimic_ce.constants.element_constants import EL_NESTED_KEY
from datamimic_ce.model.constraints import (
    NESTED_CYCLIC_REQUIRES_COUNT,
    NESTED_CYCLIC_REQUIRES_SOURCE_OR_SCRIPT,
    NESTED_LIST_REQUIRES_COUNT,
    NESTED_SCRIPT_FORBIDDEN_ATTRS,
    NESTED_SCRIPT_FORBIDS,
    SOURCE_DISTRIBUTION_VALUES,
    Constraint,
    constraints_schema_extra,
    element_constraints,
    resolved_values,
)
from datamimic_ce.model.model_util import ModelUtil


class NestedKeyModel(BaseModel):
    __constraints__: ClassVar[tuple[Constraint, ...]] = element_constraints(EL_NESTED_KEY)
    model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

    name: str = Field(..., description="Name of the nested key; becomes the field name in the generated record.")
    type: str | None = Field(
        None,
        description="Shape of the nested key: 'dict' builds one object from child <key>s, 'list' builds "
        "a list of them (with count/minCount/maxCount). Omit type with source/script to enrich existing data.",
        examples=["dict", "list"],
    )
    source_entity: str | None = Field(
        None,
        alias=ATTR_SOURCE_ENTITY,
        description="Explicit source entity (memstore producer name) to read nested key data from, "
        "overriding the type -> name fallback used to pick which producer's rows to read.",
        examples=["orders"],
    )
    count: str | None = Field(
        None,
        description="Number of list items to generate (digits or a {script} expression). Mutually "
        "exclusive with minCount/maxCount; required in list mode unless source supplies the length.",
        examples=["1", "5", "{parent.item_count}"],
    )
    source: str | None = Field(
        None,
        description="Existing data to read/enrich instead of generating fresh nested key data: a "
        "'.csv'/'.json' file path (relative to the descriptor), or a <memstore> id.",
        examples=["data/visits.json", "mem"],
    )
    source_script: bool | None = Field(
        None,
        alias=ATTR_SOURCE_SCRIPTED,
        description="Evaluate variablePrefix/variableSuffix-delimited placeholders in the loaded "
        "source data as Python expressions before assigning it to the nested key.",
        examples=[True, False],
    )
    cyclic: bool | None = Field(
        None,
        description="Wrap around and repeat the source/count once exhausted instead of stopping. "
        "Requires both one of source/script AND one of count/minCount/maxCount to avoid an infinite loop.",
        examples=[True, False],
    )
    separator: str | None = Field(
        None,
        description="Field separator used when reading a CSV source; defaults to the descriptor-wide separator.",
        examples=[",", ";", "|"],
    )
    condition: str | None = Field(
        None,
        description="Python expression guarding whether this nested key is generated for the current "
        "record. When it evaluates false, defaultValue (if set) is used instead and nothing else runs.",
        examples=["age > 18", "parent.status == 'active'"],
    )
    script: str | None = Field(
        None,
        description="Python expression producing the nested key's value (a dict or list) directly, "
        "instead of building it from child <key>/<nestedKey> elements. Not combinable with type/source/separator.",
        examples=["{'id': uuid.uuid4().hex}", "[x for x in range(3)]"],
    )
    min_count: int | None = Field(
        None,
        alias=ATTR_MIN_COUNT,
        description="Lower bound of a randomly chosen list length, used instead of a fixed count.",
        examples=[1],
    )
    max_count: int | None = Field(
        None,
        alias=ATTR_MAX_COUNT,
        description="Upper bound of a randomly chosen list length, used instead of a fixed count.",
        examples=[5],
    )
    default_value: str | None = Field(
        None,
        alias=ATTR_DEFAULT_VALUE,
        description="Fallback Python expression evaluated and assigned when condition is false, or "
        "when evaluating script fails while iterating an existing source.",
        examples=["None", "{}"],
    )
    distribution: str | None = Field(
        None,
        description="Ordering strategy applied when loading nested key data from a source: "
        "'random' (default), 'ordered' (source order), or 'cumulated' (bell-shaped).",
        examples=["ordered", "random"],
    )
    converter: str | None = Field(
        None,
        description="Converter(s) applied to the generated/loaded nested key value before it is "
        "assigned to the current record.",
        examples=["RemoveNoneOrEmptyElement"],
    )
    variable_prefix: str | None = Field(
        None,
        alias=ATTR_VARIABLE_PREFIX,
        description="Placeholder prefix recognized when sourceScripted evaluates templated fields "
        "inside this nested key's scope; defaults to the descriptor-wide defaultVariablePrefix ('__').",
        examples=["__"],
    )
    variable_suffix: str | None = Field(
        None,
        alias=ATTR_VARIABLE_SUFFIX,
        description="Placeholder suffix recognized when sourceScripted evaluates templated fields "
        "inside this nested key's scope; defaults to the descriptor-wide defaultVariableSuffix ('__').",
        examples=["__"],
    )

    @model_validator(mode="before")
    @classmethod
    def check_attribute_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={
                ATTR_NAME,
                ATTR_TYPE,
                ATTR_COUNT,
                ATTR_SOURCE,
                ATTR_SOURCE_ENTITY,
                ATTR_SOURCE_SCRIPTED,
                ATTR_CYCLIC,
                ATTR_SEPARATOR,
                ATTR_SCRIPT,
                ATTR_MIN_COUNT,
                ATTR_MAX_COUNT,
                ATTR_CONDITION,
                ATTR_DEFAULT_VALUE,
                ATTR_DISTRIBUTION,
                ATTR_CONVERTER,
                ATTR_VARIABLE_PREFIX,
                ATTR_VARIABLE_SUFFIX,
            },
        )

    @model_validator(mode="before")
    @classmethod
    def validate_additional_source_attributes(cls, values: dict):
        # in nestedKey, allow cyclic without source, because it can combine with script
        return ModelUtil.check_valid_additional_source_attributes_without_cyclic(values=values)

    @model_validator(mode="before")
    @classmethod
    def validate_cyclic_exit(cls, values: dict):
        # cyclic can combine with source and script; enforce the declared fact
        # (presence-based Requires with a static message).
        return ModelUtil.check_constraints(values, (NESTED_CYCLIC_REQUIRES_SOURCE_OR_SCRIPT,))

    @model_validator(mode="before")
    @classmethod
    def validate_min_max_count(cls, values: dict):
        return ModelUtil.check_min_max_count(values, EL_NESTED_KEY)

    @model_validator(mode="before")
    @classmethod
    def validate_count_with_data_type(cls, values: dict):
        return ModelUtil.check_constraints(
            values,
            (NESTED_CYCLIC_REQUIRES_COUNT, NESTED_LIST_REQUIRES_COUNT),
        )

    @model_validator(mode="before")
    @classmethod
    def validate_script_exist(cls, values: dict):
        # Enforces the central NESTED_SCRIPT_FORBIDS fact; iterates its ordered
        # source tuple because the
        # dynamic message reports the FIRST offending attribute in that order.
        key_set = set(values.keys())
        if NESTED_SCRIPT_FORBIDS.attr in key_set:
            for key in NESTED_SCRIPT_FORBIDDEN_ATTRS:
                if key in key_set:
                    raise ValueError(
                        f"When 'script' is defined in <nestedKey>, "
                        f"not allow to define {NESTED_SCRIPT_FORBIDDEN_ATTRS}, but get invalid attribute '{key}'"
                    )
        return values

    @model_validator(mode="before")
    @classmethod
    def validate_generator_mode_of_source(cls, values: dict):
        """
        Validate at most "type" or "selector" can be defined with "source"
        :param value:
        :return:
        """
        return ModelUtil.check_generation_mode_of_source(values)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        return ModelUtil.check_not_empty(value=value)

    @field_validator("source_entity")
    @classmethod
    def _entity_not_blank(cls, value: str | None) -> str | None:
        """A physical entity name must be meaningful: strip it, and reject blank (a real user error -
        an empty sourceEntity means the user forgot the value, not "use the default")."""
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("sourceEntity must not be blank")
        # sourceEntity is a single table/collection name for a memstore read, never a path.
        if "/" in stripped or "\\" in stripped or ".." in stripped:
            raise ValueError(f"sourceEntity must be a plain entity name, not a path: '{stripped}'")
        return stripped

    @field_validator("distribution")
    @classmethod
    def validate_distribution(cls, value: str | None) -> str | None:
        if value is not None:
            ModelUtil.check_valid_data_value(value, resolved_values(SOURCE_DISTRIBUTION_VALUES))
        return value
