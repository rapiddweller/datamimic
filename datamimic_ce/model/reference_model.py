# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


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
    # Optional legacy single-field shortcut; composite references use <field> children instead.
    source_key: str | None = Field(default=None, alias=ATTR_SOURCE_KEY)
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

    @field_validator("name", "source", "source_type")
    @classmethod
    def validate_not_none(cls, value):
        return ModelUtil.check_not_empty(value=value)
