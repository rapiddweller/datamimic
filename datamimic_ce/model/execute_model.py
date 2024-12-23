# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from pydantic import BaseModel, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_TARGET, ATTR_URI
from datamimic_ce.model.model_util import ModelUtil


class ExecuteModel(BaseModel):
    uri: str
    target: str | None = None

    @model_validator(mode="before")  # noqa: B023
    @classmethod
    def check_execute_valid_attributes(cls, values: dict[str, Any]) -> dict[str, Any]:
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={ATTR_URI, ATTR_TARGET},
        )

    @field_validator("uri")  # noqa: B023
    @classmethod
    def validate_uri(cls, value):
        return ModelUtil.check_not_empty(value=value)
