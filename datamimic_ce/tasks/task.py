# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC, abstractmethod

from datamimic_ce.contexts.context import Context
from datamimic_ce.statements.statement import Statement


class Task(ABC):
    @abstractmethod
    def execute(self, ctx: Context) -> None:
        pass

    @property
    @abstractmethod
    def statement(self) -> Statement:
        pass
