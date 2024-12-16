# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, ConfigDict

from datamimic_ce.credentials.credential import Credential


class MongoDBCredential(BaseModel, Credential):
    """
    MongoDB's credentials used for connecting to database server
    """

    host: str
    port: int
    database: str
    user: str | None = None
    password: str | None = None

    model_config = ConfigDict(extra="allow")

    def get_credentials(self):
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
        }

    def check_credentials(self):
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
