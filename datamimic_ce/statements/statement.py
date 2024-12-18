# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC
from typing import TYPE_CHECKING, Optional

from datamimic_ce.constants.convention_constants import NAME_SEPARATOR

if TYPE_CHECKING:
    from datamimic_ce.statements.generate_statement import GenerateStatement


class Statement(ABC):  # noqa: B024
    def __init__(self, name: str | None, parent_stmt: Optional["Statement"]):
        self._name = name
        parent_stmt = self._adjust_parent_stmt(parent_stmt)
        self._parent_stmt = parent_stmt
        self._full_name = (
            name
            if (parent_stmt is None or parent_stmt.full_name is None)
            else f"{parent_stmt.full_name}{NAME_SEPARATOR}{self._name}"
        )

    @property
    def name(self) -> str | None:
        return self._name

    @property
    def full_name(self) -> str | None:
        return self._full_name

    @property
    def parent_stmt(self) -> Optional["Statement"]:
        return self._parent_stmt

    def get_parent_full_name(self):
        # Split the path into components
        path_components = self.full_name.split(NAME_SEPARATOR)
        # Remove the last component
        path_components.pop()
        # Join the components back together
        return NAME_SEPARATOR.join(path_components)

    def get_root_generate_statement(self) -> Optional["GenerateStatement"]:  # noqa: F821
        from datamimic_ce.statements.generate_statement import GenerateStatement
        from datamimic_ce.statements.setup_statement import SetupStatement

        if isinstance(self, GenerateStatement | SetupStatement):
            return None
        else:
            parent_stmt = self.parent_stmt
            while not isinstance(parent_stmt, GenerateStatement):
                parent_stmt = parent_stmt.parent_stmt if parent_stmt is not None else None
            return parent_stmt

    @staticmethod
    def _adjust_parent_stmt(parent_stmt):
        """
        Change parent statement of sub-statements of [IfStatement, ElseIfStatement, ElseStatement]
        Because Condition/if-else statement just for decision-making,
        its sub-statements parent should connect to parent statement of <Condition>
        """
        from datamimic_ce.statements.else_if_statement import ElseIfStatement
        from datamimic_ce.statements.else_statement import ElseStatement
        from datamimic_ce.statements.if_statement import IfStatement

        # attach sub statements of if/else (condition) to outer statement
        if isinstance(parent_stmt, IfStatement | ElseIfStatement | ElseStatement):
            parent_stmt = parent_stmt.parent_stmt.parent_stmt

        return parent_stmt
