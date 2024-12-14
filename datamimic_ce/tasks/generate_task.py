# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
import csv
import json
import math
import os
import shutil
from pathlib import Path
from typing import Dict, Awaitable, Any

import ray
import xmltodict
import inspect

from datamimic_ce.clients.database_client import DatabaseClient
from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.exporters.mongodb_exporter import MongoDBExporter
from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.data_sources.data_source_util import DataSourceUtil
from datamimic_ce.logger import logger
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.key_statement import KeyStatement
from datamimic_ce.statements.setup_statement import SetupStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.tasks.task import Task
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil
from datamimic_ce.utils.in_memory_cache_util import InMemoryCache


def _finalize_and_export_consumers(context: Context, stmt: GenerateStatement) -> None:
    """
    Finalize chunks and export data for all consumers that require it.

    :param context: Context instance.
    :param stmt: GenerateStatement instance.
    :return: None
    """
    if hasattr(context.root, "_task_exporters"):
        # Find all exporters for this statement
        cache_key_prefix = f"{context.root.task_id}_{stmt.name}_"
        relevant_exporters = [
            exporters
            for cache_key, exporters in context.root._task_exporters.items()
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


@ray.remote
class GenerateWorker:
    """Worker class for generating data in parallel using Ray"""

    def __init__(self):
        self._initialized = False
        self.context = None

    def initialize(self, context: Context):
        """Initialize worker with context"""
        if not self._initialized:
            if isinstance(context, SetupContext):
                context = copy.deepcopy(context)

            # Initialize database clients
            for _, client in context.root.clients.items():
                if isinstance(client, RdbmsClient | MongoDBClient):
                    if isinstance(client, RdbmsClient):
                        client.initialize_engine()
                    elif isinstance(client, MongoDBClient):
                        client._create_connection()

            self.context = context
            self._initialized = True

    async def generate_chunk(
        self, context: Context, statement: GenerateStatement, start_idx: int, end_idx: int, page_size: int
    ) -> dict[str, list]:
        """Generate data for a chunk of records"""
        self.initialize(context)

        try:
            # Use root context's clients
            for client in self.context.root.clients.values():
                if isinstance(client, RdbmsClient | MongoDBClient):
                    if isinstance(client, RdbmsClient):
                        client.initialize_engine()
                    elif isinstance(client, MongoDBClient):
                        client._create_connection()

            result: dict[str, list] = {}
            current_start = start_idx

            while current_start < end_idx:
                current_end = min(current_start + page_size, end_idx)
                page_result = await _geniter_single_process_generate(
                    (self.context, statement, (current_start, current_end))
                )

                # Merge results
                for key, value in page_result.items():
                    if key not in result:
                        result[key] = []
                    result[key].extend(value)

                current_start = current_end

            return result

        finally:
            # Cleanup connections
            for client in self.context.clients.values():
                if hasattr(client, "cleanup"):
                    client.cleanup()


async def _geniter_single_process_generate(args: tuple) -> dict[str, list]:
    """Generate product in each process."""
    context: Context = args[0]
    root_context: SetupContext = context.root
    stmt: GenerateStatement = args[1]
    start_idx, end_idx = args[2]

    processed_data_count = end_idx - start_idx
    pagination = DataSourcePagination(skip=start_idx, limit=processed_data_count)

    # Extract converter list
    task_util_cls = root_context.class_factory_util.get_task_util_cls()
    converter_list = task_util_cls.create_converter_list(context, stmt.converter)

    # Build sub-tasks
    tasks = [
        task_util_cls.get_task_by_statement(root_context, child_stmt, pagination) for child_stmt in stmt.sub_statements
    ]

    # Load data source
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
        start_idx,
        end_idx,
        pagination,
    )

    # Store results
    product_holder: dict[str, list] = {}
    result = []

    # Generate data
    for idx in range(processed_data_count):
        ctx = GenIterContext(context, stmt.name)

        if build_from_source:
            if idx >= len(source_data):
                break
            ctx.current_product = copy.deepcopy(source_data[idx])

        try:
            # Execute sub-tasks
            from datamimic_ce.tasks.condition_task import ConditionTask

            for task in tasks:
                if isinstance(task, GenerateTask | ConditionTask):
                    sub_gen_result = task.execute(ctx)
                    if inspect.iscoroutine(sub_gen_result):
                        sub_gen_result = await sub_gen_result
                    if isinstance(sub_gen_result, dict):  # Add type check
                        for key, value in sub_gen_result.items():
                            product_holder[key] = product_holder.get(key, []) + value
                            inner_generate_key = key.split("|", 1)[-1].strip()
                            ctx.current_variables[inner_generate_key] = value
                else:
                    task.execute(ctx)

            # Post convert product
            for converter in converter_list:
                ctx.current_product = converter.convert(ctx.current_product)

            # Evaluate source script
            if source_scripted:
                prefix = stmt.variable_prefix or root_context.default_variable_prefix
                suffix = stmt.variable_suffix or root_context.default_variable_suffix
                ctx.current_product = task_util_cls.evaluate_file_script_template(
                    ctx=ctx, datas=ctx.current_product, prefix=prefix, suffix=suffix
                )

            result.append(ctx.current_product)

        except StopIteration:
            logger.info("Data generator sub-task reached the end")
            break

    product_holder[stmt.full_name] = result
    return product_holder


class GenerateTask(Task):
    """Task class for generating data based on the GenerateStatement using Ray for parallelization."""

    def __init__(self, statement: GenerateStatement, class_factory_util: BaseClassFactoryUtil):
        self._statement = statement
        self._class_factory_util = class_factory_util

        # Initialize Ray if not already initialized
        if not ray.is_initialized():
            ray.init()

        # Initialize database clients
        if hasattr(statement, "clients"):
            for client in statement.clients.values():
                if isinstance(client, RdbmsClient | MongoDBClient):
                    if isinstance(client, RdbmsClient):
                        client.initialize_engine()
                    elif isinstance(client, MongoDBClient):
                        client._create_connection()

    @property
    def statement(self) -> GenerateStatement:
        return self._statement

    def _determine_count(self, context: Context) -> int:
        """Determine the count of items to generate."""
        count = self.statement.get_int_count(context)
        if count is not None:
            return count

        if self.statement.selector:
            from datamimic_ce.tasks.task_util import TaskUtil

            client = context.root.get_client_by_id(self.statement.source)
            if not isinstance(client, DatabaseClient):
                raise ValueError("Using selector without count only supports DatabaseClient")

            # Evaluate selector with variables
            prefix = self.statement.variable_prefix or context.root.default_variable_prefix
            suffix = self.statement.variable_suffix or context.root.default_variable_suffix
            selector = TaskUtil.evaluate_variable_concat_prefix_suffix(context, self.statement.selector, prefix, suffix)
            return client.count_query_length(selector)

        return 0

    async def execute(self, context: Context) -> dict[str, list[Any]]:
        """Execute generate task.

        Args:
            context: The execution context

        Returns:
            A dictionary mapping full names to lists of generated values,
            or None if execution fails
        """
        self.pre_execute(context)
        count = self._determine_count(context)

        if count == 0:
            return {self.statement.full_name: []}

        # Make sure statement is serializable for Ray
        self.statement.sub_statements = list(self.statement.sub_statements)
        # Convert targets to list for serialization without modifying original
        targets_list = list(self.statement.targets)

        try:
            result = await self._execute_with_ray(context, count, targets_list)
            if not isinstance(result, dict):
                return {self.statement.full_name: []}
            return result
        except ray.exceptions.RayTaskError as e:
            logger.error(f"Ray task failed: {str(e)}")
            raise

    async def _process_results(self, context: SetupContext, results: list[dict]):
        """Process and export results from Ray workers"""
        exporter_util = context.root.class_factory_util.get_exporter_util()
        count = self._determine_count(context) or 0

        # Create exporters with operations
        consumer_with_operations, consumer_without_operations = exporter_util.create_exporter_list(
            setup_context=context,
            stmt=self.statement,
            targets=self.statement.targets,
            page_info=None,
        )

        # Handle MongoDB delete operations
        has_mongodb_delete = any(
            operation == "delete" and isinstance(consumer, MongoDBExporter)
            for consumer, operation in consumer_with_operations
        )

        if count == 0 and not has_mongodb_delete:
            return  # Skip processing if no data and no delete operations

        # Process results through exporters
        for result in results:
            if inspect.iscoroutine(result):
                result = await result
            if isinstance(result, dict):
                for key, value in result.items():
                    # Store in test result exporter
                    if context.test_mode and context.test_result_exporter:
                        context.test_result_exporter.consume((key, value))

                    # Handle operations
                    for consumer, operation in consumer_with_operations:
                        consumer.consume((key, value, {"operation": operation}))
                    # Handle non-operation consumers
                    for consumer in consumer_without_operations:
                        consumer.consume((key, value))

        # Finalize and cleanup
        _finalize_and_export_consumers(context, self.statement)

        # Cleanup
        for temp_dir in context.descriptor_dir.glob(f"temp_result_{context.task_id}*"):
            shutil.rmtree(temp_dir)

    def _merge_results(self, results: list[dict]) -> dict[str, list]:
        """Merge results from multiple workers"""
        merged: dict[str, list] = {}
        for result in results:
            for key, value in result.items():
                if key not in merged:
                    merged[key] = []
                merged[key].extend(value)
        return merged

    def _calculate_default_page_size(self, entity_count: int) -> int:
        """Calculate default page size for processing."""
        if self.statement.page_size is not None:
            return max(1, self.statement.page_size)

        if entity_count == 0:
            return 1

        default_page_size = 10000 if entity_count > 10000 else entity_count

        # Reduce page size if too many columns
        col_count = len(self.statement.sub_statements) if hasattr(self.statement, "sub_statements") else 0
        if col_count > 25:
            reduction_factor = col_count / 25
            default_page_size = int(default_page_size / reduction_factor)

        return max(1, default_page_size)

    @staticmethod
    def _scan_data_source(ctx: SetupContext, statement: Statement) -> None:
        """Scan data source and set data source length."""
        ctx.class_factory_util.get_datasource_util_cls().set_data_source_length(ctx, statement)
        if isinstance(statement, CompositeStatement):
            for child_stmt in statement.sub_statements:
                GenerateTask._scan_data_source(ctx, child_stmt)

    def pre_execute(self, context: Context):
        """Pre-execute task before Ray workers start."""
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
    async def execute_include(setup_stmt: SetupStatement, parent_context: GenIterContext) -> None:
        """Execute include XML model inside <generate>"""
        root_context = copy.deepcopy(parent_context.root)
        root_context.update_with_stmt(setup_stmt)
        root_context.global_variables.update(parent_context.current_variables)
        root_context.global_variables.update(parent_context.current_product)

        task_util_cls = root_context.class_factory_util.get_task_util_cls()
        for stmt in setup_stmt.sub_statements:
            task = task_util_cls.get_task_by_statement(root_context, stmt)
            if inspect.iscoroutinefunction(task.execute):
                await task.execute(root_context)  # Await async tasks
            else:
                task.execute(root_context)  # Execute sync tasks normally

    @staticmethod
    def convert_xml_dict_to_json_dict(xml_dict: dict):
        """Convert XML dict with #text and @attribute to pure JSON dict."""
        if "#text" in xml_dict:
            return xml_dict["#text"]
        res = {}
        for key, value in xml_dict.items():
            if not key.startswith("@"):
                if isinstance(value, dict | list):
                    if isinstance(value, dict):
                        res[key] = GenerateTask.convert_xml_dict_to_json_dict(value)
                    else:
                        res[key] = [
                            GenerateTask.convert_xml_dict_to_json_dict(v) if isinstance(v, dict) else v for v in value
                        ]
                else:
                    res[key] = value
        return res

    async def _execute_with_ray(self, context: Context, count: int, targets: list) -> dict[str, list[any]] | None:
        """Execute task using Ray workers"""
        try:
            page_size = self._calculate_default_page_size(count)
            num_workers = int(self.statement.num_process or context.root.num_process or 1)
            chunk_size = math.ceil(count / num_workers)

            workers = [GenerateWorker.remote() for _ in range(num_workers)]
            chunks = [(i * chunk_size, min((i + 1) * chunk_size, count)) for i in range(num_workers)]

            futures = []
            for worker, (start, end) in zip(workers, chunks, strict=True):
                logger.info(f"Generating chunk {start}-{end} with page size {page_size}")
                context_copy = copy.deepcopy(context)
                futures.append(worker.generate_chunk.remote(context_copy, self._statement, start, end, page_size))

            results = ray.get(futures)

            if isinstance(context, SetupContext):
                await self._process_results(context, results)
                return {}  # Return empty dict instead of None

            return self._merge_results(results)

        finally:
            # Cleanup
            if isinstance(context, SetupContext):
                for temp_dir in context.descriptor_dir.glob(f"temp_result_{context.task_id}*"):
                    shutil.rmtree(temp_dir)
