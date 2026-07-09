# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.contexts.context import Context
from datamimic_ce.statements.memstore_statement import MemstoreStatement
from datamimic_ce.tasks.task import SetupSubTask


class MemstoreTask(SetupSubTask):
    def __init__(self, statement: MemstoreStatement):
        self._statement = statement

    @property
    def statement(self) -> MemstoreStatement:
        return self._statement

    def execute(self, ctx: Context):
        ctx.root.memstore_manager.add_memstore(self.statement.id)
        # Bind by id into the script namespace (migration parity: <execute>/<variable script=>
        # can reference `mem` directly, e.g. `mem.sumEntityColumn(...)`) - mirrors add_client's
        # binding for <database>/<mongodb>.
        ctx.root.namespace[self.statement.id] = ctx.root.memstore_manager.get_memstore(self.statement.id)
