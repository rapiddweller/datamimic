# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.contexts.context import Context
from datamimic_ce.statements.memstore_statement import MemstoreStatement
from datamimic_ce.tasks.task import Task


class MemstoreTask(Task):
    def __init__(self, statement: MemstoreStatement):
        self._statement = statement

    @property
    def statement(self) -> MemstoreStatement:
        return self._statement

    def execute(self, ctx: Context):
        ctx.root.memstore_manager.add_memstore(self.statement.id)
