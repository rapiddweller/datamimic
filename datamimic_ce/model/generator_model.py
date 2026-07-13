# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, Field, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_GENERATOR, ATTR_NAME
from datamimic_ce.model.model_util import ModelUtil


class GeneratorModel(BaseModel):
    name: str = Field(
        ...,
        description="Id this generator instance is registered under, so <key>/<variable> "
        "elements elsewhere can reuse it via their own generator= attribute.",
        examples=["id_generator"],
    )
    generator: str = Field(
        ...,
        description="Generator constructor expression to instantiate and register under 'name'.",
        examples=["IncrementGenerator(start=1)"],
    )

    @model_validator(mode="before")
    @classmethod
    def check_execute_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={ATTR_NAME, ATTR_GENERATOR},
        )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        return ModelUtil.check_not_empty(value=value)

    @field_validator("generator")
    @classmethod
    def validate_generator(cls, value):
        return ModelUtil.check_not_empty(value=value)
