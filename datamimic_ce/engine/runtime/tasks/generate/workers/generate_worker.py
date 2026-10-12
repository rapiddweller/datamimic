# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import copy
import os
import pickle
from contextlib import suppress
from io import BytesIO

import dill

from datamimic_ce.engine.dsl.api import CompositeStatement, ConditionStatement, GenerateStatement, Statement
from datamimic_ce.engine.io.api import (
    DataSourcePagination,
    ExportSession,
    MongoDBConnectionConfig,
    RdbmsConnectionConfig,
    RegisteredClient,
    create_mongodb_client,
    create_rdbms_client,
    dispose_client_engine,
    resolve_target_entity,
)
from datamimic_ce.engine.runtime.contexts.context import (
    ClientConfig,
    DescriptorClientRef,
    SetupContext,
    WorkerContextPayload,
)
from datamimic_ce.engine.runtime.contexts.geniter_context import GenIterContext
from datamimic_ce.engine.runtime.logging import gen_timer, logger, setup_logger
from datamimic_ce.engine.runtime.scripting.evaluation import evaluate_source_template
from datamimic_ce.engine.runtime.tasks.base.dispatch import create_task
from datamimic_ce.engine.runtime.tasks.base.task import CommonSubTask, GenSubTask
from datamimic_ce.engine.runtime.tasks.generate.export_order import export_product_by_page
from datamimic_ce.engine.runtime.tasks.sources.chunk_source_reader import ChunkSourceReader
from datamimic_ce.engine.runtime.tasks.values.construction.converters import create_converter_list


class GenerateWorker:
    """
    Worker class for generating and exporting data by page in single process.
    """

    @staticmethod
    def serialize_worker_context(context: SetupContext) -> WorkerContextPayload:
        configs = {
            token: config
            for token, (client_ref, config) in enumerate(context._descriptor_client_history)
            if client_ref() is not None
        }
        tokens = {
            id(client): token
            for token, (client_ref, _config) in enumerate(context._descriptor_client_history)
            if (client := client_ref()) is not None
        }
        bindings = {
            client_id: tokens[id(client)]
            for client_id, client in context.clients.items()
            if id(client) in tokens
        }
        projected = context.worker_projection()
        namespace_functions = {key: value for key, value in projected.namespace.items() if callable(value)}
        for key in namespace_functions:
            projected.namespace.pop(key)
        generators = projected.generators
        projected.generators = {}

        seen: set[int] = set()

        def dump_graph(value: object) -> bytes:
            stream = BytesIO()

            class ClientReferencePickler(dill.Pickler):
                def persistent_id(self, obj: object) -> object | None:
                    token = obj.token if isinstance(obj, DescriptorClientRef) else tokens.get(id(obj))
                    if token is None:
                        return None
                    seen.add(token)
                    return ("descriptor-client", token)

            ClientReferencePickler(
                stream,
                protocol=dill.settings["protocol"],
                byref=dill.settings["byref"],
                fmode=dill.settings["fmode"],
                recurse=dill.settings["recurse"],
            ).dump(value)
            return stream.getvalue()

        context_bytes = dump_graph(projected)
        namespace_bytes = dump_graph(namespace_functions)
        generators_bytes = dump_graph(generators)
        payload_tokens = seen | set(bindings.values())
        return WorkerContextPayload(
            task_id=context.task_id,
            context=context_bytes,
            namespace_functions=namespace_bytes,
            generators=generators_bytes,
            client_configs={token: configs[token] for token in payload_tokens},
            client_bindings=bindings,
        )

    @staticmethod
    def deserialize_worker_context(payload: WorkerContextPayload) -> SetupContext:
        created: list[tuple[RegisteredClient, ClientConfig]] = []

        def load_graph(
            blob: bytes, configs: dict[int, ClientConfig]
        ) -> tuple[object, dict[int, RegisteredClient]]:
            graph_clients: dict[int, RegisteredClient] = {}
            stream = BytesIO(blob)

            class ClientReferenceUnpickler(dill.Unpickler):
                def persistent_load(self, persistent_id: object) -> object:
                    if not isinstance(persistent_id, tuple) or len(persistent_id) != 2:
                        raise pickle.UnpicklingError(f"Unknown descriptor client reference: {persistent_id!r}")
                    kind, token = persistent_id
                    if not isinstance(kind, str) or not isinstance(token, int):
                        raise pickle.UnpicklingError(f"Unknown descriptor client reference: {persistent_id!r}")
                    if kind != "descriptor-client" or token not in configs:
                        raise pickle.UnpicklingError(f"Unknown descriptor client reference: {persistent_id!r}")
                    if token not in graph_clients:
                        config = configs[token]
                        if isinstance(config, RdbmsConnectionConfig):
                            client = create_rdbms_client(config, payload.task_id)
                        elif isinstance(config, MongoDBConnectionConfig):
                            client = create_mongodb_client(config)
                        else:
                            raise pickle.UnpicklingError(
                                f"Unsupported descriptor client config: {type(config).__name__}"
                            )
                        graph_clients[token] = client
                        created.append((client, config))
                    return graph_clients[token]

            return ClientReferenceUnpickler(stream).load(), graph_clients

        try:
            context_object, context_clients = load_graph(payload.context, payload.client_configs)
            if not isinstance(context_object, SetupContext):
                raise pickle.UnpicklingError("Worker context graph did not contain SetupContext")
            namespace_functions, _function_clients = load_graph(payload.namespace_functions, payload.client_configs)
            if not isinstance(namespace_functions, dict):
                raise pickle.UnpicklingError("Worker namespace graph did not contain a mapping")
            generators, _generator_clients = load_graph(payload.generators, payload.client_configs)
            if not isinstance(generators, dict):
                raise pickle.UnpicklingError("Worker generators graph did not contain a mapping")
            context_object.namespace.update(namespace_functions)
            context_object.generators = generators
            context_object._clients = {}
            for client_id, token in payload.client_bindings.items():
                client = context_clients.get(token)
                config = payload.client_configs[token]
                if client is None:
                    if isinstance(config, RdbmsConnectionConfig):
                        client = create_rdbms_client(config, payload.task_id)
                    elif isinstance(config, MongoDBConnectionConfig):
                        client = create_mongodb_client(config)
                    else:
                        raise TypeError(f"Unsupported descriptor client config: {type(config).__name__}")
                    context_clients[token] = client
                    created.append((client, config))
                context_object._clients[client_id] = client
                context_object._descriptor_client_bindings[client_id] = context_object._record_descriptor_reference(
                    client, config
                )
            for client, config in created:
                context_object._record_descriptor_reference(client, config)
        except BaseException:
            with suppress(BaseException):
                GenerateWorker._cleanup_created_clients(created)
            raise
        return context_object

    @staticmethod
    def _cleanup_created_clients(clients: list[tuple[RegisteredClient, ClientConfig]]) -> None:
        first_error: BaseException | None = None
        for client, _config in clients:
            try:
                dispose_client_engine(client)
            except BaseException as error:
                if first_error is None:
                    first_error = error
        if first_error is not None:
            raise first_error

    @staticmethod
    def cleanup_worker_context(context: SetupContext) -> None:
        owned = context.take_owned_descriptor_clients()
        clients = [
            (client, config)
            for client_ref, config in context._descriptor_client_history
            if (client := client_ref()) is not None and any(client is current for current in owned)
        ]
        GenerateWorker._cleanup_created_clients(clients)

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

        root_context = context.root
        export_session = root_context.export_session
        if export_session is None:
            export_session = ExportSession(worker_id)
            root_context.export_session = export_session
        export_session.register(
            setup_context=root_context,
            full_name=stmt.full_name,
            product_name=resolve_target_entity(stmt.target_entity, None, stmt.name),
            export_uri=stmt.export_uri,
            targets=list(stmt.targets),
        )

        # Keys the outermost run must accumulate across pages: everything in test mode,
        # otherwise only products a memstore consumes at the end of the run
        # (export_memstore). Anything else would pile up in RAM page after page — and
        # cross process boundaries in mp mode — only to be discarded.
        keep_keys: set[str] | None = None
        if isinstance(context, SetupContext) and not root_context.test_mode:
            keep_keys = GenerateWorker._memstore_product_keys(root_context, stmt)

        # Chunk-scoped source reader: loads + orders the source once per chunk and hands
        # each page its window (see ChunkSourceReader) — the worker only iterates pages.
        source_reader = ChunkSourceReader(context, stmt, chunk_start, chunk_end)

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
                # Export product by page. A NESTED generate (GenIterContext) defers to the enclosing
                # statement's page export, which writes the parent's rows first and then recurses into
                # the children - exporting here would land child rows
                # in the DB before their parent exists and break child->parent FK constraints.
                if not isinstance(context, GenIterContext):
                    export_product_by_page(stmt, result_dict, export_session)

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
        converter_list = create_converter_list(context, stmt.converter)

        # 1: Build sub-tasks in GenIterStatement
        tasks = [
            create_task(child_stmt, root_context, pagination) for child_stmt in stmt.sub_statements
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
                for task in tasks:
                    # Collect product from sub-generate task and add into product_holder
                    if not isinstance(task, GenSubTask | CommonSubTask):
                        raise TypeError(f"Unsupported generation task type: {type(task).__name__}")
                    if isinstance(task.statement, GenerateStatement | ConditionStatement):
                        # Execute sub generate task
                        sub_gen_result = task.execute(ctx)
                        if isinstance(sub_gen_result, dict):
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
                    converted_product = converter.convert(ctx.current_product)
                    if not isinstance(converted_product, dict):
                        raise ValueError(
                            f"Product converter must return a dictionary, but got {type(converted_product)}"
                        )
                    ctx.current_product = converted_product

                # Lazily evaluate source script after executing sub-tasks
                if source_scripted:
                    # Evaluate python expression in source
                    prefix = stmt.variable_prefix or root_context.default_variable_prefix
                    suffix = stmt.variable_suffix or root_context.default_variable_suffix
                    evaluated_product = evaluate_source_template(ctx, ctx.current_product, prefix, suffix)
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
        setup_logger(logger_name="DATAMIMIC", worker_name=f"WORK-{worker_id}", level=loglevel)

        # worker_id is 1-indexed (mp_process: enumerate(chunks, 1)); SetupContext.process_id is
        # 0-indexed (consumers like SequenceTableGenerator multiply it by a per-process share).
        # This was never wired up before - every worker read process_id as None/0, so
        # SequenceTableGenerator's per-process offset was always a no-op and the only thing
        # separating workers' id ranges was the shared DB sequence's own atomic advance, which
        # isn't a real guarantee once the per-process math is supposed to keep ranges apart.
        context.root.process_id = worker_id - 1
