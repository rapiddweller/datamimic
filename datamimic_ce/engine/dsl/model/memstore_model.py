# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, Field, field_validator, model_validator

from datamimic_ce.engine.dsl.constants.attribute_constants import ATTR_ID
from datamimic_ce.engine.dsl.model.model_util import ModelUtil


class MemstoreModel(BaseModel):
    id: str = Field(
        ...,
        description="Identifier for this in-memory store, used as a <generate target=> write "
        "destination and a <variable source=> read source for pipeline handoff within the same run.",
        examples=["mem"],
    )

    @model_validator(mode="before")
    @classmethod
    def check_execute_valid_attributes(cls, values: object) -> object:
        if not isinstance(values, dict):
            raise TypeError("<memstore> attributes must be a mapping")
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={ATTR_ID},
        )

    @field_validator(ATTR_ID)
    @classmethod
    def validate_id(cls, value):
        return ModelUtil.check_not_empty(value=value)
