# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from pydantic import BaseModel, Field, field_validator

from datamimic_ce.constants.attribute_constants import ATTR_IF, ATTR_THEN
from datamimic_ce.model.model_util import ModelUtil


class RuleModel(BaseModel):
    if_rule: str = Field(alias=ATTR_IF)
    then_rule: str = Field(alias=ATTR_THEN)

    @field_validator("if_rule", "then_rule")
    @classmethod
    def validate_name(cls, value):
        return ModelUtil.check_not_empty(value=value)
