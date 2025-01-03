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


def _wrapper(args):
    """
    Wrapper multiprocessing function to deserialize args and execute the generate function.

    :param args: Tuple containing necessary arguments.
    :return: Result from single_process_execute_function.
    """
    (
        local_ctx,
        statement,
        chunk_data,
        single_process_execute_function,
        namespace_functions,
        mp_idx,
        page_size,
        mp_chunk_size,
    ) = args
    # Re-initialize logging for this child process
    loglevel = os.getenv("LOG_LEVEL", "INFO")
    setup_logger_func = local_ctx.class_factory_util.get_setup_logger_func()
    app_settings = local_ctx.class_factory_util.get_app_settings()
    setup_logger_func(logger_name=app_settings.DEFAULT_LOGGER, task_id=local_ctx.task_id, level=loglevel)

    # Deserialize utility functions
    namespace_functions = dill.loads(namespace_functions)
    local_ctx.namespace.update(namespace_functions)
    local_ctx.generators = dill.loads(local_ctx.generators)

    return single_process_execute_function((local_ctx, statement, chunk_data, mp_idx, page_size, mp_chunk_size))


def _geniter_single_process_generate(args: tuple) -> dict[str, list]:
    """
    (IMPORTANT: Only to be used as multiprocessing function) Generate product in each single process.

    :param args: Tuple containing context, statement, and index range.
    :return: Dictionary with generated products.
    """

    # Parse args
    context: SetupContext | GenIterContext = args[0]
    root_context: SetupContext = context.root
    stmt: GenerateStatement = args[1]
    start_idx, end_idx = args[2]

    # Determine number of data to be processed
    processed_data_count = end_idx - start_idx
    pagination = DataSourcePagination(skip=start_idx, limit=processed_data_count)

    # Prepare loaded datasource pagination
    load_start_idx = start_idx
    load_end_idx = end_idx
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


def _geniter_single_process_generate_and_consume_by_page(args: tuple) -> dict:
    """
    IMPORTANT: Used as multiprocessing page process function only.
    Generate then consume product in each single process by page.

    :param args: Tuple containing necessary arguments.
    :return: Dictionary with generated products if needed.
    """
    context: SetupContext = args[0]
    stmt: GenerateStatement = args[1]
    mp_idx = args[3]
    start_idx, end_idx = args[2]
    page_size = args[4]
    mp_chunk_size = args[5]

    # Calculate page chunk
    index_chunk = [(i, min(i + page_size, end_idx)) for i in range(start_idx, end_idx, page_size)]

    # Check if product result should be returned on multiprocessing process
    return_product_result = context.test_mode or any(
        [context.memstore_manager.contain(consumer_str) for consumer_str in stmt.targets]
    )
    result: dict = {}

    # Generate and consume product by page
    args_list = list(args)
    for page_idx, index_tuple in enumerate(index_chunk):
        # Index tuple for each page
        args_list[2] = index_tuple
        updated_args = tuple(args_list)

        result_dict = _geniter_single_process_generate(updated_args)
        _consume_by_page(
            stmt,
            context,
            result_dict,
            page_idx,
            page_size,
            mp_idx,
            mp_chunk_size,
            page_idx == len(index_chunk) - 1,
        )
        if return_product_result:
            for key, value in result_dict.items():
                result[key] = result.get(key, []) + value

        # Manual garbage collection
        del result_dict
        # gc.collect()

    return result


def _consume_by_page(
    stmt: GenerateStatement,
    context: Context,
    xml_result: dict,
    page_idx: int,
    page_size: int,
    mp_idx: int | None,
    mp_chunk_size: int | None,
    is_last_page: bool,
) -> None:
    """
    Consume product by page.

    :param stmt: GenerateStatement instance.
    :param context: Context instance.
    :param xml_result: Generated product data.
    :param page_idx: Current page index.
    :param page_size: Page size for processing.
    :param mp_idx: Multiprocessing index.
    :param mp_chunk_size: Chunk size for multiprocessing.
    :return: None
    """
    # Consume non-specific exporters
    _consume_outermost_gen_stmt_by_page(
        stmt,
        context,
        xml_result,
        MultiprocessingPageInfo(
            mp_idx,
            mp_chunk_size,
            page_idx,
            page_size,
        ),
        is_last_page,
    )


def _pre_consume_product(stmt: GenerateStatement, dict_result: list[dict]) -> tuple:
    """
    Preprocess consumer data to adapt some special consumer (e.g., MongoDB upsert).

    :param stmt: GenerateStatement instance.
    :param dict_result: Generated data.
    :return: Preprocessed product tuple.
    """
    packed_result: tuple
    if getattr(stmt, "selector", False):
        packed_result = (stmt.name, dict_result, {"selector": stmt.selector})
    elif getattr(stmt, "type", False):
        packed_result = (stmt.name, dict_result, {"type": stmt.type})
    else:
        packed_result = (stmt.name, dict_result)
    return packed_result


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


def _load_csv_file(
    ctx: SetupContext,
    file_path: Path,
    separator: str,
    cyclic: bool | None,
    start_idx: int,
    end_idx: int,
    source_scripted: bool,
    prefix: str,
    suffix: str,
) -> list[dict]:
    """
    Load CSV content from file with skip and limit.

    :param file_path: Path to the CSV file.
    :param separator: CSV delimiter.
    :param cyclic: Whether to cycle through data.
    :param start_idx: Starting index.
    :param end_idx: Ending index.
    :return: List of dictionaries representing CSV rows.
    """
    from datamimic_ce.tasks.task_util import TaskUtil

    cyclic = cyclic if cyclic is not None else False

    with file_path.open(newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=separator)
        pagination = (
            DataSourcePagination(start_idx, end_idx - start_idx)
            if (start_idx is not None and end_idx is not None)
            else None
        )
        result = DataSourceUtil.get_cyclic_data_list(data=list(reader), cyclic=cyclic, pagination=pagination)

        # if sourceScripted then evaluate python expression in csv
        if source_scripted:
            evaluated_result = TaskUtil.evaluate_file_script_template(
                ctx=ctx, datas=result, prefix=prefix, suffix=suffix
            )
            return evaluated_result if isinstance(evaluated_result, list) else [evaluated_result]

        return result


def _load_json_file(task_id: str, file_path: Path, cyclic: bool | None, start_idx: int, end_idx: int) -> list[dict]:
    """
    Load JSON content from file using skip and limit.

    :param file_path: Path to the JSON file.
    :param cyclic: Whether to cycle through data.
    :param start_idx: Starting index.
    :param end_idx: Ending index.
    :return: List of dictionaries representing JSON objects.
    """
    cyclic = cyclic if cyclic is not None else False

    # Try to load JSON data from InMemoryCache
    in_mem_cache = InMemoryCache()
    # Add task_id to cache_key for testing lib without platform
    cache_key = str(file_path) if task_id in str(file_path) else f"{task_id}_{str(file_path)}"
    cache_data = in_mem_cache.get(cache_key)
    if cache_data:
        data = json.loads(cache_data)
    else:
        # Read the JSON data from a file and store it in redis
        with file_path.open("r") as file:
            data = json.load(file)
        # Store data in redis for 24 hours
        in_mem_cache.set(str(file_path), json.dumps(data))

    if not isinstance(data, list):
        raise ValueError(f"JSON file '{file_path.name}' must contain a list of objects")
    pagination = (
        DataSourcePagination(start_idx, end_idx - start_idx)
        if (start_idx is not None and end_idx is not None)
        else None
    )
    return DataSourceUtil.get_cyclic_data_list(data=data, cyclic=cyclic, pagination=pagination)


def _load_xml_file(file_path: Path, cyclic: bool | None, start_idx: int, end_idx: int) -> list[dict]:
    """
    Load XML content from file using skip and limit.

    :param file_path: Path to the XML file.
    :param cyclic: Whether to cycle through data.
    :param start_idx: Starting index.
    :param end_idx: Ending index.
    :return: List of dictionaries representing XML items.
    """
    cyclic = cyclic if cyclic is not None else False
    # Read the XML data from a file
    with file_path.open("r") as file:
        data = xmltodict.parse(file.read(), attr_prefix="@", cdata_key="#text")
        # Handle the case where data might be None
        if data is None:
            return []

        # Extract items from list structure if present
        if isinstance(data, dict) and data.get("list") and data.get("list", {}).get("item"):
            items = data["list"]["item"]
        else:
            items = data

        # Convert single item to list if needed
        if isinstance(items, OrderedDict):
            items = [items]
        elif not isinstance(items, list):
            items = []

        # Apply pagination if needed
        pagination = (
            DataSourcePagination(start_idx, end_idx - start_idx)
            if (start_idx is not None and end_idx is not None)
            else None
        )
        return DataSourceUtil.get_cyclic_data_list(data=items, cyclic=cyclic, pagination=pagination)


def _evaluate_selector_script(context: Context, stmt: GenerateStatement):
    """
    Evaluate script selector.

    :param context: Context instance.
    :param stmt: GenerateStatement instance.
    :return: Evaluated selector.
    """
    from datamimic_ce.tasks.task_util import TaskUtil

    selector = stmt.selector or ""
    prefix = stmt.variable_prefix or context.root.default_variable_prefix
    suffix = stmt.variable_suffix or context.root.default_variable_suffix
    return TaskUtil.evaluate_variable_concat_prefix_suffix(context, selector, prefix=prefix, suffix=suffix)


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
                selector = _evaluate_selector_script(context=context, stmt=self._statement)
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

    def _prepare_mp_generate_args(
        self,
        setup_ctx: SetupContext,
        single_process_execute_function: Callable,
        count: int,
        num_processes: int,
        page_size: int,
    ) -> list[tuple]:
        """
        Prepare arguments for multiprocessing function.

        :param setup_ctx: SetupContext instance.
        :param single_process_execute_function: Function to execute in single process.
        :param count: Total number of records.
        :param num_processes: Number of processes.
        :param page_size: Page size for processing.
        :return: List of argument tuples.
        """
        # Determine chunk size
        mp_chunk_size = math.ceil(count / num_processes)

        # Log processing info
        logger.info(
            f"Run {type(self.statement).__name__} task for entity {self.statement.name} with "
            f"{num_processes} processes in parallel and chunk size: {mp_chunk_size}"
        )

        # Determine chunk indices
        chunk_data_list = self._get_chunk_indices(mp_chunk_size, count)

        # Split namespace functions from current namespace
        namespace_functions = {k: v for k, v in setup_ctx.namespace.items() if callable(v)}
        for func in namespace_functions:
            setup_ctx.namespace.pop(func)

        # Serialize namespace functions
        setup_ctx.namespace_functions = dill.dumps(namespace_functions)

        setup_ctx.generators = dill.dumps(setup_ctx.generators)

        # Close RDBMS engine
        for _key, value in setup_ctx.clients.items():
            if isinstance(value, RdbmsClient) and value.engine is not None:
                value.engine.dispose()
                value.engine = None

        # List of arguments to be processed in parallel
        return [
            (
                setup_ctx,
                self._statement,
                chunk_data_list[idx],
                single_process_execute_function,
                setup_ctx.namespace_functions,
                idx,
                page_size,
                mp_chunk_size,
            )
            for idx in range(len(chunk_data_list))
        ]

    def _sp_generate(self, context: Context, start: int, end: int) -> dict[str, list]:
        """
        Single-process generate product.

        :param context: Context instance.
        :param start: Start index.
        :param end: End index.
        :return: Generated product data.
        """
        if end - start == 0:
            return {}

        report_logging = isinstance(context, SetupContext) and context.report_logging
        with gen_timer("generate", report_logging, self.statement.full_name) as timer_result:
            # Generate product
            result = _geniter_single_process_generate((context, self._statement, (start, end)))
            timer_result["records_count"] = len(result.get(self._statement.full_name, []))

        return result

    def _mp_page_process(
        self,
        setup_ctx: SetupContext,
        page_size: int,
        single_process_execute_function: Callable[[tuple], dict | None],
    ):
        """
        Multi-process page generation and consumption of products.

        This method divides the work across multiple processes, each of which generates and consumes
        products in chunks. After multiprocessing, a post-processing step applies any necessary
        consumer/exporter operations on the merged results from all processes.

        :param setup_ctx: The setup context instance containing configurations and resources.
        :param page_size: The page size for each process to handle per batch.
        :param single_process_execute_function: The function each process will execute.
        """
        exporter_util = setup_ctx.root.class_factory_util.get_exporter_util()

        # Start timer to measure entire process duration
        with gen_timer("process", setup_ctx.report_logging, self.statement.full_name) as timer_result:
            # 1. Determine the total record count and number of processes
            count = self._determine_count(setup_ctx)
            num_processes = self.statement.num_process or setup_ctx.num_process or multiprocessing.cpu_count()

            timer_result["records_count"] = count

            # 2. Prepare arguments for each process based on count, process count, and page size
            arg_list = self._prepare_mp_generate_args(
                setup_ctx,
                single_process_execute_function,
                count,
                num_processes,
                page_size,
            )

            # Debug log the chunks each process will handle
            chunk_info = [args[2] for args in arg_list]
            logger.debug(f"Start generating {count} products with {num_processes} processes, chunks: {chunk_info}")
            # 3. Initialize any required post-process consumers, e.g., for testing or memory storage
            post_consumer_list = []
            # Add test result exporter if test mode is enabled
            if setup_ctx.test_mode:
                post_consumer_list.append(EXPORTER_TEST_RESULT_EXPORTER)
            # Add memstore exporters
            post_consumer_list.extend(
                filter(
                    lambda consumer_str: setup_ctx.memstore_manager.contain(consumer_str),
                    self.statement.targets,
                )
            )

            # Initialize exporters for each post-process consumer
            _, post_consumer_list_instances = exporter_util.create_exporter_list(
                setup_ctx, self.statement, post_consumer_list, None
            )
            logger.debug(
                f"Post-consumer exporters initialized: "
                f"{[consumer.__class__.__name__ for consumer in post_consumer_list_instances]}"
            )

            # 4. Run multiprocessing Pool to handle the generation/consumption function for each chunk
            with multiprocessing.Pool(processes=num_processes) as pool:
                # Collect then merge result
                mp_result_list = pool.map(_wrapper, arg_list)

            # 5. Post-processing with consumer consumption for merged results across processes
            if post_consumer_list_instances:
                logger.debug("Processing merged results with post-consumers.")
                for consumer in post_consumer_list_instances:
                    for mp_result in mp_result_list:
                        for key, value in mp_result.items():
                            logger.debug(f"Consuming result for {key} with {consumer.__class__.__name__}")
                            consumer.consume((key, value))

            # 6. Clean up and finalize
            del mp_result_list  # Free up memory from the merged results
            logger.info("Completed multi-process page processing.")

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
        self.pre_execute(context)

        # Determine count of generate process
        count = self._determine_count(context)

        if count == 0:
            return {self.statement.full_name: []}

        page_size = self._calculate_default_page_size(count)

        # Generate and export if gen_stmt is outermost (which has context as SetupContext)
        exporter_util = context.root.class_factory_util.get_exporter_util()
        if isinstance(context, SetupContext):
            consumer_with_operations, consumer_without_operations = exporter_util.create_exporter_list(
                setup_context=context,
                stmt=self.statement,
                targets=self.statement.targets,
                page_info=None,
            )
            # Check for conditions to use multiprocessing
            has_mongodb_delete = any(
                [
                    operation == "delete" and isinstance(consumer, MongoDBExporter)
                    for consumer, operation in consumer_with_operations
                ]
            )
            match self.statement.multiprocessing:
                case None:
                    use_mp = (not has_mongodb_delete) and context.use_mp
                case _:
                    use_mp = bool(self.statement.multiprocessing)

            # Generate in multiprocessing
            if use_mp:
                # IMPORTANT: always use deep copied setup_ctx for mp to avoid modify original setup_ctx accidentally
                copied_ctx = copy.deepcopy(context)
                # Process data by page
                logger.info(f"Processing by page with size {page_size} for '{self.statement.name}'")
                self._mp_page_process(
                    copied_ctx,
                    page_size,
                    _geniter_single_process_generate_and_consume_by_page,
                )
            # Generate and consume in single process
            else:
                # Process data by page in single process
                index_chunk = self._get_chunk_indices(page_size, count)
                logger.info(f"Processing {len(index_chunk)} pages for {count:,} products of '{self.statement.name}'")
                for page_index, page_tuple in enumerate(index_chunk):
                    start, end = page_tuple
                    logger.info(
                        f"Processing {end - start:,} product '{self.statement.name}' on page "
                        f"{page_index + 1}/{len(index_chunk)} in a single process"
                    )
                    # Generate product
                    result = self._sp_generate(context, start, end)
                    # Consume by page
                    _consume_by_page(
                        self.statement,
                        context,
                        result,
                        page_index,
                        page_size,
                        None,
                        None,
                        page_index == len(index_chunk) - 1,
                    )

                    # Manual garbage collection to free memory
                    del result

            # Clean temp directory on outermost gen_stmt
            for temp_dir in context.descriptor_dir.glob(f"temp_result_{context.task_id}*"):
                shutil.rmtree(temp_dir)

        # Just return product generated in single process if gen_stmt is inner one
        else:
            # Do not apply process by page for inner gen_stmt
            return self._sp_generate(context, 0, count)

        return None

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
