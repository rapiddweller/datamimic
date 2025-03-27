# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, ConfigDict

from datamimic_ce.connection_config.connection_config_base import ConnectionConfig


class RdbmsConnectionConfig(ConnectionConfig, BaseModel):
    """
    Database's connection configuration used for connecting to database server
    """

    dbms: str
    host: str | None
    port: int | None
    user: str | None
    password: str | None
    database: str
    db_schema: str | None

    model_config = ConfigDict(extra="allow")

    def get_connection_config(self):
        return BaseModel.model_dump(self)

    def check_connection_config(self):
        if not self.dbms:
            raise ValueError("DBMS is required")

        if not self.host:
            raise ValueError("Host is required")

        if not self.port:
            raise ValueError("Port is required")

        if not self.user:
            raise ValueError("User is required")

        if not self.password:
            raise ValueError("Password is required")

        if not self.database:
            raise ValueError("Database is required")

        if not self.db_schema:
            raise ValueError("DB Schema is required")

        return True
