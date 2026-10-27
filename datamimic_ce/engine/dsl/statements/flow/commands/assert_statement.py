# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.model.flow.commands.assert_model import AssertModel
from datamimic_ce.engine.dsl.statements.base.statement import Statement


class AssertStatement(Statement):
    def __init__(self, model: AssertModel, line: int | None = None):
        super().__init__(None, None)
        self._condition = model.condition
        self._message = model.message
        # Build finds the failed assert by its line: two asserts in one step otherwise share one path.
        self._line = line

    @property
    def condition(self) -> str:
        return self._condition

    @property
    def message(self) -> str | None:
        return self._message

    @property
    def line(self) -> int | None:
        return self._line
