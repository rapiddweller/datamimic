# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.api import DatabaseStatement
from datamimic_ce.engine.io.api import RdbmsClient, RdbmsConnectionConfig
from datamimic_ce.engine.runtime.contexts.setup_context import SetupContext
from datamimic_ce.engine.runtime.tasks.task import SetupSubTask


class DatabaseTask(SetupSubTask):
    def __init__(self, statement: DatabaseStatement):
        self._statement = statement

    def execute(self, ctx: SetupContext):
        connection_config = RdbmsConnectionConfig(**self._statement.model.model_dump())
        client = RdbmsClient(connection_config, ctx.task_id)
        ctx.add_client(self._statement.db_id, client)

    @property
    def statement(self) -> DatabaseStatement:
        return self._statement
