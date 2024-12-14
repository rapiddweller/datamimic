# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC, abstractmethod
from typing import Any, Awaitable

from datamimic_ce.contexts.context import Context
from datamimic_ce.statements.statement import Statement


class Task(ABC):
    @abstractmethod
    def execute(self, ctx: Context) -> dict[str, list] | Awaitable[dict[str, list]] | None:
        """Execute the task.

        Args:
            context: The execution context

        Returns:
            Dict mapping statement names to lists of generated records,
            or an awaitable that resolves to such a dict,
            or None if no results are produced
        """
        pass

    @property
    @abstractmethod
    def statement(self) -> Statement:
        pass
