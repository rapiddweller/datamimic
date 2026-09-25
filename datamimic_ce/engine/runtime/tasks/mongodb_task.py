# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.api import MongoDBStatement
from datamimic_ce.engine.io.api import MongoDBConnectionConfig, create_mongodb_client
from datamimic_ce.engine.runtime.contexts.setup_context import SetupContext
from datamimic_ce.engine.runtime.tasks.task import SetupSubTask


class MongoDBTask(SetupSubTask):
    def __init__(self, statement: MongoDBStatement):
        self._statement = statement

    @property
    def statement(self) -> MongoDBStatement:
        return self._statement

    def execute(self, ctx: SetupContext):
        connection_config = MongoDBConnectionConfig(**self._statement.model.model_dump())
        ctx.add_client(
            self._statement.mongodb_id,
            create_mongodb_client(connection_config),
        )
