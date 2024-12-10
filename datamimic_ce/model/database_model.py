# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, ConfigDict, Field, field_validator

from datamimic_ce.constants.attribute_constants import ATTR_SCHEMA
from datamimic_ce.model.model_util import ModelUtil


class DatabaseModel(BaseModel):
    id: str
    host: str | None = None
    port: str | None = None
    database: str | None = None
    dbms: str
    environment: str | None = None
    system: str | None = None
    user: str | None = None
    password: str | None = None
    db_schema: str | None = Field(None, alias=ATTR_SCHEMA)

    model_config = ConfigDict(extra="allow")

    @field_validator("id", "host", "database", "dbms")
    @classmethod
    def validate_name(cls, value):
        return ModelUtil.check_not_empty(value=value)

    @field_validator("port")
    @classmethod
    def validate_port(cls, value):
        return value if value is None else ModelUtil.check_is_digit(value=value)
