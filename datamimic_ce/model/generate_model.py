# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, Field, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import (
    ATTR_BUCKET,
    ATTR_CONTAINER,
    ATTR_CONVERTER,
    ATTR_COUNT,
    ATTR_CYCLIC,
    ATTR_DISTRIBUTION,
    ATTR_EXPORT_URI,
    ATTR_MULTIPROCESSING,
    ATTR_NAME,
    ATTR_NUM_PROCESS,
    ATTR_PAGE_SIZE,
    ATTR_SELECTOR,
    ATTR_SEPARATOR,
    ATTR_SOURCE,
    ATTR_SOURCE_SCRIPTED,
    ATTR_SOURCE_URI,
    ATTR_STORAGE_ID,
    ATTR_TARGET,
    ATTR_TYPE,
    ATTR_VARIABLE_PREFIX,
    ATTR_VARIABLE_SUFFIX,
)
from datamimic_ce.model.model_util import ModelUtil


class GenerateModel(BaseModel):
    name: str
    count: str | None = None
    source: str | None = None
    cyclic: bool | None = None
    type: str | None = None
    selector: str | None = None
    separator: str | None = None
    source_scripted: bool | None = Field(None, alias=ATTR_SOURCE_SCRIPTED)
    target: str | None = None
    page_size: int | None = Field(None, alias=ATTR_PAGE_SIZE)
    source_uri: str | None = Field(None, alias=ATTR_SOURCE_URI)
    container: str | None = None
    storage_id: str | None = Field(None, alias=ATTR_STORAGE_ID)
    multiprocessing: bool | None = None
    export_uri: str | None = Field(None, alias=ATTR_EXPORT_URI)
    distribution: str | None = None
    variable_prefix: str | None = Field(None, alias=ATTR_VARIABLE_PREFIX)
    variable_suffix: str | None = Field(None, alias=ATTR_VARIABLE_SUFFIX)
    converter: str | None = None
    bucket: str | None = Field(None, alias=ATTR_BUCKET)
    num_process: int | None = Field(None, alias=ATTR_NUM_PROCESS)

    @model_validator(mode="before")
    @classmethod
    def check_generate_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={
                ATTR_TARGET,
                ATTR_COUNT,
                ATTR_CYCLIC,
                ATTR_NAME,
                ATTR_SELECTOR,
                ATTR_SEPARATOR,
                ATTR_SOURCE,
                ATTR_SOURCE_SCRIPTED,
                ATTR_TYPE,
                ATTR_PAGE_SIZE,
                ATTR_SOURCE_URI,
                ATTR_CONTAINER,
                ATTR_STORAGE_ID,
                ATTR_MULTIPROCESSING,
                ATTR_EXPORT_URI,
                ATTR_DISTRIBUTION,
                ATTR_VARIABLE_PREFIX,
                ATTR_VARIABLE_SUFFIX,
                ATTR_CONVERTER,
                ATTR_NUM_PROCESS,
            },
        )

    @model_validator(mode="before")
    @classmethod
    def validate_count_and_source(cls, values: dict):
        return ModelUtil.check_exist_count(values=values)

    @model_validator(mode="before")
    @classmethod
    def validate_additional_source_attributes(cls, values: dict):
        return ModelUtil.check_valid_additional_source_attributes(values=values)

    @model_validator(mode="before")
    @classmethod
    def validate_generator_mode_of_source(cls, values: dict):
        """
        Validate at most "type" or "selector" can be defined with "source"
        :param value:
        :return:
        """
        return ModelUtil.check_generation_mode_of_source(values)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        return ModelUtil.check_not_empty(value=value)

    @field_validator("count")
    @classmethod
    def validate_count(cls, value):
        return ModelUtil.check_is_digit_or_script(value=value)

    @field_validator("distribution")
    @classmethod
    def validate_distribution(cls, value):
        """
        Validate attribute "distribution"
        """
        return ModelUtil.check_valid_distribution(value)
