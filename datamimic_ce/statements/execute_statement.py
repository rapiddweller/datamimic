# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.model.execute_model import ExecuteModel
from datamimic_ce.statements.statement import Statement


class ExecuteStatement(Statement):
    def __init__(self, model: ExecuteModel):
        self._uri = model.uri
        self._target = model.target

    @property
    def uri(self):
        return self._uri

    @property
    def target(self):
        return self._target
