# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

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
