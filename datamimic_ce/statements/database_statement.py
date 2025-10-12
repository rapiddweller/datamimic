# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.model.database_model import DatabaseModel
from datamimic_ce.statements.statement import Statement


class DatabaseStatement(Statement):
    def __init__(self, model: DatabaseModel):
        super().__init__(None, None)

        # Get connection configuration from descriptor element attribute, user defined conf or system env properties
        self._db_id = model.id

        # Compose Database connection configuration
        self._db_connection_config = RdbmsConnectionConfig(**model.model_dump())

    @property
    def db_id(self):
        return self._db_id

    @property
    def db_connection_config(self):
        return self._db_connection_config
