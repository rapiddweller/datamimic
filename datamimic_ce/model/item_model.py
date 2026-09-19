# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, Field, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_CONDITION
from datamimic_ce.model.model_util import ModelUtil


class ItemModel(BaseModel):
    condition: str | None = Field(
        None,
        description="Python expression guarding whether this <item> (a single fixed-shape entry of a "
        "<list>) is populated; when false, its keys are not generated and the list gets None in that "
        "position instead (the item is not removed from the list).",
        examples=["patient_id % 2 == 0"],
    )

    @model_validator(mode="before")
    @classmethod
    def check_execute_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={ATTR_CONDITION},
        )
