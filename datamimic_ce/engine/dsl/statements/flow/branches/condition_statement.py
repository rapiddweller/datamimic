# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.statements.base.composite_statement import CompositeStatement, ConditionBranchStatement


class ConditionStatement(CompositeStatement):
    def __init__(self, parent_stmt: CompositeStatement):
        super().__init__(name=None, parent_stmt=parent_stmt)
        self.executed_statements: set[ConditionBranchStatement] = set()

    def add_executed_statement(self, value: ConditionBranchStatement) -> None:
        """
        Keep executed statements for later use
        """
        self.executed_statements.add(value)
