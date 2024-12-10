# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, ConfigDict

from datamimic_ce.credentials.credential import Credential


class RdbmsCredential(Credential, BaseModel):
    """
    Database's credentials used for connecting to database server
    """

    dbms: str
    host: str | None
    port: int | None
    user: str | None
    password: str | None
    database: str
    db_schema: str | None

    model_config = ConfigDict(extra="allow")

    def get_credentials(self):
        return {
            "dbms": self.dbms,
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "db_schema": self.db_schema,
        }

    def check_credentials(self):
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
