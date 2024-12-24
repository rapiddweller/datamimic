# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.statements.mongodb_statement import MongoDBStatement
from datamimic_ce.tasks.task import SetupSubTask


class MongoDBTask(SetupSubTask):
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
