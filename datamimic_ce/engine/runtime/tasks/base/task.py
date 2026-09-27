# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC, abstractmethod
from typing import Protocol

from datamimic_ce.engine.dsl.api import Statement
from datamimic_ce.engine.runtime.contexts.context import Context
from datamimic_ce.engine.runtime.contexts.geniter_context import GenIterContext
from datamimic_ce.engine.runtime.contexts.setup_context import SetupContext


class Task(ABC):
    """
    Super class of all tasks
    """

    @property
    @abstractmethod
    def statement(self) -> Statement:
        pass

    def pre_execute(self, ctx: Context) -> None:
        """Prepare state that must be initialized before task execution."""
        return None


class ExecutableTask(Protocol):
    def execute(self, ctx: SetupContext | GenIterContext) -> object: ...


class GenSubTask(Task, ABC):
    """
    Sub-task of GenerateTask
    """

    @abstractmethod
    def execute(self, ctx: GenIterContext) -> object:
        pass


class SetupSubTask(Task, ABC):
    """
    Sub-task of SetupTask
    """

    @abstractmethod
    def execute(self, ctx: SetupContext) -> object:
        pass


class CommonSubTask(Task, ABC):
    """
    Sub-task of SetupTask and GenerateTask
    """

    @abstractmethod
    def execute(self, ctx: SetupContext | GenIterContext) -> object:
        pass
