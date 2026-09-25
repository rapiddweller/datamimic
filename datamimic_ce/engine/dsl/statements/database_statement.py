# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.model.database_model import DatabaseModel
from datamimic_ce.engine.dsl.statements.statement import Statement


class DatabaseStatement(Statement):
    def __init__(self, model: DatabaseModel):
        super().__init__(None, None)

        self._model = model

    @property
    def model(self) -> DatabaseModel:
        return self._model

    @property
    def db_id(self):
        return self._model.id
