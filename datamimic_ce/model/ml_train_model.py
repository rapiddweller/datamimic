# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from pydantic import BaseModel, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import (
    ATTR_MAXTRAININGTIME,
    ATTR_MODE,
    ATTR_NAME,
    ATTR_SEPARATOR,
    ATTR_SOURCE,
    ATTR_TYPE,
)
from datamimic_ce.model.model_util import ModelUtil


class MLTrainModel(BaseModel):
    name: str
    source: str
    type: str | None = None
    mode: str | None = None
    maxTrainingTime: str | None = None
    separator: str | None = None

    @model_validator(mode="before")
    @classmethod
    def check_generate_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={
                ATTR_NAME,
                ATTR_SOURCE,
                ATTR_TYPE,
                ATTR_MODE,
                ATTR_MAXTRAININGTIME,
                ATTR_SEPARATOR,
            },
        )

    @model_validator(mode="before")
    @classmethod
    def validate_additional_source_attributes(cls, values: dict):
        return ModelUtil.check_valid_additional_source_attributes(values=values)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        return ModelUtil.check_not_empty(value=value)
