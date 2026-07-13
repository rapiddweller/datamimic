# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, Field, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import (
    ATTR_CYCLIC,
    ATTR_DISTRIBUTION,
    ATTR_NAME,
    ATTR_SOURCE,
    ATTR_SOURCE_KEY,
    ATTR_SOURCE_TYPE,
    ATTR_UNIQUE,
)
from datamimic_ce.enums.distribution_enums import SourceDistribution
from datamimic_ce.model.model_util import ModelUtil


class ReferenceModel(BaseModel):
    name: str = Field(
        ...,
        description="Field name in the generated record that receives the reference value. Also "
        "used as the legacy target when no <field> children are present.",
        examples=["customer_id"],
    )
    source: str = Field(
        ...,
        description="Id of the <database>/<mongodb> client to pull the reference from.",
        examples=["db", "mongo"],
    )
    # Optional legacy single-field shortcut; composite references use <field> children instead.
    source_key: str | None = Field(
        default=None,
        alias=ATTR_SOURCE_KEY,
        description="Legacy single-field shortcut: source column to read, mapped onto 'name'. "
        "Mutually exclusive with <field> children — use those for composite (multi-column) "
        "references.",
        examples=["id"],
    )
    source_type: str = Field(
        alias=ATTR_SOURCE_TYPE,
        description="Source table/collection to select reference rows from.",
        examples=["customer"],
    )
    unique: bool | None = Field(
        None,
        description="Draw distinct rows without replacement instead of the default "
        "with-replacement sampling (a foreign key may otherwise repeat the same row). Only "
        "combines with distribution='random' (the default) and is incompatible with cyclic.",
        examples=[True],
    )
    # Row-selection shape, same vocabulary as <variable>/<generate>: random (default, with
    # replacement), ordered (source order, strict unless cyclic), cumulated (bell). cyclic wraps.
    distribution: str | None = Field(
        None,
        description="Row-selection shape, same vocabulary as <variable>/<generate>: random "
        "(default, with replacement), ordered (source order, strict unless cyclic), cumulated "
        "(bell).",
        examples=["random", "ordered", "cumulated"],
    )
    cyclic: bool | None = Field(
        None,
        description="Wrap ordered selection back to the start once the source is exhausted, "
        "instead of stopping.",
        examples=[True],
    )

    @model_validator(mode="before")
    @classmethod
    def check_attribute_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={
                ATTR_NAME,
                ATTR_SOURCE,
                ATTR_SOURCE_TYPE,
                ATTR_SOURCE_KEY,
                ATTR_UNIQUE,
                ATTR_DISTRIBUTION,
                ATTR_CYCLIC,
            },
        )

    @model_validator(mode="before")
    @classmethod
    def check_unique_constraints(cls, values: dict):
        # unique implies distinct random order: incompatible with cyclic/ordered/cumulated.
        return ModelUtil.check_unique_constraints(values=values)

    @field_validator("distribution")
    @classmethod
    def validate_distribution(cls, value):
        if value is not None:
            SourceDistribution.coerce(value)  # unknown value -> ValueError at parse time
        return value

    @field_validator("name", "source", "source_type")
    @classmethod
    def validate_not_none(cls, value):
        return ModelUtil.check_not_empty(value=value)
