# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.model.execute_model import ExecuteModel
from datamimic_ce.statements.statement import Statement


class ExecuteStatement(Statement):
    def __init__(self, model: ExecuteModel, exec_type: str, code: str | None = None):
        super().__init__(name=None, parent_stmt=None)  # setup-level: no name/parent, but honor the base contract
        self._uri = model.uri
        self._target = model.target
        self._type = exec_type  # resolved: python | bash | sql
        self._code = code  # inline code (None when a uri script file is used)
        self._script = model.script  # expression whose evaluated value is the code

    @property
    def uri(self):
        return self._uri

    @property
    def target(self):
        return self._target

    @property
    def type(self) -> str:
        return self._type

    @property
    def code(self) -> str | None:
        return self._code

    @property
    def script(self) -> str | None:
        return self._script
