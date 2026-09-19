# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.model.while_model import WhileModel
from datamimic_ce.statements.composite_statement import CompositeStatement


class WhileStatement(CompositeStatement):
    def __init__(self, model: WhileModel, parent_stmt: CompositeStatement):
        super().__init__(name=None, parent_stmt=parent_stmt)
        self._condition = model.condition
        self._max_iterations = model.max_iterations

    @property
    def condition(self) -> str:
        return self._condition

    @property
    def max_iterations(self) -> int:
        return self._max_iterations
