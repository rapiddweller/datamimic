# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import copy

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.data_sources.data_source_registry import DataSourceRegistry
from datamimic_ce.exporters.exporter_state_manager import ExporterStateManager
from datamimic_ce.logger import logger
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.tasks.generate_task import GenerateTask
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

        # Check if product result should be returned for test mode or memstore exporter
        has_memstore_exporter = False
        current_gen_stmt = stmt
        while isinstance(current_gen_stmt, GenerateStatement):
            if any(
                    [
                        ("." not in exporter_str)
                        and ("(" not in exporter_str)
                        and context.root.memstore_manager.contain(exporter_str)
                        for exporter_str in stmt.targets
                    ]
            ):
                has_memstore_exporter = True
                break
            current_gen_stmt = current_gen_stmt.parent_stmt  # type: ignore[assignment]

        return_product_result = isinstance(context, GenIterContext) or context.root.test_mode or has_memstore_exporter

        # Generate and consume product by page
        for page_index, page_tuple in enumerate(index_chunk):
            page_info = f"{page_index + 1}/{len(index_chunk)}"
            logger.info(f"Worker {worker_id} processing page {page_info}")
            page_start, page_end = page_tuple
            with gen_timer("generate", root_context.report_logging, stmt.full_name) as timer_result:
                timer_result["records_count"] = page_end - page_start
                # Generate product
                result_dict = GenerateWorker._generate_product_by_page_in_single_process(
                    context, stmt, page_start, page_end, worker_id
                )

            with gen_timer("export", root_context.report_logging, stmt.full_name) as timer_result:
                timer_result["records_count"] = page_end - page_start
                # Export product by page
                context.root.class_factory_util.get_task_util_cls().export_product_by_page(
                    context.root, stmt, result_dict, exporter_state_manager
                )

            # TODO: improve by select only necessary keys
            # Collect result for later capturing
            if return_product_result:
                for key in result_dict:
                    result[key] = result.get(key, []) + result_dict.get(key, [])

        # Log DataSourceRegistry statistics
        if isinstance(context, SetupContext):
            context.class_factory_util.get_datasource_registry().log_cache_info()

        return result

    @staticmethod
    def _generate_product_by_page_in_single_process(
            context: SetupContext | GenIterContext, stmt: GenerateStatement, page_start: int, page_end: int,
            worker_id: int
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
            task_util_cls.get_task_by_statement(root_context, child_stmt, pagination)
            for child_stmt in stmt.sub_statements
        ]

        # 2: Load data source from file, database, memory, Kafka, etc.
        source_scripted = (
            stmt.source_script if stmt.source_script is not None else bool(root_context.default_source_scripted)
        )
        separator = stmt.separator or root_context.default_separator

        source_data, build_from_source = (
            context.root.class_factory_util.get_task_util_cls().gen_task_load_data_from_source_or_script(
                context,
                stmt,
                stmt.source,
                separator,
                source_scripted,
                processed_data_count,
                load_start_idx,
                load_end_idx,
                load_pagination,
            )
        )

        # Shuffle source data if distribution is random
        if is_random_distribution:
            seed = root_context.get_distribution_seed()
            # Use original pagination for shuffling
            source_data = DataSourceRegistry.get_shuffled_data_with_cyclic(source_data, pagination, stmt.cyclic, seed)

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
                    f"Data generator sub-task {task.__class__.__name__} '{task.statement.name}' has already reached "
                    f"the end"
                )
                break

        # 4. Return product for later export
        product_holder[stmt.full_name] = result
        return product_holder
