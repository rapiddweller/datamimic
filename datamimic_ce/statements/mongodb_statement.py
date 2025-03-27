# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.model.mongodb_model import MongoDBModel
from datamimic_ce.statements.statement import Statement


class MongoDBStatement(Statement):
    def __init__(self, model: MongoDBModel):
        super().__init__(None, None)
        self._model = model
        self._mongodb_connection_config = MongoDBConnectionConfig(**model.model_dump())
        self._mongodb_client = MongoDBClient(self._mongodb_connection_config)
        self._mongodb_id = model.id

    @property
    def mongodb_id(self):
        return self._mongodb_id

    @property
    def mongodb_connection_config(self):
        return self._mongodb_connection_config
