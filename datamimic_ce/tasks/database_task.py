# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

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
