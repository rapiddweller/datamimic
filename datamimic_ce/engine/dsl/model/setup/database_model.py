# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, ConfigDict, Field, field_validator

from datamimic_ce.engine.dsl.model.validation import ModelUtil
from datamimic_ce.engine.dsl.vocabulary.constants.attribute_constants import ATTR_SCHEMA
from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms


class DatabaseModel(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier for this database connection, referenced elsewhere via "
        "source=/target= (e.g. <generate target='db'/>, <variable source='db'/>, <execute target='db'/>).",
        examples=["db", "sourceDB"],
    )
    host: str | None = Field(
        None,
        description="Hostname or IP of the database server. Prefer the connection profile: "
        "a matching '{system}.db.host' property overrides this attribute; without one, this value is kept.",
        examples=["localhost", "127.0.0.1"],
    )
    port: str | None = Field(
        None,
        description="Port number of the database server, as a string of digits. A matching "
        "'{system}.db.port' connection-profile property overrides this attribute; otherwise this value is kept.",
        examples=["5432", "3306"],
    )
    database: str | None = Field(
        None,
        description="Database/service name to connect to. A matching '{system}.db.database' "
        "connection-profile property overrides this attribute; otherwise this value is kept.",
        examples=["mydb"],
    )
    dbms: Dbms = Field(
        ...,
        description="Database management system driving connection/dialect handling. A matching "
        "'{system}.db.dbms' connection-profile property overrides this attribute.",
        examples=[dbms.value for dbms in Dbms],
    )
    environment: str | None = Field(
        None,
        description="Selects the connection profile: first conf/{environment}.env.properties beside the descriptor, "
        "then {environment}.env.properties in the working directory, then ~/datamimic/{environment}.env.properties. "
        "The first existing file is used; matching properties override descriptor attributes. "
        "Defaults to 'local' when running in development, otherwise 'environment'.",
        examples=["local", "dev", "prod"],
    )
    system: str | None = Field(
        None,
        description="Connection-profile key prefix used to override matching attributes as "
        "'{system}.db.{attr}' (e.g. db.db.host). Defaults to id "
        "when omitted.",
        examples=["db"],
    )
    user: str | None = Field(
        None,
        description="Username for the database connection. A matching '{system}.db.user' "
        "connection-profile property overrides this attribute; otherwise this value is kept.",
        examples=["postgres"],
    )
    password: str | None = Field(
        None,
        description="Password for the database connection. A matching '{system}.db.password' "
        "connection-profile property overrides this attribute; otherwise this value is kept.",
        examples=["secret"],
    )
    db_schema: str | None = Field(
        None,
        alias=ATTR_SCHEMA,
        description="Default schema/namespace to use when connecting; used for table reflection, "
        "table lookups and sequence resolution (falls back to 'public' for sequences when unset). "
        "A matching '{system}.db.schema' connection-profile property overrides this attribute.",
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
