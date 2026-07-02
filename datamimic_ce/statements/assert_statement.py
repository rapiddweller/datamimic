# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.model.assert_model import AssertModel
from datamimic_ce.statements.statement import Statement


class AssertStatement(Statement):
    def __init__(self, model: AssertModel):
        super().__init__(None, None)
        self._condition = model.condition
        self._message = model.message

    @property
    def condition(self) -> str:
        return self._condition

    @property
    def message(self) -> str | None:
        return self._message
