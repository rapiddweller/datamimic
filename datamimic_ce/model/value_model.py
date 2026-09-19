# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Pydantic model for literal <value> entries inside <array type="literal">."""

from pydantic import BaseModel, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_CONSTANT
from datamimic_ce.model.model_util import ModelUtil


class ValueModel(BaseModel):
    constant: str

    @model_validator(mode="before")
    @classmethod
    def check_valid_attributes(cls, values: dict) -> dict:
        return ModelUtil.check_valid_attributes(values=values, valid_attributes={ATTR_CONSTANT})

    @field_validator("constant")
    @classmethod
    def validate_constant(cls, value: str) -> str:
        return ModelUtil.check_not_empty(value=value)
