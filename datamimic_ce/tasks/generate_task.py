# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
import csv
import json
import math
import multiprocessing
import os
import shutil
import time
from collections import OrderedDict
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

import dill  # type: ignore
import ray
import xmltodict

from datamimic_ce.clients.database_client import DatabaseClient
from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.constants.exporter_constants import EXPORTER_TEST_RESULT_EXPORTER
from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.data_sources.data_source_util import DataSourceUtil
from datamimic_ce.exporters.mongodb_exporter import MongoDBExporter
from datamimic_ce.logger import logger
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.key_statement import KeyStatement
from datamimic_ce.statements.setup_statement import SetupStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.tasks.task import CommonSubTask
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil
from datamimic_ce.utils.in_memory_cache_util import InMemoryCache
from datamimic_ce.utils.multiprocessing_page_info import MultiprocessingPageInfo

ray.init(ignore_reinit_error=True)


def _geniter_single_process_generate(context: SetupContext | GenIterContext, stmt: GenerateStatement, page_start: int,
                                     page_end: int) -> dict[str, list]:
    """
    (IMPORTANT: Only to be used as multiprocessing function) Generate product in each single process.

    :param args: Tuple containing context, statement, and index range.
    :return: Dictionary with generated products.
    """

    # Parse args
    root_context: SetupContext = context.root

    # Determine number of data to be processed
    processed_data_count = page_end - page_start
    pagination = DataSourcePagination(skip=page_start, limit=processed_data_count)

    # Prepare loaded datasource pagination
    load_start_idx = page_start
    load_end_idx = page_end
    load_pagination: DataSourcePagination | None = pagination

    # Extract converter list
    task_util_cls = root_context.class_factory_util.get_task_util_cls()
    converter_list = task_util_cls.create_converter_list(context, stmt.converter)

    # 1: Build sub-tasks in GenIterStatement
    tasks = [
        task_util_cls.get_task_by_statement(root_context, child_stmt, pagination) for child_stmt in stmt.sub_statements
    ]

    # 2: Load data source
    source_str = stmt.source
    source_scripted = (
        stmt.source_script if stmt.source_script is not None else bool(root_context.default_source_scripted)
    )
    separator = stmt.separator or root_context.default_separator
    is_random_distribution = stmt.distribution in ("random", None)
    if is_random_distribution:
        # Use task_id as seed for random distribution
        # Don't use pagination for random distribution to load all data before shuffle
        load_start_idx = None
        load_end_idx = None
        load_pagination = None
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

    if is_random_distribution:
        seed = root_context.get_distribution_seed()
        # Use original pagination for shuffling
        source_data = DataSourceUtil.get_shuffled_data_with_cyclic(source_data, pagination, stmt.cyclic, seed)

    # Keep current product and sub <generate> product in product_holder on non low memory mode
    product_holder: dict[str, list] = {}
    # Store temp result
    result = []

    # 3: Modify data
    for idx in range(processed_data_count):
        # Create sub-context for each product creation
        ctx = GenIterContext(context, stmt.name)

        # Set current product to the product from data source if building from datasource
        if build_from_source:
            if idx >= len(source_data):
                break
            ctx.current_product = copy.deepcopy(source_data[idx])
        try:
            # Execute sub-tasks
            from datamimic_ce.tasks.condition_task import ConditionTask

            for task in tasks:
                # Add sub generate product to current product_holder
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
            # Post convert product
            for converter in converter_list:
                ctx.current_product = converter.convert(ctx.current_product)

            # Evaluate source script after executing sub-tasks
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

    product_holder[stmt.full_name] = result
    return product_holder


def _consume_outermost_gen_stmt_by_page(
        stmt: GenerateStatement,
        context: Context,
        result_dict: dict,
        page_info: MultiprocessingPageInfo,
        is_last_page: bool,
) -> None:
    """
    Consume result_dict returned by outermost gen_stmt.

    :param stmt: GenerateStatement instance.
    :param context: Context instance.
    :param result_dict: Generated product data.
    :param page_info: Tuple containing page information.
    :return: None
    """
    report_logging = False

    # Create a dictionary to track start times for each statement
    if not hasattr(context, "_statement_start_times"):
        context._statement_start_times = {}

    # Initialize start times for statements if this is the first page
    if page_info.page_idx == 0:  # Check if this is the first page
        for stmt_full_name in result_dict:
            context._statement_start_times[stmt_full_name] = time.time()

    with gen_timer("export", report_logging, stmt.full_name) as timer_result:
        timer_result["records_count"] = len(result_dict.get(stmt.full_name, []))

        consumed_result = result_dict

        for stmt_full_name, result in consumed_result.items():
            # Retrieve GenerateStatement using fullname
            sub_stmt = stmt.retrieve_sub_statement_by_fullname(stmt_full_name)
            if sub_stmt is None:
                raise ValueError(f"Cannot find element <generate> '{stmt_full_name}'")
            context.root.class_factory_util.get_task_util_cls().consume_product_by_page(
                root_context=context.root,
                stmt=sub_stmt,
                xml_result=result,
                page_info=page_info,
            )
            if is_last_page:
                _finalize_and_export_consumers(context, sub_stmt)


def _finalize_and_export_consumers(context: Context, stmt: GenerateStatement) -> None:
    """
    Finalize chunks and export data for all consumers that require it.

    :param context: Context instance.
    :param stmt: GenerateStatement instance.
    :return: None
    """
    # TODO: manage client life cycle
    if hasattr(context.root, "_task_exporters"):
        # Find all exporters for this statement
        cache_key_prefix = f"{context.root.task_id}_{stmt.name}_"
        relevant_exporters = [
            exporters
            for cache_key, exporters in context.root.task_exporters.items()
            if cache_key.startswith(cache_key_prefix)
        ]

        for exporter_set in relevant_exporters:
            # Combine all exporters that need finalization
            all_exporters = [consumer for consumer, _ in exporter_set["with_operation"]] + exporter_set[
                "without_operation"
            ]
            for consumer in all_exporters:
                try:
                    if hasattr(consumer, "finalize_chunks"):
                        consumer.finalize_chunks()
                    if hasattr(consumer, "upload_to_storage"):
                        consumer.upload_to_storage(
                            bucket=stmt.bucket or stmt.container, name=f"{context.root.task_id}/{stmt.name}"
                        )
                    if hasattr(consumer, "save_exported_result"):
                        consumer.save_exported_result()

                    # Only clean up on outermost generate task
                    if isinstance(context, SetupContext) and hasattr(consumer, "cleanup"):
                        consumer.cleanup()

                except Exception as e:
                    logger.error(f"Error finalizing consumer {type(consumer).__name__}: {str(e)}")
                    raise

        # Clear the cache after finalization
        context.root._task_exporters = {}


@contextmanager
def gen_timer(process: Literal["generate", "export", "process"], report_logging: bool, product_name: str):
    """
    Timer for generate and consume process.

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

        count = self._statement.get_int_count(context)

        # Set length of data source if count is not defined
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

    def execute(self, context: SetupContext | GenIterContext) -> dict[str, list] | None:
        """
        Execute generate task. If gen_stmt is inner, return generated product; otherwise, consume them.

        :param context: Context instance.
        :return: Generated product data or None.
        """
        try:
            # Pre-execute sub-tasks
            self.pre_execute(context)

            # Determine count of generate process
            count = self._determine_count(context)

            # Early return if count is 0
            if count == 0:
                return {self.statement.full_name: []}

            # Calculate page size for processing by page
            page_size = self._calculate_default_page_size(count)

            # Determine number of Ray workers
            num_workers = int(self.statement.num_process or context.root.num_process or 1)

            # Determine chunk size for each worker
            chunk_size = math.ceil(count / num_workers)

            # Execute generate task using Ray
            workers = [GenerateWorker.remote() for w in range(num_workers)]
            chunks = [(i * chunk_size, min((i + 1) * chunk_size, count)) for i in range(num_workers)]

            futures = []
            for worker, (start, end) in zip(workers, chunks, strict=True):
                logger.info(f"Generating chunk {start}-{end} with page size {page_size}")
                context_copy = copy.deepcopy(context)
                futures.append(worker.generate_by_chunk.remote(context_copy, self._statement, start, end, page_size))

            results = ray.get(futures)

            return results

        finally:
            # Clean temp directory on outermost gen_stmt
            for temp_dir in context.descriptor_dir.glob(f"temp_result_{context.task_id}*"):
                shutil.rmtree(temp_dir)

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


@ray.remote
class GenerateWorker:
    @staticmethod
    def generate_by_chunk(context: SetupContext | GenIterContext, stmt: GenerateStatement, chunk_start: int,
                          chunk_end: int, page_size: int) -> dict:
        # Determine chunk data range, like (0, 1000), (1000, 2000), etc.
        index_chunk = [(i, min(i + page_size, chunk_end)) for i in range(chunk_start, chunk_end, page_size)]

        # Check if product result should be returned for test mode or memstore consumers
        return_product_result = context.test_mode or any(
            [context.memstore_manager.contain(consumer_str) for consumer_str in stmt.targets]
        )
        result: dict = {}

        non_lazy_exporter = []

        # Generate and consume product by page
        for page_idx, index_tuple in enumerate(index_chunk):
            # TODO: fulfill args
            page_start, page_end = index_tuple
            result_dict = _geniter_single_process_generate(context, stmt, page_start, page_end)
            for exporter in non_lazy_exporter:
                exporter.consume(result_dict)

            # Collect result for later capture
            if return_product_result:
                for key, value in result_dict.items():
                    result[key] = result.get(key, []) + value

            # Execute lazy exporter if outermost gen_stmt
            if isinstance(context, SetupContext):
                # TODO: check if mp_idx and mp_chunk_size is necessary for MultiprocessingPageInfo
                page_info = MultiprocessingPageInfo(None, None, page_idx, len(index_chunk))
                _consume_outermost_gen_stmt_by_page(stmt, context, result, page_info, is_last_page=page_idx == len(index_chunk) - 1)

        # Return results if inner gen_stmt
        if isinstance(context, GenIterContext):
            return result

        return {}