# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC, abstractmethod
from typing import Any

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.statements.statement import Statement


class Task(ABC):
    """
    Super class of all tasks
    """

    @property
    @abstractmethod
    def statement(self) -> Statement:
        pass


class GenSubTask(Task, ABC):
    """
    Sub-task of GenerateTask
    """

    @abstractmethod
    def execute(self, ctx: GenIterContext) -> Any:
        pass


class SetupSubTask(Task, ABC):
    """
    Sub-task of SetupTask
    """

    @abstractmethod
    def execute(self, ctx: SetupContext) -> Any:
        pass


class CommonSubTask(Task, ABC):
    """
    Sub-task of SetupTask and GenerateTask
    """

    @abstractmethod
    def execute(self, ctx: SetupContext | GenIterContext) -> Any:
        pass
