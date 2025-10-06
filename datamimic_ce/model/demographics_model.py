"""Pydantic model for <demographics> XML node."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_DATASET, ATTR_DIR
from datamimic_ce.model.model_util import ModelUtil


class DemographicsModel(BaseModel):
    dataset: str = Field(..., alias=ATTR_DATASET)
    version: str
    directory: str = Field(..., alias=ATTR_DIR)
    rng_seed: int | None = Field(None, alias="rngSeed")

    @model_validator(mode="before")
    @classmethod
    def check_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={ATTR_DATASET, "version", ATTR_DIR, "rngSeed"},
        )
