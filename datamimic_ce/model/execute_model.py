# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from pydantic import BaseModel, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_TARGET, ATTR_TYPE, ATTR_URI
from datamimic_ce.model.model_util import ModelUtil

# Inline/uri execution languages DATAMIMIC supports.
VALID_EXECUTE_TYPES = {"python", "bash", "sql"}


class ExecuteModel(BaseModel):
    # uri (a script file) XOR inline element text; enforced by the parser, which also resolves `type`.
    uri: str | None = None
    target: str | None = None
    type: str | None = None

    @model_validator(mode="before")  # noqa: B023
    @classmethod
    def check_execute_valid_attributes(cls, values: dict[str, Any]) -> dict[str, Any]:
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={ATTR_URI, ATTR_TARGET, ATTR_TYPE},
        )

    @field_validator("type")  # noqa: B023
    @classmethod
    def validate_type(cls, value):
        if value is not None and value not in VALID_EXECUTE_TYPES:
            raise ValueError(f"'{ATTR_TYPE}' of <execute> must be one of {sorted(VALID_EXECUTE_TYPES)}, got '{value}'")
        return value
