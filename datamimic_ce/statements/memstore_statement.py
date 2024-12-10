# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.model.memstore_model import MemstoreModel
from datamimic_ce.statements.statement import Statement


class MemstoreStatement(Statement):
    def __init__(self, model: MemstoreModel):
        self._id = model.id

    @property
    def id(self):
        return self._id
