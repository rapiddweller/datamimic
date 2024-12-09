# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/


from pydantic import BaseModel, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_TARGET, ATTR_URI
from datamimic_ce.model.model_util import ModelUtil


class ExecuteModel(BaseModel):
    uri: str
    target: str | None = None

    @model_validator(mode="before")
    @classmethod
    def check_execute_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={ATTR_URI, ATTR_TARGET},
        )

    @field_validator("uri")
    @classmethod
    def validate_uri(cls, value):
        return ModelUtil.check_not_empty(value=value)
