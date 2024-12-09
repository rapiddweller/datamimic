# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

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
