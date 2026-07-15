"""Pydantic model for <demographics> XML node."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_DATASET, ATTR_DIR, ATTR_RNG_SEED
from datamimic_ce.model.model_util import ModelUtil


class DemographicsModel(BaseModel):
    dataset: str = Field(
        ...,
        alias=ATTR_DATASET,
        description="Demographic dataset code selecting which profile to load (e.g. a country code). "
        "Must match the 'dataset' column value inside the CSV files found in 'directory'. Once loaded, "
        "this profile is installed setup-wide and feeds age/condition sampling for entities that support "
        "it (e.g. <variable entity=\"Person\"/>), independent of that entity's own dataset= attribute.",
        examples=["DE"],
    )
    version: str = Field(
        ...,
        description="Demographic dataset version, matched against the 'version' column inside the CSV "
        "files in 'directory' (together with 'dataset' this identifies a single profile snapshot).",
        examples=["2023Q4"],
    )
    directory: str = Field(
        ...,
        alias=ATTR_DIR,
        description="Directory containing the demographic CSV files (age_pyramid.dmgrp.csv and "
        "condition_rates.dmgrp.csv are required). Relative paths are resolved against the directory of "
        "the XML descriptor, not the current working directory.",
        examples=["DE/2023Q4"],
    )
    rng_seed: int | None = Field(
        None,
        alias=ATTR_RNG_SEED,
        description="Seed for the demographic sampler's own RNG, independent of any per-<variable> "
        "rngSeed. When omitted, the sampler derives its RNG from the model-wide <setup rngSeed> instead.",
        examples=[42],
    )

    @model_validator(mode="before")
    @classmethod
    def check_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={ATTR_DATASET, "version", ATTR_DIR, ATTR_RNG_SEED},
        )
