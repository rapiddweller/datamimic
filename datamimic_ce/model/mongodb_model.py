# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/


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
