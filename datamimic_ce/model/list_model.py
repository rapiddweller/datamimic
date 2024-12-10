# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_CONVERTER, ATTR_NAME
from datamimic_ce.model.model_util import ModelUtil


class ListModel(BaseModel):
    name: str
    converter: str | None = None

    @model_validator(mode="before")
    @classmethod
    def check_execute_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={ATTR_NAME, ATTR_CONVERTER},
        )

    @field_validator(ATTR_NAME)
    @classmethod
    def validate_name(cls, value):
        return ModelUtil.check_not_empty(value=value)
