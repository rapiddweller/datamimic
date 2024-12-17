# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
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
)
from datamimic_ce.model.model_util import ModelUtil


class SetupModel(BaseModel):
    multiprocessing: bool | None = None
    default_separator: str | None = Field(None, alias=ATTR_DEFAULT_SEPARATOR)
    default_dataset: str | None = Field(None, alias=ATTR_DEFAULT_DATASET)
    default_locale: str | None = Field(None, alias=ATTR_DEFAULT_LOCALE)
    num_process: int | None = Field(None, alias=ATTR_NUM_PROCESS)
    default_line_separator: str | None = Field(None, alias=ATTR_DEFAULT_LINE_SEPARATOR)
    default_source_scripted: bool | None = Field(None, alias=ATTR_DEFAULT_SOURCE_SCRIPTED)
    report_logging: bool | None = Field(None, alias=ATTR_REPORT_LOGGING)
    default_variable_prefix: str | None = Field(None, alias=ATTR_DEFAULT_VARIABLE_PREFIX)
    default_variable_suffix: str | None = Field(None, alias=ATTR_DEFAULT_VARIABLE_SUFFIX)

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
            },
        )
