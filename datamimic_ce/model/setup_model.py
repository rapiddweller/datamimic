# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, Field, model_validator

from datamimic_ce.constants.attribute_constants import (
    ATTR_DEFAULT_DATASET,
    ATTR_DEFAULT_LINE_SEPARATOR,
    ATTR_DEFAULT_LOCALE,
    ATTR_DEFAULT_SEPARATOR,
    ATTR_DEFAULT_SOURCE_SCRIPTED,
    ATTR_DEFAULT_VARIABLE_PREFIX,
    ATTR_DEFAULT_VARIABLE_SUFFIX,
    ATTR_MULTIPROCESSING,
    ATTR_NUM_PROCESS,
    ATTR_REPORT_LOGGING,
    ATTR_RNG_SEED,
)
from datamimic_ce.model.model_util import ModelUtil


class SetupModel(BaseModel):
    multiprocessing: bool | None = Field(
        None,
        description="Run top-level <generate> statements across worker processes instead of a single process.",
        examples=[True],
    )
    default_separator: str | None = Field(
        None,
        alias=ATTR_DEFAULT_SEPARATOR,
        description="Default field separator for delimited (e.g. CSV) sources/exports when a "
        "statement doesn't set its own separator=.",
        examples=[",", ";", "|"],
    )
    default_dataset: str | None = Field(
        None,
        alias=ATTR_DEFAULT_DATASET,
        description="Default dataset (country/locale-specific data pool) used when a statement "
        "doesn't set its own dataset=.",
        examples=["US", "DE"],
    )
    default_locale: str | None = Field(
        None,
        alias=ATTR_DEFAULT_LOCALE,
        description="Default locale used when a statement doesn't set its own locale=.",
        examples=["en", "de"],
    )
    num_process: int | None = Field(
        None,
        alias=ATTR_NUM_PROCESS,
        description="Number of worker processes to use when multiprocessing is enabled.",
        examples=[4],
    )
    default_line_separator: str | None = Field(
        None,
        alias=ATTR_DEFAULT_LINE_SEPARATOR,
        description="Default line separator for generated text output.",
        examples=["\n", "\r\n"],
    )
    default_source_scripted: bool | None = Field(
        None,
        alias=ATTR_DEFAULT_SOURCE_SCRIPTED,
        description="Default for sourceScripted when a statement's source doesn't set its own — "
        "whether source rows are treated as containing script expressions to evaluate.",
        examples=[True],
    )
    report_logging: bool | None = Field(
        None,
        alias=ATTR_REPORT_LOGGING,
        description="Enable or disable the generation report/log output for the run.",
        examples=[True, False],
    )
    default_variable_prefix: str | None = Field(
        None,
        alias=ATTR_DEFAULT_VARIABLE_PREFIX,
        description="Default prefix marking a variable reference for string interpolation (e.g. in "
        "string=/pattern=) when a statement doesn't set its own.",
        examples=["__"],
    )
    default_variable_suffix: str | None = Field(
        None,
        alias=ATTR_DEFAULT_VARIABLE_SUFFIX,
        description="Default suffix marking a variable reference for string interpolation (e.g. in "
        "string=/pattern=) when a statement doesn't set its own.",
        examples=["__"],
    )
    rng_seed: int | None = Field(
        None,
        alias=ATTR_RNG_SEED,
        description="Seed for the deterministic random number generator, making the whole run "
        "reproducible. Omitting it means every run differs.",
        examples=[1, 12345],
    )

    @model_validator(mode="before")
    @classmethod
    def check_execute_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={
                ATTR_MULTIPROCESSING,
                ATTR_DEFAULT_SEPARATOR,
                ATTR_DEFAULT_DATASET,
                ATTR_DEFAULT_LOCALE,
                ATTR_NUM_PROCESS,
                ATTR_DEFAULT_LINE_SEPARATOR,
                ATTR_DEFAULT_SOURCE_SCRIPTED,
                ATTR_DEFAULT_VARIABLE_PREFIX,
                ATTR_DEFAULT_VARIABLE_SUFFIX,
                ATTR_REPORT_LOGGING,
                ATTR_RNG_SEED,
            },
        )
