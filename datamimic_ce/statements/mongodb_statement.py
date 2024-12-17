# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.credentials.mongodb_credential import MongoDBCredential
from datamimic_ce.model.mongodb_model import MongoDBModel
from datamimic_ce.statements.statement import Statement


class MongoDBStatement(Statement):
    def __init__(self, model: MongoDBModel):
        super().__init__(None, None)
        self._mongodb_id = model.id

        # Compose MongoDB credentials
        self._mongodb_credential = MongoDBCredential(**model.model_dump())

    @property
    def mongodb_id(self):
        return self._mongodb_id

    @property
    def mongodb_credential(self):
        return self._mongodb_credential
