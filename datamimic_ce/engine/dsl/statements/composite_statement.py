# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC
from typing import TYPE_CHECKING

from datamimic_ce.engine.dsl.statements.statement import Statement

if TYPE_CHECKING:
    from datamimic_ce.engine.dsl.statements.generate_statement import GenerateStatement


class CompositeStatement(Statement, ABC):
    """
    Combine many statements into a composite one
    """

    def __init__(self, name: str | None, parent_stmt: Statement | None):
        super().__init__(name=name, parent_stmt=parent_stmt)

    @property
    def sub_statements(self) -> list[Statement]:
        return self._sub_statements

    @sub_statements.setter
    def sub_statements(self, sub_statements: list[Statement]) -> None:
        self._sub_statements = [] if sub_statements is None else sub_statements

    def retrieve_sub_statement_by_fullname(self, name: str) -> "GenerateStatement | None":
        return None

    def retrieve_executed_sub_gen_statement_by_name(self, name: str) -> "GenerateStatement | None":
        return None


class ConditionBranchStatement(CompositeStatement, ABC):
    @property
    def child_parent(self) -> Statement:
        """A branch is control flow; its children belong to the enclosing statement."""
        condition = self.parent_stmt
        if condition is None or condition.parent_stmt is None:
            raise ValueError("Condition branch has no enclosing statement")
        return condition.parent_stmt
