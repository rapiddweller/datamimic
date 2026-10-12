# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
from contextlib import suppress
from pathlib import Path
from typing import Literal

from datamimic_ce.domains.api import RunSeed
from datamimic_ce.engine.dsl.api import DatabaseStatement, MongoDBStatement, SetupStatement
from datamimic_ce.engine.io.api import (
    MongoDBConnectionConfig,
    RdbmsConnectionConfig,
    RegisteredClient,
    TestResultExporter,
    clone_client_for_include,
    create_mongodb_client,
    create_rdbms_client,
    dispose_client_engine,
)
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.storage.memstore_manager import MemstoreManager
from datamimic_ce.engine.runtime.tasks.base.dispatch import create_task
from datamimic_ce.engine.runtime.tasks.base.task import CommonSubTask, SetupSubTask


class SetupTask:
    def __init__(
        self,
        setup_stmt: SetupStatement,
        memstore_manager: MemstoreManager | None,
        task_id: str,
        properties: dict[str, str] | dict[str, object] | None,
        test_mode: bool,
        test_result_storage: TestResultExporter,
        descriptor_dir: Path,
        runtime_environment: Literal["development", "production"] = "production",
        ray_debug: bool = False,
    ):
        self._descriptor_dir = descriptor_dir
        self._setup_stmt = setup_stmt
        # Init MemstoreManager() once for first root SetupTask
        self._memstore_manager = MemstoreManager() if memstore_manager is None else memstore_manager
        self._task_id = task_id
        self._properties = properties
        self._test_mode = test_mode
        self._test_result_storage = test_result_storage
        self._runtime_environment = runtime_environment
        self._ray_debug = ray_debug
        # Assign default setup config value
        self._use_mp = self._setup_stmt.use_mp
        self._default_separator = setup_stmt.default_separator or "|"
        self._default_locale = setup_stmt.default_locale or "en"
        self._default_dataset = setup_stmt.default_dataset or "US"
        self._default_variable_prefix = setup_stmt.default_variable_prefix or "__"
        self._default_variable_suffix = setup_stmt.default_variable_suffix or "__"

    def execute(self) -> None:
        # Init root context
        root_context = SetupContext(
            memstore_manager=self._memstore_manager,
            task_id=self._task_id,
            use_mp=self._use_mp,
            properties=self._properties,
            test_mode=self._test_mode,
            descriptor_dir=self._descriptor_dir,
            test_result_exporter=self._test_result_storage,
            default_separator=self._default_separator,
            default_locale=self._default_locale,
            default_dataset=self._default_dataset,
            num_process=self._setup_stmt.num_process,
            default_variable_prefix=self._default_variable_prefix,
            default_variable_suffix=self._default_variable_suffix,
            default_line_separator=self._setup_stmt.default_line_separator,
            default_source_scripted=self._setup_stmt.default_source_scripted,
            report_logging=self._setup_stmt.report_logging in (True, None),  # default value is True
            run_seed=RunSeed.create(self._setup_stmt.rng_seed),
            runtime_environment=self._runtime_environment,
            ray_debug=self._ray_debug,
        )

        self.execute_statements(self._setup_stmt, root_context)

    @staticmethod
    def execute_statements(setup_stmt: SetupStatement, root_context: SetupContext) -> None:
        try:
            for stmt in setup_stmt.sub_statements:
                if not isinstance(stmt, DatabaseStatement | MongoDBStatement):
                    SetupTask._bind_pending_clients(root_context)
                task = create_task(stmt, root_context)
                if isinstance(task, SetupSubTask | CommonSubTask):
                    task.execute(root_context)
                else:
                    raise TypeError(f"Unsupported setup task type: {type(task).__name__}")
        except BaseException:
            with suppress(BaseException):
                SetupTask._cleanup_owned_clients(root_context)
            raise
        SetupTask._cleanup_owned_clients(root_context)

    @staticmethod
    def _bind_pending_clients(context: SetupContext) -> None:
        for client_id, config in tuple(context._pending_client_configs.items()):
            if isinstance(config, RdbmsConnectionConfig):
                client = create_rdbms_client(config, context.task_id)
            elif isinstance(config, MongoDBConnectionConfig):
                client = create_mongodb_client(config)
            else:
                raise TypeError(f"Unsupported descriptor client config: {type(config).__name__}")
            context.record_descriptor_client(client_id, client, config)

    @staticmethod
    def _cleanup_owned_clients(context: SetupContext) -> None:
        first_error: BaseException | None = None
        for client in context.take_owned_descriptor_clients():
            try:
                dispose_client_engine(client)
            except BaseException as error:
                if first_error is None:
                    first_error = error
        if first_error is not None:
            raise first_error

    @staticmethod
    def execute_include(setup_stmt: SetupStatement, parent_context: SetupContext) -> None:
        """
        Execute include in <setup>
        :param setup_stmt:
        :param parent_context:
        :return:
        """
        # Use copy of parent_context as child_context
        root_context = SetupTask._copy_include_context(parent_context)

        # Update root_context with attributes defined in sub-setup statement
        root_context.update_with_stmt(setup_stmt)

        SetupTask.execute_statements(setup_stmt, root_context)

    @staticmethod
    def _copy_include_context(parent_context: SetupContext) -> SetupContext:
        descriptor_clients = tuple(
            (token, client, config)
            for token, (client_ref, config) in enumerate(parent_context._descriptor_client_history)
            if (client := client_ref()) is not None
        )
        memo: dict[int, object] = {
            id(parent_context._descriptor_client_history): parent_context._descriptor_client_history
        }
        clone_by_token: dict[int, RegisteredClient] = {}
        for token, client, _config in descriptor_clients:
            clone = clone_client_for_include(client)
            memo[id(client)] = clone
            clone_by_token[token] = clone
        descriptor_ids = {id(client) for _token, client, _config in descriptor_clients}
        for client in parent_context.clients.values():
            if id(client) not in descriptor_ids:
                memo[id(client)] = client
        child = copy.deepcopy(parent_context, memo)
        token_map: dict[int, int] = {}
        for token, _client, config in descriptor_clients:
            clone = clone_by_token[token]
            token_map[token] = child._record_descriptor_reference(clone, config)
        child._descriptor_client_bindings = {
            client_id: token_map[token]
            for client_id, token in parent_context._descriptor_client_bindings.items()
        }
        return child
