# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, Field, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import (
    ATTR_CONDITION,
    ATTR_CONSTANT,
    ATTR_CONVERTER,
    ATTR_DATABASE,
    ATTR_DEFAULT_VALUE,
    ATTR_GENERATOR,
    ATTR_IN_DATE_FORMAT,
    ATTR_NAME,
    ATTR_NULL_QUOTA,
    ATTR_OUT_DATE_FORMAT,
    ATTR_PATTERN,
    ATTR_SCRIPT,
    ATTR_SELECTOR,
    ATTR_SEPARATOR,
    ATTR_SOURCE,
    ATTR_STRING,
    ATTR_TYPE,
    ATTR_VALUES,
    ATTR_VARIABLE_PREFIX,
    ATTR_VARIABLE_SUFFIX,
)
from datamimic_ce.constants.data_type_constants import DATA_TYPE_BOOL, DATA_TYPE_FLOAT, DATA_TYPE_INT, DATA_TYPE_STRING
from datamimic_ce.model.model_util import ModelUtil


class KeyModel(BaseModel):
    name: str
    type: str | None = None
    source: str | None = None
    selector: str | None = None
    separator: str | None = None
    values: str | None = None
    script: str | None = None
    generator: str | None = None
    constant: str | None = None
    condition: str | None = None
    converter: str | None = None
    pattern: str | None = None
    in_date_format: str | None = Field(None, alias=ATTR_IN_DATE_FORMAT)
    out_date_format: str | None = Field(None, alias=ATTR_OUT_DATE_FORMAT)
    default_value: str | None = Field(None, alias=ATTR_DEFAULT_VALUE)
    null_quota: float | None = Field(None, alias=ATTR_NULL_QUOTA)
    database: str | None = None
    string: str | None = Field(None, alias=ATTR_STRING)
    variable_prefix: str | None = Field(None, alias=ATTR_VARIABLE_PREFIX)
    variable_suffix: str | None = Field(None, alias=ATTR_VARIABLE_SUFFIX)

    @model_validator(mode="before")
    @classmethod
    def check_attribute_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={
                ATTR_NAME,
                ATTR_TYPE,
                ATTR_SOURCE,
                ATTR_SELECTOR,
                ATTR_SEPARATOR,
                ATTR_VALUES,
                ATTR_SCRIPT,
                ATTR_GENERATOR,
                ATTR_CONSTANT,
                ATTR_CONDITION,
                ATTR_CONVERTER,
                ATTR_PATTERN,
                ATTR_IN_DATE_FORMAT,
                ATTR_OUT_DATE_FORMAT,
                ATTR_DEFAULT_VALUE,
                ATTR_NULL_QUOTA,
                ATTR_DATABASE,
                ATTR_STRING,
                ATTR_VARIABLE_PREFIX,
                ATTR_VARIABLE_SUFFIX,
            },
        )

    @model_validator(mode="before")
    @classmethod
    def validate_additional_source_attributes(cls, values: dict):
        return ModelUtil.check_valid_additional_source_attributes(values=values)

    @model_validator(mode="before")
    @classmethod
    def validate_generator_mode(cls, values: dict):
        """
        Check if <key> define only one valid generation option
        :param values:
        :return:
        """
        key_set = set(values.keys())
        generator_option = {
            ATTR_TYPE,
            ATTR_SOURCE,
            ATTR_VALUES,
            ATTR_SCRIPT,
            ATTR_GENERATOR,
            ATTR_CONSTANT,
            ATTR_PATTERN,
            ATTR_STRING,
        }
        # Check if at least one of following attribute is existed to generate <key> value
        if all(key not in key_set for key in generator_option):
            raise ValueError(f"Must defined one of following attributes {generator_option}")
        # Check if at most one generation mode is defined
        generation_mode = {
            ATTR_SOURCE,
            ATTR_VALUES,
            ATTR_SCRIPT,
            ATTR_GENERATOR,
            ATTR_CONSTANT,
            ATTR_PATTERN,
        }
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
                        f"but got: {first_mode} & {mode}"
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
    def validate_default_value(cls, values: dict):
        """
        Validate attribute "fallback"
        :param values:
        :return:
        """
        return ModelUtil.check_valid_default_value(values)

    @field_validator("type")
    @classmethod
    def validate_data_type(cls, value):
        """
        Validate attribute "type"
        :param value:
        :return:
        """
        return ModelUtil.check_valid_data_value(
            value=value,
            valid_values={
                DATA_TYPE_STRING,
                DATA_TYPE_INT,
                DATA_TYPE_FLOAT,
                DATA_TYPE_BOOL,
            },
        )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        return ModelUtil.check_not_empty(value=value)

    @field_validator("null_quota")
    @classmethod
    def validate_null_quota(cls, value):
        if value > 1 or value < 0:
            raise ValueError(f"must be in range [0, 1], but get invalid value: {value}")
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
