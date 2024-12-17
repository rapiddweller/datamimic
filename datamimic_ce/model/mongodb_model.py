# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, ConfigDict, field_validator

from datamimic_ce.model.model_util import ModelUtil


class MongoDBModel(BaseModel):
    id: str
    host: str
    port: str
    database: str
    environment: str | None = None
    user: str | None = None
    password: str | None = None

    model_config = ConfigDict(extra="allow")

    # @model_validator(mode="before")
    # @classmethod
    # def check_database_valid_attributes(cls, values: Dict):
    #     return ModelUtil.check_valid_attributes(
    #         values=values,
    #         valid_attributes={
    #             ATTR_ID,
    #             ATTR_HOST,
    #             ATTR_PORT,
    #             ATTR_DATABASE,
    #             ATTR_USER,
    #             ATTR_PASSWORD,
    #             ATTR_SYSTEM,
    #             ATTR_ENVIRONMENT,
    #         },
    #     )

    @field_validator("id", "host", "port", "database")
    @classmethod
    def validate_name(cls, value):
        return ModelUtil.check_not_empty(value=value)

    @field_validator("port")
    @classmethod
    def validate_port(cls, value):
        return ModelUtil.check_is_digit(value=value)
