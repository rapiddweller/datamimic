# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, Field, field_validator, model_validator

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
    ATTR_SCRIPT,
    ATTR_SELECTOR,
    ATTR_SEPARATOR,
    ATTR_SOURCE,
    ATTR_SOURCE_SCRIPTED,
    ATTR_STRING,
    ATTR_TYPE,
    ATTR_VALUES,
    ATTR_VARIABLE_PREFIX,
    ATTR_VARIABLE_SUFFIX,
    ATTR_WEIGHT_COLUMN,
)
from datamimic_ce.model.model_util import ModelUtil


class VariableModel(BaseModel):
    name: str
    type: str | None = None
    source: str | None = None
    selector: str | None = None
    separator: str | None = None
    cyclic: bool | None = None
    entity: str | None = None
    script: str | None = None
    weight_column: str | None = Field(None, alias=ATTR_WEIGHT_COLUMN)
    source_script: bool | None = Field(None, alias=ATTR_SOURCE_SCRIPTED)
    generator: str | None = None
    dataset: str | None = None
    locale: str | None = None
    in_date_format: str | None = Field(None, alias=ATTR_IN_DATE_FORMAT)
    out_date_format: str | None = Field(None, alias=ATTR_OUT_DATE_FORMAT)
    converter: str | None = None
    values: str | None = None
    constant: str | None = None
    iteration_selector: str | None = Field(None, alias=ATTR_ITERATION_SELECTOR)
    default_value: str | None = Field(None, alias=ATTR_DEFAULT_VALUE)
    pattern: str | None = None
    distribution: str | None = None
    database: str | None = None
    variable_prefix: str | None = Field(None, alias=ATTR_VARIABLE_PREFIX)
    variable_suffix: str | None = Field(None, alias=ATTR_VARIABLE_SUFFIX)
    string: str | None = Field(None, alias=ATTR_STRING)

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
                ATTR_ITERATION_SELECTOR,
                ATTR_DEFAULT_VALUE,
                ATTR_PATTERN,
                ATTR_DISTRIBUTION,
                ATTR_DATABASE,
                ATTR_VARIABLE_PREFIX,
                ATTR_VARIABLE_SUFFIX,
                ATTR_STRING,
            },
        )

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
        Check if <variable> define only one valid generation option
        :param values:
        :return:
        """
        key_set = set(values.keys())
        generator_option = {
            ATTR_SOURCE,
            ATTR_ENTITY,
            ATTR_SCRIPT,
            ATTR_GENERATOR,
            ATTR_VALUES,
            ATTR_CONSTANT,
            ATTR_TYPE,
            ATTR_PATTERN,
            ATTR_STRING,
        }
        # Check if at least one of following attribute is existed to generate <variable> value
        if all(key not in key_set for key in generator_option):
            raise ValueError(f"Must defined one of following attributes {generator_option}")
        # Check if at most one generation mode is defined
        generation_mode = {
            ATTR_SOURCE,
            ATTR_ENTITY,
            ATTR_SCRIPT,
            ATTR_GENERATOR,
            ATTR_VALUES,
            ATTR_CONSTANT,
            ATTR_PATTERN,
            ATTR_STRING,
        }
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
    def validate_distribution(cls, value):
        """
        Validate attribute "distribution"
        """
        return ModelUtil.check_valid_distribution(value)
