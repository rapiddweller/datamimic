# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.statements.mongodb_statement import MongoDBStatement
from datamimic_ce.tasks.task import Task


class MongoDBTask(Task):
    def __init__(self, statement: MongoDBStatement):
        self._statement = statement

    @property
    def statement(self) -> MongoDBStatement:
        return self._statement

    def execute(self, ctx: SetupContext):
        ctx.add_client(
            self._statement.mongodb_id,
            MongoDBClient(self._statement.mongodb_credential),
        )
