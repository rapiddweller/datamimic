# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.credentials.rdbms_credential import RdbmsCredential
from datamimic_ce.model.database_model import DatabaseModel
from datamimic_ce.statements.statement import Statement


class DatabaseStatement(Statement):
    def __init__(self, model: DatabaseModel):
        super().__init__(None, None)

        # Get credentials from descriptor element attribute, user defined conf or system env properties file
        self._db_id = model.id

        # Compose Database credentials
        self._db_credential = RdbmsCredential(**model.model_dump())

    @property
    def db_id(self):
        return self._db_id

    @property
    def db_credential(self):
        return self._db_credential
