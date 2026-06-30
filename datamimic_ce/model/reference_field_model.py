# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, Field, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_SOURCE_KEY, ATTR_TARGET
from datamimic_ce.model.model_util import ModelUtil


class ReferenceFieldModel(BaseModel):
    """A <field> child of a composite <reference>: maps a source column to a target field."""

    target: str = Field(alias=ATTR_TARGET)
    source_key: str = Field(alias=ATTR_SOURCE_KEY)

    @model_validator(mode="before")
    @classmethod
    def check_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(values=values, valid_attributes={ATTR_TARGET, ATTR_SOURCE_KEY})

    @field_validator("target", "source_key")
    @classmethod
    def validate_not_empty(cls, value):
        return ModelUtil.check_not_empty(value=value)
