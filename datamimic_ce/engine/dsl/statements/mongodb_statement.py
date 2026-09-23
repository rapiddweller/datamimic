# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.model.mongodb_model import MongoDBModel
from datamimic_ce.engine.dsl.statements.statement import Statement


class MongoDBStatement(Statement):
    def __init__(self, model: MongoDBModel):
        super().__init__(None, None)
        self._model = model

    @property
    def model(self) -> MongoDBModel:
        return self._model

    @property
    def mongodb_id(self):
        return self._model.id
