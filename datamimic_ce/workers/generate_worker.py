# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import copy
import os

import dill  # type: ignore[import-untyped]

from datamimic_ce.config import settings
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.data_sources.chunk_source_reader import ChunkSourceReader
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.exporters.exporter_state_manager import ExporterStateManager
from datamimic_ce.exporters.exporter_util import ExporterUtil
from datamimic_ce.logger import logger, setup_logger
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.tasks.generate_task import GenerateTask
from datamimic_ce.tasks.task_util import TaskUtil
from datamimic_ce.utils.logging_util import gen_timer


class GenerateWorker:
    """
    Worker class for generating and exporting data by page in single process.
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
        ) = ExporterUtil.create_exporter_list(
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

        # Keys the outermost run must accumulate across pages: everything in test mode,
        # otherwise only products a memstore consumes at the end of the run
        # (export_memstore). Anything else would pile up in RAM page after page — and
        # cross process boundaries in mp mode — only to be discarded.
        keep_keys: set[str] | None = None
        if isinstance(context, SetupContext) and not root_context.test_mode:
            keep_keys = GenerateWorker._memstore_product_keys(root_context, stmt)

        # Chunk-scoped source reader: owns the loads_all pool caching and hands each
        # page its window (see ChunkSourceReader) — the worker only iterates pages.
        source_reader = ChunkSourceReader(context, stmt)

        # Generate and consume product by page
        for page_index, page_tuple in enumerate(index_chunk):
            page_info = f"{page_index + 1}/{len(index_chunk)}"
            logger.info(f"Worker {worker_id} processing page {page_info}")
            page_start, page_end = page_tuple
            with gen_timer("generate", root_context.report_logging, stmt.full_name) as timer_result:
                timer_result["records_count"] = page_end - page_start
                # Generate product
                result_dict = GenerateWorker._generate_product_by_page_in_single_process(
                    context, stmt, page_start, page_end, worker_id, source_reader
                )

            with gen_timer("export", root_context.report_logging, stmt.full_name) as timer_result:
                timer_result["records_count"] = page_end - page_start
                # Export product by page
                TaskUtil.export_product_by_page(context.root, stmt, result_dict, exporter_state_manager)

            # Collect result for later capturing (keep_keys None -> keep everything)
            for key in result_dict.keys() if keep_keys is None else keep_keys & result_dict.keys():
                result[key] = result.get(key, []) + result_dict[key]

        return result

    @staticmethod
    def _memstore_product_keys(root_context: SetupContext, statement: GenerateStatement) -> set[str]:
        """full_names of statement + nested <generate>s whose targets include a memstore —
        the only products the end-of-run lazy export (export_memstore) consumes."""
        memstore_manager = root_context.memstore_manager
        keys: set[str] = set()

        def _walk(stmt: Statement) -> None:
            if isinstance(stmt, GenerateStatement) and any(
                "." not in t and "(" not in t and memstore_manager.contain(t) for t in stmt.targets
            ):
                keys.add(stmt.full_name)
            if isinstance(stmt, CompositeStatement):
                for sub in stmt.sub_statements:
                    _walk(sub)

        _walk(statement)
        return keys

    @staticmethod
    def _generate_product_by_page_in_single_process(
        context: SetupContext | GenIterContext,
        stmt: GenerateStatement,
        page_start: int,
        page_end: int,
        worker_id: int,
        source_reader: ChunkSourceReader,
    ) -> dict[str, list]:
        """
        (IMPORTANT: Only to be used as Ray multiprocessing function)
        This function is used to generate data for a single process, includes steps:
        1. Build sub-tasks in GenIterStatement
        2. Load data source (if any)
        3. Modify/Generate data by executing sub-tasks

        :param source_reader: chunk-scoped reader handing this page its source window
            (ordered: paged load; random/cumulated/unique: window of the cached pool).
        :return: Dictionary with generated products.
        """
        root_context: SetupContext = context.root

        # Determine number of data to be processed
        processed_data_count = page_end - page_start
        pagination = DataSourcePagination(skip=page_start, limit=processed_data_count)

        # Extract converter list for post-processing
        converter_list = TaskUtil.create_converter_list(context, stmt.converter)

        # 1: Build sub-tasks in GenIterStatement
        tasks = [
            TaskUtil.get_task_by_statement(root_context, child_stmt, pagination) for child_stmt in stmt.sub_statements
        ]

        # 2: Load this page's window of the data source (file, database, memory, ...)
        source_data, build_from_source = source_reader.read_page(page_start, page_end)

        # Used below to lazily evaluate scripted source templates after sub-tasks ran
        source_scripted = (
            stmt.source_script if stmt.source_script is not None else bool(root_context.default_source_scripted)
        )

        # Store temp result
        product_holder: dict[str, list] = {}
        result = []

        # Parsed once per page when in time-series mode; None otherwise.
        ts_config = stmt.get_time_series_config()

        # 3: Modify/Generate data by executing sub-tasks
        for idx in range(processed_data_count):
            # Create sub-context for each product record creation
            ctx = GenIterContext(context, stmt.name)
            # Get current worker_id from outermost gen_stmt
            ctx.worker_id = worker_id

            # Time-series mode: expose `ts` namespace (now/step/series) in the script context.
            # Use the global index (page_start + idx) so series/step are stable across chunks.
            if ts_config is not None:
                ctx.current_variables["ts"] = ts_config.at(page_start + idx)

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
                        task.execute(ctx)  # type: ignore[attr-defined]
                # Post-process product by applying converters
                for converter in converter_list:
                    ctx.current_product = converter.convert(ctx.current_product)

                # Lazily evaluate source script after executing sub-tasks
                if source_scripted:
                    # Evaluate python expression in source
                    prefix = stmt.variable_prefix or root_context.default_variable_prefix
                    suffix = stmt.variable_suffix or root_context.default_variable_suffix
                    evaluated_product = TaskUtil.evaluate_file_script_template(
                        ctx=ctx, datas=ctx.current_product, prefix=prefix, suffix=suffix
                    )
                    # Update current product with evaluated product
                    if not isinstance(evaluated_product, dict):
                        raise ValueError(
                            f"Source script evaluated result must be a dictionary, but got {type(evaluated_product)}"
                        )
                    ctx.current_product = evaluated_product

                result.append(ctx.current_product)
            except StopIteration:
                # Stop generating data if one of datasource reach the end
                logger.info(
                    f"Data generator sub-task {task.__class__.__name__} '{task.statement.name}' has already reached "
                    f"the end"
                )
                break

        # 4. Return product for later export
        product_holder[stmt.full_name] = result
        return product_holder

    @staticmethod
    def mp_preprocess(context: SetupContext | GenIterContext, worker_id: int):
        """
        Preprocess function for multiprocessing worker. Deserialize namespace functions and generators.
        """
        loglevel = os.getenv("LOG_LEVEL", "INFO")
        setup_logger(logger_name=settings.DEFAULT_LOGGER, worker_name=f"WORK-{worker_id}", level=loglevel)

        # Deserialize multiprocessing arguments
        context.root.namespace.update(dill.loads(context.root.namespace_functions))
        context.root.generators = dill.loads(context.root.generators)
