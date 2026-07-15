# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, Field, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_ID, ATTR_START
from datamimic_ce.model.model_util import ModelUtil


class StateMachineModel(BaseModel):
    id: str = Field(
        ...,
        description="Unique name under which this weighted state-machine definition (this element plus "
        'its <transition> children) is registered. Referenced later via generator="<id>" on a <key>/'
        "<variable> to walk the machine; each reference builds its own independent, stateful walk.",
        examples=["orderLifecycle"],
    )
    start: str | None = Field(
        None,
        description="Starting state of the walk. When omitted, defaults to the 'from' state of the "
        "first <transition> child (in document order).",
        examples=["open"],
    )

    @model_validator(mode="before")
    @classmethod
    def check_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(values=values, valid_attributes={ATTR_ID, ATTR_START})

    @field_validator("id")
    @classmethod
    def validate_id(cls, value):
        return ModelUtil.check_not_empty(value=value)
