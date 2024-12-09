# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.statements.database_statement import DatabaseStatement
from datamimic_ce.tasks.task import Task


class DatabaseTask(Task):
    def __init__(self, statement: DatabaseStatement):
        self._statement = statement

    def execute(self, ctx: SetupContext):
        client = RdbmsClient(self._statement.db_credential, ctx.task_id)
        ctx.add_client(self._statement.db_id, client)

    @property
    def statement(self) -> DatabaseStatement:
        return self._statement
