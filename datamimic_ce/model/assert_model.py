# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pydantic import BaseModel, Field, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_CONDITION, ATTR_MESSAGE
from datamimic_ce.model.model_util import ModelUtil


class AssertModel(BaseModel):
    condition: str = Field(
        ...,
        description="Boolean expression the record (or setup context) must satisfy; the run fails when it is not true.",
        examples=["18 <= age <= 65", "total > 0", "status in ('open', 'closed')"],
    )
    message: str | None = Field(
        None,
        description="Optional explanation surfaced when the assertion fails.",
        examples=["age out of the working range", "amount must be positive"],
    )

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
