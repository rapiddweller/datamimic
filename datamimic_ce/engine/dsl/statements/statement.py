# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC
from typing import TYPE_CHECKING, Optional

from datamimic_ce.engine.dsl.constants.convention_constants import NAME_SEPARATOR

if TYPE_CHECKING:
    from datamimic_ce.engine.dsl.statements.generate_statement import GenerateStatement


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
    def source_entity(self) -> str | None:
        """Explicit physical entity to read; None unless a subclass (generate/iterate, variable)
        carries a sourceEntity. Lets StatementUtil.resolve_source_entity work on any statement."""
        return None

    @property
    def full_name(self) -> str | None:
        return self._full_name

    @property
    def parent_stmt(self) -> Optional["Statement"]:
        return self._parent_stmt

    @property
    def child_parent(self) -> "Statement":
        """The statement a direct child should treat as its logical parent."""
        return self

    def get_parent_full_name(self):
        # Split the path into components
        path_components = self.full_name.split(NAME_SEPARATOR)
        # Remove the last component
        path_components.pop()
        # Join the components back together
        return NAME_SEPARATOR.join(path_components)

    def get_root_generate_statement(self) -> Optional["GenerateStatement"]:  # noqa: F821
        from datamimic_ce.engine.dsl.statements.generate_statement import GenerateStatement

        if isinstance(self, GenerateStatement):
            return None
        parent_stmt = self.parent_stmt
        while parent_stmt is not None and not isinstance(parent_stmt, GenerateStatement):
            parent_stmt = parent_stmt.parent_stmt
        return parent_stmt

    @staticmethod
    def _adjust_parent_stmt(parent_stmt: Optional["Statement"]) -> Optional["Statement"]:
        return None if parent_stmt is None else parent_stmt.child_parent
