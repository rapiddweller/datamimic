# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, Field, field_validator, model_validator

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
    ATTR_SOURCE_SCRIPTED,
    ATTR_TYPE,
    ATTR_VARIABLE_PREFIX,
    ATTR_VARIABLE_SUFFIX,
)
from datamimic_ce.constants.data_type_constants import DATA_TYPE_LIST
from datamimic_ce.model.model_util import ModelUtil


class NestedKeyModel(BaseModel):
    name: str
    type: str | None = None
    count: str | None = None
    source: str | None = None
    source_script: bool | None = Field(None, alias=ATTR_SOURCE_SCRIPTED)
    cyclic: bool | None = None
    separator: str | None = None
    condition: str | None = None
    script: str | None = None
    min_count: int | None = Field(None, alias=ATTR_MIN_COUNT)
    max_count: int | None = Field(None, alias=ATTR_MAX_COUNT)
    default_value: str | None = Field(None, alias=ATTR_DEFAULT_VALUE)
    distribution: str | None = None
    converter: str | None = None
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
                ATTR_COUNT,
                ATTR_SOURCE,
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
        # cyclic can combine with source and script
        key_set = set(values.keys())
        main_attributes = tuple([ATTR_SOURCE, ATTR_SCRIPT])
        if ATTR_CYCLIC in key_set and not any(attr in key_set for attr in main_attributes):
            raise ValueError(f"'{ATTR_CYCLIC}' is only allowed when one of {main_attributes} is defined")
        return values

    @model_validator(mode="before")
    @classmethod
    def validate_min_max_count(cls, values: dict):
        key_set = set(values.keys())
        if ATTR_COUNT in key_set:
            # Not allow minCount or maxCount is defined with count
            if ATTR_MIN_COUNT in key_set or ATTR_MAX_COUNT in key_set:
                raise ValueError(
                    f"'{ATTR_MIN_COUNT}' and '{ATTR_MAX_COUNT}' must not be defined "
                    f"when '{ATTR_COUNT}' exists in <nestedKey>"
                )
        else:
            if (
                ATTR_MIN_COUNT in key_set
                and ATTR_MAX_COUNT in key_set
                and (values[ATTR_MIN_COUNT] > values[ATTR_MAX_COUNT])
            ):
                raise ValueError(
                    f"'{ATTR_MIN_COUNT}' value ({values[ATTR_MIN_COUNT]}) "
                    f"must be less than or equal to '{ATTR_MAX_COUNT}' value ({values[ATTR_MAX_COUNT]})"
                )
        return values

    @model_validator(mode="before")
    @classmethod
    def validate_count_with_data_type(cls, values: dict):
        key_set = set(values.keys())
        part_type = values.get(ATTR_TYPE)
        count_defined = any(ele in key_set for ele in (ATTR_COUNT, ATTR_MAX_COUNT, ATTR_MIN_COUNT))
        # Make sure 'cyclic' can only be defined with 'count' to avoid infinity loop
        if not count_defined and ATTR_CYCLIC in key_set:
            raise ValueError(
                f"'{ATTR_CYCLIC}' is only allowed when '{ATTR_COUNT}', '{ATTR_MIN_COUNT}' "
                f"or '{ATTR_MAX_COUNT}' is defined"
            )
        # Make sure 'count' is defined in part list generation mode
        if not count_defined and part_type == DATA_TYPE_LIST and ATTR_SOURCE not in key_set:
            raise ValueError(
                f"'{ATTR_COUNT}', '{ATTR_MIN_COUNT}' or '{ATTR_MAX_COUNT}' "
                f"must be defined in part having {ATTR_TYPE} '{part_type}' without '{ATTR_SOURCE}'"
            )
        return values

    @model_validator(mode="before")
    @classmethod
    def validate_script_exist(cls, values: dict):
        key_set = set(values.keys())
        invalid_attributes = (
            ATTR_TYPE,
            ATTR_SOURCE,
            ATTR_SOURCE_SCRIPTED,
            ATTR_SEPARATOR,
        )
        # Not allow invalid_attributes being defined in part when 'script' exist
        if ATTR_SCRIPT in key_set:
            for key in invalid_attributes:
                if key in key_set:
                    raise ValueError(
                        f"When 'script' is defined in <nestedKey>, "
                        f"not allow to define {invalid_attributes}, but get invalid attribute '{key}'"
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
