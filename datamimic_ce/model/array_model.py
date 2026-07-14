# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_COUNT, ATTR_NAME, ATTR_SCRIPT, ATTR_TYPE
from datamimic_ce.constants.data_type_constants import (
    DATA_TYPE_BOOL,
    DATA_TYPE_FLOAT,
    DATA_TYPE_INT,
    DATA_TYPE_LITERAL,
    DATA_TYPE_STRING,
)
from datamimic_ce.model.constraints import (
    Constraint,
    ValidValues,
    constraints_schema_extra,
    resolved_values,
)
from datamimic_ce.model.model_util import ModelUtil

# Declared fact (SPOT): the type literal lives ONCE here; ALLOWED_ARRAY_TYPES is an
# alias derived from it, and the enforcing field_validator reads the alias. Message
# is dynamic (interpolates the rejected value), so the fact carries message=None.
_ARRAY_TYPE_VALUES = ValidValues(
    ATTR_TYPE,
    frozenset((
        DATA_TYPE_STRING,
        DATA_TYPE_INT,
        DATA_TYPE_BOOL,
        DATA_TYPE_FLOAT,
        DATA_TYPE_LITERAL,
    )),
)
ALLOWED_ARRAY_TYPES: frozenset[str] = resolved_values(_ARRAY_TYPE_VALUES)


class ArrayModel(BaseModel):
    # Declared cross-field constraints
    __constraints__: ClassVar[tuple[Constraint, ...]] = (
        # Same object the type field_validator reads (via the ALLOWED_ARRAY_TYPES alias)
        _ARRAY_TYPE_VALUES,
    )
    model_config = ConfigDict(json_schema_extra=constraints_schema_extra)

    name: str = Field(..., description="Name of the array; becomes the field name in the generated record.")
    type: str | None = Field(
        None,
        description="Element data type of the array. 'literal' preserves child <value constant=...> "
        "entries verbatim instead of randomly generating them (and must not be combined with count/script).",
        examples=["string", "int", "float", "bool", "literal"],
    )
    count: int | None = Field(
        None,
        description="Number of randomly generated elements in the array. Required together with type "
        "unless script is used instead; not allowed with type 'literal'.",
        examples=[1, 5, 10],
    )
    script: str | None = Field(
        None,
        description="Python expression producing the array's elements directly as a list, instead of "
        "randomly generating count elements of type. All elements must share the same data type.",
        examples=["[10, 20, 30]", "[random.randint(1, 10) for _ in range(5)]"],
    )

    @model_validator(mode="before")
    @classmethod
    def check_attribute_valid_attributes(cls, values: dict) -> dict:
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={
                ATTR_NAME,
                ATTR_TYPE,
                ATTR_COUNT,
                ATTR_SCRIPT,
            },
        )

    @model_validator(mode="before")
    @classmethod
    def check_script_mode(cls, values: dict) -> dict:
        """
        Check attribute definition
        When 'script' field is not defined then 'type' and 'count' should be defined and vice versa
        :param values:
        :return:
        """
        key_set = set(values.keys())
        if values.get(ATTR_TYPE) == DATA_TYPE_LITERAL:
            if ATTR_SCRIPT in key_set:
                raise ValueError(f"'{ATTR_SCRIPT}' must not be defined with {ATTR_TYPE} '{DATA_TYPE_LITERAL}'")
            if ATTR_COUNT in key_set:
                raise ValueError(f"'{ATTR_COUNT}' must not be defined with {ATTR_TYPE} '{DATA_TYPE_LITERAL}'")
            return values
        if ATTR_SCRIPT in key_set:
            if ATTR_COUNT in key_set or ATTR_TYPE in key_set:
                raise ValueError(f"'{ATTR_COUNT}' and '{ATTR_TYPE}' must not be defined with {ATTR_SCRIPT}")
            return values
        else:
            if ATTR_COUNT not in key_set:
                raise ValueError(
                    f"{ATTR_COUNT} and {ATTR_TYPE} are required when {ATTR_SCRIPT} not defined, "
                    f"but missing {ATTR_COUNT}"
                )
            elif ATTR_TYPE not in key_set:
                raise ValueError(
                    f"{ATTR_COUNT} and {ATTR_TYPE} are required when {ATTR_SCRIPT} not defined, but missing {ATTR_TYPE}"
                )
            return values

    @field_validator("type")
    @classmethod
    def validate_attribute_data_type(cls, value):
        """
        Validate data type of <attribute>
        :param value:
        :return:
        """
        return ModelUtil.check_valid_data_value(
            value=value,
            valid_values=ALLOWED_ARRAY_TYPES,
        )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Any) -> str:
        return ModelUtil.check_not_empty(value=value)
