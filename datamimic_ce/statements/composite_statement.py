# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from abc import ABC

from datamimic_ce.statements.statement import Statement


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
