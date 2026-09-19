# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pydantic import BaseModel, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_CONDITION, ATTR_MESSAGE
from datamimic_ce.model.model_util import ModelUtil


class AssertModel(BaseModel):
    condition: str
    message: str | None = None

    @model_validator(mode="before")
    @classmethod
    def check_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={ATTR_CONDITION, ATTR_MESSAGE},
        )

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, value):
        return ModelUtil.check_not_empty(value=value)
