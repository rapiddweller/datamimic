# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC, abstractmethod
from typing import Any

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.statements.statement import Statement


class Task(ABC):
    @property
    @abstractmethod
    def statement(self) -> Statement:
        pass


class SetupSubTask(Task, ABC):
    @abstractmethod
    def execute(self, ctx: SetupContext) -> Any:
        pass


class GenIterSubTask(Task, ABC):
    @abstractmethod
    def execute(self, ctx: GenIterContext) -> Any:
        pass


class CommonSubTask(Task, ABC):
    @abstractmethod
    def execute(self, ctx: SetupContext | GenIterContext) -> Any:
        pass
