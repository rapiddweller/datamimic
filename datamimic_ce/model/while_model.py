# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pydantic import BaseModel, Field, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_CONDITION, ATTR_MAX_ITERATIONS
from datamimic_ce.model.model_util import ModelUtil


class WhileModel(BaseModel):
    condition: str
    # Mandatory infinite-loop backstop: the loop RAISES when it exceeds this (never silently stops).
    max_iterations: int = Field(default=10000, alias=ATTR_MAX_ITERATIONS)

    @model_validator(mode="before")
    @classmethod
    def check_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={ATTR_CONDITION, ATTR_MAX_ITERATIONS},
        )

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, value):
        return ModelUtil.check_not_empty(value=value)
