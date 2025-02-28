# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.tasks.task import Task

from datamimic_ce.statements.constraints_statement import ConstraintsStatement


class ConstraintsTask(Task):
    def __init__(self, statement: ConstraintsStatement):
        self._statement = statement

    def execute(self, parent_context: GenIterContext):
        pass

    @property
    def statement(self) -> ConstraintsStatement:
        return self._statement
