# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pydantic import BaseModel, Field, field_validator, model_validator

from datamimic_ce.engine.dsl.model.validation import ModelUtil
from datamimic_ce.engine.dsl.vocabulary.constants.attribute_constants import ATTR_FROM, ATTR_TO, ATTR_WEIGHT


class TransitionModel(BaseModel):
    source: str = Field(..., alias=ATTR_FROM)
    target: str = Field(..., alias=ATTR_TO)
    weight: float = Field(1.0, gt=0)

    @model_validator(mode="before")
    @classmethod
    def check_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(values=values, valid_attributes={ATTR_FROM, ATTR_TO, ATTR_WEIGHT})

    @field_validator("source", "target")
    @classmethod
    def validate_endpoint(cls, value):
        return ModelUtil.check_not_empty(value=value)
