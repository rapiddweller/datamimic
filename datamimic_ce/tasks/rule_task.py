# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.statements.rule_statement import RuleStatement
from datamimic_ce.tasks.task import Task


class RuleTask(Task):
    def __init__(
        self,
        statement: RuleStatement,
    ):
        self._statement = statement

    @property
    def statement(self) -> RuleStatement:
        return self._statement

    def execute(self, parent_context: GenIterContext):
        pass
