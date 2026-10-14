# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, ConfigDict, Field, field_validator

from datamimic_ce.engine.dsl.model.validation import ModelUtil


class MongoDBModel(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier for this MongoDB connection, referenced elsewhere via "
        "source=/target= (e.g. <generate target='mongo.upsert'/>, <variable source='mongo'/>).",
        examples=["mongo", "sourceMongo"],
    )
    host: str = Field(
        ...,
        description="Hostname or IP of the MongoDB server. Prefer the connection profile: a matching "
        "'{system}.mongo.host' property overrides this attribute; without one, this value is kept.",
        examples=["localhost", "127.0.0.1"],
    )
    port: str = Field(
        ...,
        description="Port number of the MongoDB server, as a string of digits. A matching "
        "'{system}.mongo.port' connection-profile property overrides this attribute; otherwise this value is kept.",
        examples=["27017"],
    )
    database: str = Field(
        ...,
        description="Database name to connect to. A matching '{system}.mongo.database' "
        "connection-profile property overrides this attribute; otherwise this value is kept.",
        examples=["mydb"],
    )
    environment: str | None = Field(
        None,
        description="Selects the connection profile: first conf/{environment}.env.properties beside the descriptor, "
        "then {environment}.env.properties in the working directory, then ~/datamimic/{environment}.env.properties. "
        "The first existing file is used; '{system}.mongo.{attr}' properties override matching descriptor attributes. "
        "The system prefix defaults to id. Defaults to 'local' when running in development, otherwise 'environment'.",
        examples=["local", "dev", "prod"],
    )
    user: str | None = Field(
        None,
        description="Username for the MongoDB connection. A matching '{system}.mongo.user' "
        "connection-profile property overrides this attribute; otherwise this value is kept.",
        examples=["mongo_user"],
    )
    password: str | None = Field(
        None,
        description="Password for the MongoDB connection. A matching '{system}.mongo.password' "
        "connection-profile property overrides this attribute; otherwise this value is kept.",
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
