# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
import math
import shutil
import time
from contextlib import contextmanager
from typing import Literal

import dill  # type: ignore
import ray

from datamimic_ce.clients.database_client import DatabaseClient
from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.data_sources.data_source_util import DataSourceUtil
from datamimic_ce.exporters.exporter_state_manager import ExporterStateManager
from datamimic_ce.logger import logger
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.key_statement import KeyStatement
from datamimic_ce.statements.setup_statement import SetupStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.tasks.task import CommonSubTask
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


def generate_product_by_page_in_single_process(
        context: SetupContext | GenIterContext, stmt: GenerateStatement, page_start: int, page_end: int, worker_id: int
) -> dict[str, list]:
    """
    (IMPORTANT: Only to be used as Ray multiprocessing function)
    This function is used to generate data for a single process, includes steps:
    1. Build sub-tasks in GenIterStatement
    2. Load data source (if any)
    3. Modify/Generate data by executing sub-tasks

    :return: Dictionary with generated products.
    """
    root_context: SetupContext = context.root

    # Determine number of data to be processed
    processed_data_count = page_end - page_start
    pagination = DataSourcePagination(skip=page_start, limit=processed_data_count)

    # Determined page of data source to load
    # If distribution is random, load all data before shuffle, which means no pagination (or, pagination=None)
    # If distribution is not random, load data by pagination
    is_random_distribution = stmt.distribution in ("random", None)
    if is_random_distribution:
        # Use task_id as seed for random distribution
        # Don't use pagination for random distribution to load all data before shuffle
        load_start_idx = None
        load_end_idx = None
        load_pagination: DataSourcePagination | None = None
    else:
        load_start_idx = page_start
        load_end_idx = page_end
        load_pagination = pagination

    # Extract converter list for post-processing
    task_util_cls = root_context.class_factory_util.get_task_util_cls()
    converter_list = task_util_cls.create_converter_list(context, stmt.converter)

    # 1: Build sub-tasks in GenIterStatement
    tasks = [
        task_util_cls.get_task_by_statement(root_context, child_stmt, pagination) for child_stmt in stmt.sub_statements
    ]

    # 2: Load data source from file, database, memory, Kafka, etc.
    source_str = stmt.source
    source_scripted = (
        stmt.source_script if stmt.source_script is not None else bool(root_context.default_source_scripted)
    )
    separator = stmt.separator or root_context.default_separator

    source_data, build_from_source = context.root.class_factory_util.get_task_util_cls().gen_task_load_data_from_source(
        context,
        stmt,
        source_str,
        separator,
        source_scripted,
        processed_data_count,
        load_start_idx,
        load_end_idx,
        load_pagination,
    )

    # Shuffle source data if distribution is random
    if is_random_distribution:
        seed = root_context.get_distribution_seed()
        # Use original pagination for shuffling
        source_data = DataSourceUtil.get_shuffled_data_with_cyclic(source_data, pagination, stmt.cyclic, seed)

    # Store temp result
    product_holder: dict[str, list] = {}
    result = []

    # 3: Modify/Generate data by executing sub-tasks
    for idx in range(processed_data_count):
        # Create sub-context for each product record creation
        ctx = GenIterContext(context, stmt.name)
        # Get current worker_id from outermost gen_stmt
        ctx.worker_id = worker_id

        # Set current product to the product from data source if building from datasource
        if build_from_source:
            if idx >= len(source_data):
                break
            ctx.current_product = copy.deepcopy(source_data[idx])

        try:
            # Start executing sub-tasks
            from datamimic_ce.tasks.condition_task import ConditionTask

            for task in tasks:
                # Collect product from sub-generate task and add into product_holder
                if isinstance(task, GenerateTask | ConditionTask):
                    # Execute sub generate task
                    sub_gen_result = task.execute(ctx)
                    if sub_gen_result:
                        for key, value in sub_gen_result.items():
                            # Store product for later export
                            product_holder[key] = product_holder.get(key, []) + value
                            # Store temp product in context for later evaluate
                            inner_generate_key = key.split("|", 1)[-1].strip()
                            ctx.current_variables[inner_generate_key] = value
                else:
                    task.execute(ctx)

            # Post-process product by applying converters
            for converter in converter_list:
                ctx.current_product = converter.convert(ctx.current_product)

            # Lazily evaluate source script after executing sub-tasks
            if source_scripted:
                # Evaluate python expression in source
                prefix = stmt.variable_prefix or root_context.default_variable_prefix
                suffix = stmt.variable_suffix or root_context.default_variable_suffix
                ctx.current_product = task_util_cls.evaluate_file_script_template(
                    ctx=ctx, datas=ctx.current_product, prefix=prefix, suffix=suffix
                )

            result.append(ctx.current_product)
        except StopIteration:
            # Stop generating data if one of datasource reach the end
            logger.info(
                f"Data generator sub-task {task.__class__.__name__} '{task.statement.name}' has already reached the end"
            )
            break

    # 4. Return product for later export
    product_holder[stmt.full_name] = result
    return product_holder


@contextmanager
def gen_timer(process: Literal["generate", "export", "process"], report_logging: bool, product_name: str):
    """
    Timer for generate and export process.

    :param process: Type of process ('generate', 'consume', 'process').
    :param report_logging: Whether to log the timing information.
    :param product_name: Name of the product being processed.
    :return: Context manager.
    """
    timer_result: dict = {}
    # Ignore timer if report_logging is False
    if not report_logging:
        yield timer_result
        return
    start_time = time.time()
    try:
        yield timer_result
    finally:
        records_count = timer_result.get("records_count", 0)
        end_time = time.time()
        elapsed_time = end_time - start_time
        timer_result["elapsed_time"] = elapsed_time
        match process:
            case "generate":
                process_name = "Generating"
            case "export":
                process_name = "Exporting"
            case _:
                process_name = "Generating and exporting"
        logger.info(
            f"{process_name} {records_count:,} records '{product_name}' took {round(elapsed_time, 5)} seconds "
            f"({int(records_count / elapsed_time):,} records/second)"
            if elapsed_time > 0
            else "N/A records/second"
        )


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

    def _determine_count(self, context: Context) -> int:
        """
        Determine the count of records to generate.

        :param context: Context instance.
        :return: Number of records to generate.
        """
        root_context: SetupContext = context.root

        # Scan statements to check data source length (and cyclic)
        self._scan_data_source(root_context, self._statement)

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
    def _scan_data_source(ctx: SetupContext, statement: Statement) -> None:
        """
        Scan data source and set data source length.

        :param ctx: SetupContext instance.
        :param statement: Statement instance.
        :return: None
        """
        # 1. Scan statement
        ctx.class_factory_util.get_datasource_util_cls().set_data_source_length(ctx, statement)
        # 2. Scan sub-statement
        if isinstance(statement, CompositeStatement):
            for child_stmt in statement.sub_statements:
                GenerateTask._scan_data_source(ctx, child_stmt)

    @staticmethod
    def determine_num_workers(context: GenIterContext | SetupContext, stmt: GenerateStatement) -> int:
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

    def execute(self, context: SetupContext | GenIterContext) -> dict[str, list] | None:
        """
        Execute generate task.
        First, generate data and export data by page.
        Second:
        - If gen_stmt is inner, return generated product to outermost gen_stmt.
        - Otherwise, export gathered product with lazy exporter on outermost gen_stmt.

        :param context: Context instance.
        :return: Generated product data or None.
        """
        try:
            # Pre-execute sub-tasks before generating any data
            self.pre_execute(context)

            # Determine count of generate process
            count = self._determine_count(context)

            # Early return if count is 0
            if count == 0:
                return {self.statement.full_name: []}

            # Calculate page size for processing by page
            page_size = self._calculate_default_page_size(count)

            # Determine number of Ray workers for multiprocessing
            num_workers = self.determine_num_workers(context, self.statement)

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

                # Create Ray workers
                workers = [RayGenerateWorker.remote() for _ in
                           range(num_workers)]  # type: ignore[attr-defined]

                # Execute generate task using Ray
                futures = []
                for worker_id, worker, (chunk_start, chunk_end) in zip(
                        range(1, num_workers + 1), workers, chunks, strict=True
                ):
                    logger.info(f"Generating chunk {chunk_start}-{chunk_end} with page size {page_size}")
                    # Generate and export data by page
                    futures.append(
                        worker.generate_and_export_data_by_chunk.remote(
                            copied_context, self._statement, worker_id, chunk_start, chunk_end, page_size
                        )
                    )

                # Gather result from Ray workers
                ray_result = ray.get(futures)

                # Merge result from all workers by product name
                merged_result: dict[str, list] = {}
                for result in ray_result:
                    for product_name, product_data_list in result.items():
                        merged_result[product_name] = merged_result.get(product_name, []) + product_data_list
            # Execute generate task by page in single process
            else:
                # If inner gen_stmt, pass worker_id from outermost gen_stmt to inner gen_stmt
                worker_id = context.worker_id if isinstance(context, GenIterContext) else 1
                merged_result = GenerateWorker.generate_and_export_data_by_chunk(
                    context, self._statement, worker_id, 0, count, page_size
                )

            # At the end of OUTERMOST gen_stmt:
            # - export gathered product with LAZY exporters, such as TestResultExporter, MemstoreExporter,...
            # - gather and upload ARTIFACT exporters, such as TXT, JSON,... then clean temp directory
            if isinstance(context, SetupContext):
                # Determine lazy exporters
                lazy_exporters = []
                if context.test_mode:
                    lazy_exporters.append(context.root.test_result_exporter)
                for exporter_str in self.statement.targets:
                    if context.memstore_manager.contain(exporter_str):
                        lazy_exporters.append(context.memstore_manager.get_memstore(exporter_str))
                # Export gathered product with lazy exporters
                for exporter in lazy_exporters:
                    for product_name, product_records in merged_result.items():
                        exporter.consume((product_name, product_records))

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

    @staticmethod
    def finalize_temp_files_chunks(context: SetupContext, stmt: GenerateStatement):
        """
        Finalize temp files chunks (writing end of file).
        """
        # Determine number of Ray workers, used to determined chunk directory name
        num_workers = GenerateTask.determine_num_workers(context, stmt)

        # Get ARTIFACT exporters from statement
        exporter_list = context.root.class_factory_util.get_exporter_util().get_all_exporter(context, stmt,
                                                                                             list(stmt.targets))
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
        exporters_list = (
            context.root.class_factory_util.get_exporter_util().get_all_exporter(context, stmt, list(stmt.targets))
        )
        # Export artifact files of current statement
        for exporter in exporters_list:
            if hasattr(exporter, "save_exported_result"):
                exporter.save_exported_result()

        # Export artifact files of sub-gen_stmts
        for sub_stmt in stmt.sub_statements:
            if isinstance(sub_stmt, GenerateStatement):
                GenerateTask.export_artifact_files(context, sub_stmt)

    @staticmethod
    def convert_xml_dict_to_json_dict(xml_dict: dict):
        """
        Convert XML dict with #text and @attribute to pure JSON dict.

        :param xml_dict: XML dictionary.
        :return: JSON dictionary.
        """
        if "#text" in xml_dict:
            return xml_dict["#text"]
        res = {}
        for key, value in xml_dict.items():
            if not key.startswith("@"):
                if isinstance(value, dict):
                    res[key] = GenerateTask.convert_xml_dict_to_json_dict(value)
                elif isinstance(value, list):
                    res[key] = [
                        GenerateTask.convert_xml_dict_to_json_dict(v) if isinstance(v, dict) else v for v in value
                    ]
                else:
                    res[key] = value
        return res

    @staticmethod
    def _get_chunk_indices(chunk_size: int, data_count: int) -> list:
        """
        Create list of chunk indices based on chunk size and required data count.

        :param chunk_size: Size of each chunk.
        :param data_count: Total data count.
        :return: List of tuples representing chunk indices.
        """
        return [(i, min(i + chunk_size, data_count)) for i in range(0, data_count, chunk_size)]

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

    @staticmethod
    def execute_include(setup_stmt: SetupStatement, parent_context: GenIterContext) -> None:
        """
        Execute include XML model inside <generate>
        :param setup_stmt:
        :param parent_context:
        :return:
        """
        # Use copy of parent_context as child_context
        root_context = copy.deepcopy(parent_context.root)

        # Update root_context with attributes defined in sub-setup statement
        root_context.update_with_stmt(setup_stmt)
        # Update root_context with parent_context variables and current_product
        root_context.global_variables.update(parent_context.current_variables)
        root_context.global_variables.update(parent_context.current_product)

        task_util_cls = root_context.class_factory_util.get_task_util_cls()
        for stmt in setup_stmt.sub_statements:
            task = task_util_cls.get_task_by_statement(root_context, stmt)
            task.execute(root_context)


class GenerateWorker:
    """
    Worker class for generating data based on the GenerateStatement.
    Use this class for single process execution to avoid Ray overhead of creating too many single Ray workers.
    """

    @staticmethod
    def generate_and_export_data_by_chunk(
            context: SetupContext | GenIterContext,
            stmt: GenerateStatement,
            worker_id: int,
            chunk_start: int,
            chunk_end: int,
            page_size: int,
    ) -> dict:
        """
        Generate and export data by page in a single process.

        :param context: SetupContext or GenIterContext instance.
        :param stmt: GenerateStatement instance.
        :param worker_id: Worker ID.
        :param chunk_start: Start index of chunk.
        :param chunk_end: End index of chunk.
        :param page_size: Size of each page.
        """

        # Determine chunk data range, like (0, 1000), (1000, 2000), etc.
        index_chunk = [(i, min(i + page_size, chunk_end)) for i in range(chunk_start, chunk_end, page_size)]

        # Check if product result should be returned for test mode or memstore exporter
        return_product_result = context.root.test_mode or any(
            [context.root.memstore_manager.contain(exporter_str) for exporter_str in stmt.targets]
        )
        result: dict = {}

        # Initialize ARTIFACT exporter state manager for each worker
        exporter_state_manager = ExporterStateManager(worker_id)

        # Create and cache exporters for each worker
        exporters_set = stmt.targets.copy()
        root_context = context.root

        # Create exporters with operations
        (
            consumers_with_operation,
            consumers_without_operation,
        ) = root_context.class_factory_util.get_exporter_util().create_exporter_list(
            setup_context=root_context,
            stmt=stmt,
            targets=list(exporters_set),
        )

        # Cache the exporters
        root_context.task_exporters[stmt.full_name] = {
            "with_operation": consumers_with_operation,
            "without_operation": consumers_without_operation,
            "page_count": 0,  # Track number of pages processed
        }

        # Generate and consume product by page
        for index_tuple in index_chunk:
            page_start, page_end = index_tuple
            # Generate product
            result_dict = generate_product_by_page_in_single_process(context, stmt, page_start, page_end, worker_id)

            # Export product by page
            context.root.class_factory_util.get_task_util_cls().export_product_by_page(
                context.root, stmt, result_dict, exporter_state_manager
            )

            # Collect result for later capturing
            if return_product_result:
                for key, value in result_dict.items():
                    result[key] = result.get(key, []) + value

        # Check if product result should be returned for test mode or memstore exporter
        has_memstore_exporter = any(
            [
                ("." not in exporter_str)
                and ("(" not in exporter_str)
                and context.root.memstore_manager.contain(exporter_str)
                for exporter_str in stmt.targets
            ]
        )

        # Return results if inner gen_stmt or test mode or memstore exporter
        if isinstance(context, GenIterContext) or context.root.test_mode or has_memstore_exporter:
            return result

        return {}


@ray.remote(enable_task_events=False)
class RayGenerateWorker(GenerateWorker):
    """
    Ray worker class for generating data based on the GenerateStatement.
    """

    @staticmethod
    def generate_and_export_data_by_chunk(
            context: SetupContext | GenIterContext,
            stmt: GenerateStatement,
            worker_id: int,
            chunk_start: int,
            chunk_end: int,
            page_size: int,
    ) -> dict:
        # Deserialize multiprocessing arguments
        context.root.namespace.update(dill.loads(context.root.namespace_functions))
        context.root.generators = dill.loads(context.root.generators)

        return GenerateWorker.generate_and_export_data_by_chunk(context, stmt, worker_id, chunk_start, chunk_end,
                                                                page_size)
