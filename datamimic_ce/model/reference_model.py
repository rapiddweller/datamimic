# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/


from pydantic import BaseModel, Field, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import (
    ATTR_NAME,
    ATTR_SOURCE,
    ATTR_SOURCE_KEY,
    ATTR_SOURCE_TYPE,
    ATTR_UNIQUE,
)
from datamimic_ce.model.model_util import ModelUtil


class ReferenceModel(BaseModel):
    name: str
    source: str
    source_key: str = Field(alias=ATTR_SOURCE_KEY)
    source_type: str = Field(alias=ATTR_SOURCE_TYPE)
    unique: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def check_attribute_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={
                ATTR_NAME,
                ATTR_SOURCE,
                ATTR_SOURCE_TYPE,
                ATTR_SOURCE_KEY,
                ATTR_UNIQUE,
            },
        )

    @field_validator("name", "source", "source_type", "source_key")
    @classmethod
    def validate_not_none(cls, value):
        return ModelUtil.check_not_empty(value=value)
