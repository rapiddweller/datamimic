# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, ConfigDict

from datamimic_ce.connection_config.connection_config_base import ConnectionConfig


class MongoDBConnectionConfig(BaseModel, ConnectionConfig):
    """
    MongoDB's connection configuration used for connecting to database server
    """

    host: str
    port: int
    database: str
    user: str | None = None
    password: str | None = None

    model_config = ConfigDict(extra="allow")

    def get_connection_config(self):
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
        }

    def check_connection_config(self):
        if not self.host:
            raise ValueError("Host is required")

        if not self.port:
            raise ValueError("Port is required")

        if not self.database:
            raise ValueError("Database is required")

        if not self.user:
            raise ValueError("User is required")

        if not self.password:
            raise ValueError("Password is required")

        return True
