# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from pydantic import BaseModel, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_COUNT, ATTR_NAME, ATTR_SCRIPT, ATTR_TYPE
from datamimic_ce.constants.data_type_constants import DATA_TYPE_BOOL, DATA_TYPE_FLOAT, DATA_TYPE_INT, DATA_TYPE_STRING
from datamimic_ce.model.model_util import ModelUtil


class ArrayModel(BaseModel):
    name: str
    type: str | None = None
    count: int | None = None
    script: str | None = None

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
                    f"{ATTR_COUNT} and {ATTR_TYPE} are required when {ATTR_SCRIPT} not defined, "
                    f"but missing {ATTR_TYPE}"
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
            valid_values={
                DATA_TYPE_STRING,
                DATA_TYPE_INT,
                DATA_TYPE_BOOL,
                DATA_TYPE_FLOAT,
            },
        )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Any) -> str:
        return ModelUtil.check_not_empty(value=value)
