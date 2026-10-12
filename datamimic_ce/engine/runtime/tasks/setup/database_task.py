# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.api import DatabaseStatement
from datamimic_ce.engine.io.api import RdbmsConnectionConfig
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.tasks.base.task import SetupSubTask


class DatabaseTask(SetupSubTask):
    def __init__(self, statement: DatabaseStatement):
        self._statement = statement

    def execute(self, ctx: SetupContext):
        connection_config = RdbmsConnectionConfig(**self._statement.model.model_dump())
        ctx.register_client_config(self._statement.db_id, connection_config)

    @property
    def statement(self) -> DatabaseStatement:
        return self._statement
