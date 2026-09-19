# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, ConfigDict, Field, field_validator

from datamimic_ce.model.model_util import ModelUtil


class MongoDBModel(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier for this MongoDB connection, referenced elsewhere via "
        "source=/target= (e.g. <generate target='mongo.upsert'/>, <variable source='mongo'/>).",
        examples=["mongo", "sourceMongo"],
    )
    host: str = Field(
        ...,
        description="Hostname or IP of the MongoDB server. When omitted, resolved from "
        "conf/{environment}.env.properties using key '{system}.mongo.host'.",
        examples=["localhost", "127.0.0.1"],
    )
    port: str = Field(
        ...,
        description="Port number of the MongoDB server, as a string of digits. When omitted, "
        "resolved from conf/{environment}.env.properties using key '{system}.mongo.port'.",
        examples=["27017"],
    )
    database: str = Field(
        ...,
        description="Database name to connect to. When omitted, resolved from "
        "conf/{environment}.env.properties using key '{system}.mongo.database'.",
        examples=["mydb"],
    )
    environment: str | None = Field(
        None,
        description="Selects which conf/{environment}.env.properties file supplies credentials "
        "not given directly on this element. Defaults to 'local' when running in development, "
        "otherwise 'environment'.",
        examples=["local", "dev", "prod"],
    )
    user: str | None = Field(
        None,
        description="Username for the MongoDB connection. When omitted, resolved from "
        "conf/{environment}.env.properties using key '{system}.mongo.user'.",
        examples=["mongo_user"],
    )
    password: str | None = Field(
        None,
        description="Password for the MongoDB connection. When omitted, resolved from "
        "conf/{environment}.env.properties using key '{system}.mongo.password'.",
        examples=["secret"],
    )

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
