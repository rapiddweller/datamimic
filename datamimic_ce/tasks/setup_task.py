# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
from pathlib import Path

from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.exporters.test_result_exporter import TestResultExporter
from datamimic_ce.product_storage.memstore_manager import MemstoreManager
from datamimic_ce.statements.setup_statement import SetupStatement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class SetupTask:
    def __init__(
        self,
        setup_stmt: SetupStatement,
        memstore_manager: MemstoreManager | None,
        task_id: str,
        properties: dict | None,
        test_mode: bool,
        test_result_storage: TestResultExporter | None,
        descriptor_dir: Path,
        class_factory_util: BaseClassFactoryUtil,
    ):
        self._descriptor_dir = descriptor_dir
        self._setup_stmt = setup_stmt
        # Init MemstoreManager() once for first root SetupTask
        self._memstore_manager = MemstoreManager() if memstore_manager is None else memstore_manager
        self._task_id = task_id
        self._properties = properties
        self._test_mode = test_mode
        self._test_result_storage = test_result_storage
        # Assign default setup config value
        self._use_mp = self._setup_stmt.use_mp
        self._default_separator = setup_stmt.default_separator or "|"
        self._default_locale = setup_stmt.default_locale or "en"
        self._default_dataset = setup_stmt.default_dataset or "US"
        self._default_variable_prefix = setup_stmt.default_variable_prefix or "__"
        self._default_variable_suffix = setup_stmt.default_variable_suffix or "__"
        self._class_factory_util = class_factory_util

    def execute(self) -> None:
        # Init root context
        root_context = SetupContext(
            class_factory_util=self._class_factory_util,
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
        )

        task_util_cls = self._class_factory_util.get_task_util_cls()
        for stmt in self._setup_stmt.sub_statements:
            task = task_util_cls.get_task_by_statement(root_context, stmt)
            task.execute(root_context)

    @staticmethod
    def execute_include(setup_stmt: SetupStatement, parent_context: SetupContext) -> None:
        """
        Execute include in <setup>
        :param setup_stmt:
        :param parent_context:
        :return:
        """
        # Use copy of parent_context as child_context
        root_context = copy.deepcopy(parent_context)

        # Update root_context with attributes defined in sub-setup statement
        root_context.update_with_stmt(setup_stmt)

        task_util_cls = parent_context.class_factory_util.get_task_util_cls()
        for stmt in setup_stmt.sub_statements:
            task = task_util_cls.get_task_by_statement(root_context, stmt)
            task.execute(root_context)
