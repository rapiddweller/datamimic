# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
import math
import shutil

import dill  # type: ignore
import ray

from datamimic_ce.clients.database_client import DatabaseClient
from datamimic_ce.config import settings
from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.logger import logger
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.key_statement import KeyStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.tasks.task import CommonSubTask
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil
from datamimic_ce.utils.logging_util import gen_timer


class GenerateTask(CommonSubTask):
    """
    Task class for generating data based on the GenerateStatement.

    """

    def __init__(self, statement: GenerateStatement, class_factory_util: BaseClassFactoryUtil):
        self._statement = statement
        self._class_factory_util = class_factory_util

    @property
    def statement(self) -> GenerateStatement:
        return self._statement

    def _determine_count(self, context: SetupContext | GenIterContext) -> int:
        """
        Determine the count of records to generate.

        :param context: Context instance.
        :return: Number of records to generate.
        """
        root_context: SetupContext = context.root

        # Scan statements to check data source length (and cyclic)
        # Only scan on outermost gen_stmt
        self._scan_data_source(context, self._statement)

        # Get count from statement
        count = self._statement.get_int_count(context)

        # Set length of data source if count is not defined explicitly in statement
        if count is None:
            # Check if "selector" is defined with "source"
            if self.statement.selector:
                # Evaluate script selector
                from datamimic_ce.tasks.task_util import TaskUtil

                selector = TaskUtil.evaluate_selector_script(context=context, stmt=self._statement)
                client = (
                    root_context.get_client_by_id(self.statement.source) if self.statement.source is not None else None
                )
                if isinstance(client, DatabaseClient):
                    count = client.count_query_length(selector)
                else:
                    raise ValueError(
                        "Using selector without count only supports DatabaseClient (MongoDB, Relational Database)"
                    )
            else:
                count = root_context.data_source_len[self.statement.full_name]

        # Check if there is a special consumer (e.g., mongodb_upsert)
        if count == 0 and self.statement.contain_mongodb_upsert(root_context):
            # Upsert one collection when no record found by query
            count = 1

        return count

    def _calculate_default_page_size(self, entity_count: int) -> int:
        """
        Calculate default page size for processing by page.

        :param entity_count: Total number of entities.
        :return: Page size.
        """
        stmt_page_size = self.statement.page_size
        # Return page size if defined in statement explicitly
        if stmt_page_size is not None:
            logger.debug(f"Using page size {stmt_page_size:,} defined in statement")
            if stmt_page_size < 100:
                logger.warning(f"Using low page size {stmt_page_size} (< 100) may cause performance issues")
            return max(1, stmt_page_size)

        if entity_count == 0:
            return 1

        default_page_size = 10000 if entity_count > 10000 else entity_count

        # Reduce default page size if column count > 25
        col_count = len(self.statement.sub_statements)
        if col_count > 25:
            reduction_factor = col_count / 25
            default_page_size = int(default_page_size / reduction_factor)

        # Log calculated default page size
        default_page_size = max(1, default_page_size)
        logger.info(f"Using default page size {default_page_size} for processing by page")

        return default_page_size

    @staticmethod
    def _scan_data_source(ctx: SetupContext | GenIterContext, statement: Statement) -> None:
        """
        Scan data source and set data source length.

        :param ctx: SetupContext instance.
        :param statement: Statement instance.
        :return: None
        """
        # 1. Scan statement
        ctx.root.class_factory_util.get_datasource_registry_cls().set_data_source_length(ctx, statement)
        # 2. Scan sub-statement
        if isinstance(statement, CompositeStatement):
            for child_stmt in statement.sub_statements:
                GenerateTask._scan_data_source(ctx, child_stmt)

    @staticmethod
    def _determine_num_workers(context: GenIterContext | SetupContext, stmt: GenerateStatement) -> int:
        """
        Determine number of Ray workers for multiprocessing. Default to 1 if not specified.
        Do not apply multiprocessing (return 1) if:
        - There is a delete operation.
        - Statement is inner gen_stmt.
        """
        # Do not apply multiprocessing for inner gen_stmt
        if isinstance(context, GenIterContext):
            return 1

        # If there is a delete operation, do not apply multiprocessing
        for exporter_str in stmt.targets:
            if ".delete" in exporter_str:
                return 1

        # Get number of workers from statement, setup context, or default to 1
        current_setup_context = context
        while not isinstance(current_setup_context, SetupContext):
            current_setup_context = current_setup_context.parent

        if stmt.num_process is not None:
            num_workers = stmt.num_process
        elif current_setup_context.num_process is not None:
            num_workers = current_setup_context.num_process
        else:
            num_workers = 1

        return num_workers

    def execute(
        self, context: SetupContext | GenIterContext, source_operation: dict | None = None
    ) -> dict[str, list] | None:
        """
        Execute generate task.
        First, generate data and export data by page.
        Second:
        - If gen_stmt is inner, return generated product to outermost gen_stmt.
        - Otherwise, export gathered product with lazy exporter on outermost gen_stmt.

        :param context: Context instance.
        :return: Generated product data or None.
        """
        with gen_timer("process", context.root.report_logging, self.statement.full_name) as timer_result:
            try:
                # Mark Ray initialization status for shutdown at the end of execution
                is_ray_initialized = False

                # Pre-execute sub-tasks before generating any data
                self.pre_execute(context)

                # Determine count of generate process
                count = self._determine_count(context)
                timer_result["records_count"] = count

                # Early return if count is 0
                if count == 0:
                    return {self.statement.full_name: []}

                # Calculate page size for processing by page
                page_size = self._calculate_default_page_size(count)

                # Determine number of Ray workers for multiprocessing
                num_workers = self._determine_num_workers(context, self.statement)

                # Execute generate task by page in multiprocessing
                if isinstance(context, SetupContext) and num_workers > 1:
                    # Serialize context for Ray multiprocessing
                    copied_context = copy.deepcopy(context)
                    ns_funcs = {k: v for k, v in copied_context.root.namespace.items() if callable(v)}
                    for func in ns_funcs:
                        copied_context.root.namespace.pop(func)
                    copied_context.root.namespace_functions = dill.dumps(ns_funcs)
                    copied_context.root.generators = dill.dumps(copied_context.root.generators)

                    # Determine chunk data indices based on chunk size and required data count
                    # then populate to workers, such as (0, 1000), (1000, 2000), etc.
                    chunk_size = math.ceil(count / num_workers)
                    chunks = [(i * chunk_size, min((i + 1) * chunk_size, count)) for i in range(num_workers)]
                    logger.info(f"Generating data by page in {num_workers} workers with chunks {chunks}")

                    # Determine multiprocessing platform and process data in parallel
                    mp_platform = self._statement.mp_platform or "multiprocessing"
                    if mp_platform == "multiprocessing":
                        from datamimic_ce.workers.multiprocessing_generate_worker import MultiprocessingGenerateWorker

                        mp_worker = MultiprocessingGenerateWorker()
                    elif mp_platform == "ray":
                        from datamimic_ce.workers.ray_generate_worker import RayGenerateWorker

                        mp_worker = RayGenerateWorker()  # type: ignore[assignment]
                        # Initialize Ray
                        ray.init(ignore_reinit_error=True, local_mode=settings.RAY_DEBUG, include_dashboard=False)
                        is_ray_initialized = True
                    else:
                        raise ValueError(
                            f"Multiprocessing platform '{mp_platform}' of <generate> '{self.statement.full_name}' "
                            f"is not supported"
                        )
                    # Execute generate task by page in multiprocessing using Ray or multiprocessing
                    merged_result = mp_worker.mp_process(
                        copied_context, self._statement, chunks, page_size, source_operation
                    )

                # Execute generate task by page in single process
                else:
                    # If inner gen_stmt, pass worker_id from outermost gen_stmt to inner gen_stmt
                    worker_id = context.worker_id if isinstance(context, GenIterContext) else 1
                    from datamimic_ce.workers.generate_worker import GenerateWorker

                    merged_result = GenerateWorker.generate_and_export_data_by_chunk(
                        context, self._statement, worker_id, 0, count, page_size, source_operation
                    )

                # At the end of OUTERMOST gen_stmt:
                # - export gathered product with LAZY exporters, such as TestResultExporter, MemstoreExporter,...
                # - gather and upload ARTIFACT exporters, such as TXT, JSON,... then clean temp directory
                if isinstance(context, SetupContext):
                    # Lazily export gathered product with lazy exporters
                    # Export TestResultExporter if in test mode
                    if context.test_mode:
                        test_result_exporter = context.root.test_result_exporter
                        for product_name, product_records in merged_result.items():
                            test_result_exporter.consume((product_name, product_records))
                    # Export memstore exporters
                    self.export_memstore(context, self.statement, merged_result)

                    # # Finalize chunks files (writing end of file)
                    self.finalize_temp_files_chunks(context, self.statement)

                    # Upload ARTIFACT files at the end of ALL chunks processes
                    self.export_artifact_files(context, self.statement)

                return merged_result

            finally:
                # Clean temp directory on outermost gen_stmt
                if isinstance(context, SetupContext):
                    for temp_dir in context.descriptor_dir.glob(f"temp_result_{context.task_id}*"):
                        shutil.rmtree(temp_dir)
                # Shutdown Ray if initialized
                if is_ray_initialized:
                    ray.shutdown()

    @staticmethod
    def export_memstore(setup_context: SetupContext, current_stmt: GenerateStatement, merged_result: dict[str, list]):
        for current_exporter_str in current_stmt.targets:
            if setup_context.memstore_manager.contain(current_exporter_str):
                setup_context.memstore_manager.get_memstore(current_exporter_str).consume(
                    (current_stmt.name, merged_result[current_stmt.full_name])
                )
                # Export to memstore only once
                break
        for sub_stmt in current_stmt.sub_statements:
            if isinstance(sub_stmt, GenerateStatement):
                GenerateTask.export_memstore(setup_context, sub_stmt, merged_result)

    @staticmethod
    def finalize_temp_files_chunks(context: SetupContext, stmt: GenerateStatement):
        """
        Finalize temp files chunks (writing end of file).
        """
        # Determine number of Ray workers, used to determined chunk directory name
        num_workers = GenerateTask._determine_num_workers(context, stmt)

        # Get ARTIFACT exporters from statement
        exporter_list = context.root.class_factory_util.get_exporter_util().get_all_exporter(
            context, stmt, list(stmt.targets)
        )
        # Finalize chunks files (writing end of file)
        for exporter in exporter_list:
            if hasattr(exporter, "finalize_chunks"):
                for worker_id in range(1, num_workers + 1):
                    exporter.finalize_chunks(worker_id)

        # Finalize temp files chunks of sub-gen_stmts
        for sub_stmt in stmt.sub_statements:
            if isinstance(sub_stmt, GenerateStatement):
                GenerateTask.finalize_temp_files_chunks(context, sub_stmt)

    @staticmethod
    def export_artifact_files(context: SetupContext, stmt: GenerateStatement):
        """
        Export artifact files to storage (Execute on outermost gen_stmt)
        """
        exporters_list = context.root.class_factory_util.get_exporter_util().get_all_exporter(
            context, stmt, list(stmt.targets)
        )
        # Export artifact files of current statement
        for exporter in exporters_list:
            if hasattr(exporter, "save_exported_result"):
                exporter.save_exported_result()
            if hasattr(exporter, "upload_to_storage"):
                exporter.upload_to_storage(stmt.bucket)

        # Export artifact files of sub-gen_stmts
        for sub_stmt in stmt.sub_statements:
            if isinstance(sub_stmt, GenerateStatement):
                GenerateTask.export_artifact_files(context, sub_stmt)

    def pre_execute(self, context: Context):
        """
        Pre-execute task in single process before multiprocessing execution.

        :param context: Context instance.
        :return: None
        """
        root_context = context.root
        task_util_cls = root_context.class_factory_util.get_task_util_cls()

        pre_tasks = [
            task_util_cls.get_task_by_statement(root_context, child_stmt, None)
            for child_stmt in self.statement.sub_statements
            if isinstance(child_stmt, KeyStatement)
        ]
        for task in pre_tasks:
            task.pre_execute(context)
