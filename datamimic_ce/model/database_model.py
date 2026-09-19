# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, ConfigDict, Field, field_validator

from datamimic_ce.constants.attribute_constants import ATTR_SCHEMA
from datamimic_ce.model.model_util import ModelUtil


class DatabaseModel(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier for this database connection, referenced elsewhere via "
        "source=/target= (e.g. <generate target='db'/>, <variable source='db'/>, <execute target='db'/>).",
        examples=["db", "sourceDB"],
    )
    host: str | None = Field(
        None,
        description="Hostname or IP of the database server. When omitted, resolved from "
        "conf/{environment}.env.properties using key '{system}.db.host'.",
        examples=["localhost", "127.0.0.1"],
    )
    port: str | None = Field(
        None,
        description="Port number of the database server, as a string of digits. When omitted, "
        "resolved from conf/{environment}.env.properties using key '{system}.db.port'.",
        examples=["5432", "3306"],
    )
    database: str | None = Field(
        None,
        description="Database/service name to connect to. When omitted, resolved from "
        "conf/{environment}.env.properties using key '{system}.db.database'.",
        examples=["mydb"],
    )
    dbms: str = Field(
        ...,
        description="Database management system driving connection/dialect handling.",
        examples=["postgresql", "mysql", "mssql", "oracle"],
    )
    environment: str | None = Field(
        None,
        description="Selects which conf/{environment}.env.properties file supplies credentials "
        "not given directly on this element. Defaults to 'local' when running in development, "
        "otherwise 'environment'.",
        examples=["local", "dev", "prod"],
    )
    system: str | None = Field(
        None,
        description="Credential-lookup key prefix used to read unset attributes from the "
        "environment properties file as '{system}.db.{attr}' (e.g. db.db.host). Defaults to id "
        "when omitted.",
        examples=["db"],
    )
    user: str | None = Field(
        None,
        description="Username for the database connection. When omitted, resolved from "
        "conf/{environment}.env.properties using key '{system}.db.user'.",
        examples=["postgres"],
    )
    password: str | None = Field(
        None,
        description="Password for the database connection. When omitted, resolved from "
        "conf/{environment}.env.properties using key '{system}.db.password'.",
        examples=["secret"],
    )
    db_schema: str | None = Field(
        None,
        alias=ATTR_SCHEMA,
        description="Default schema/namespace to use when connecting; used for table reflection, "
        "table lookups and sequence resolution (falls back to 'public' for sequences when unset).",
        examples=["public"],
    )

    model_config = ConfigDict(extra="allow")

    @field_validator("id", "host", "database", "dbms")
    @classmethod
    def validate_name(cls, value):
        return ModelUtil.check_not_empty(value=value)

    @field_validator("port")
    @classmethod
    def validate_port(cls, value):
        return value if value is None else ModelUtil.check_is_digit(value=value)
