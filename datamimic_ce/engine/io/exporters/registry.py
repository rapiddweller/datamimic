# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from collections.abc import Callable, Mapping

from datamimic_ce.engine.dsl.parsers.input.target import parse_function_string
from datamimic_ce.engine.dsl.vocabulary.constants.exporter_constants import (
    EXPORTER_CONSOLE_EXPORTER,
    EXPORTER_CSV,
    EXPORTER_DBUNIT,
    EXPORTER_FIXED_WIDTH,
    EXPORTER_JSON,
    EXPORTER_LOG_EXPORTER,
    EXPORTER_TEST_RESULT_EXPORTER,
    EXPORTER_TXT,
    EXPORTER_XLSX,
    EXPORTER_XML,
)
from datamimic_ce.engine.dsl.vocabulary.enums.operation_enums import ExportOperation
from datamimic_ce.engine.io.clients.client import RegisteredClient
from datamimic_ce.engine.io.clients.mongodb_client import MongoDBClient
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.contracts import SmokeExportRequest
from datamimic_ce.engine.io.exporters.core.exporter import Exporter
from datamimic_ce.engine.io.exporters.core.exporter_config import ExporterConfig
from datamimic_ce.engine.io.exporters.core.exporter_context import ExporterContext
from datamimic_ce.engine.io.exporters.core.exporter_state_manager import ExporterStateManager
from datamimic_ce.engine.io.exporters.core.routing import resolve_target_entity
from datamimic_ce.engine.io.exporters.core.unified_buffered_exporter import UnifiedBufferedExporter
from datamimic_ce.engine.io.exporters.database.database_exporter import DatabaseExporter
from datamimic_ce.engine.io.exporters.database.mongodb_exporter import MongoDBExporter
from datamimic_ce.engine.io.exporters.diagnostics.console_exporter import ConsoleExporter
from datamimic_ce.engine.io.exporters.diagnostics.log_exporter import LogExporter
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.io.exporters.formats.csv_exporter import CSVExporter
from datamimic_ce.engine.io.exporters.formats.dbunit_exporter import DbUnitExporter
from datamimic_ce.engine.io.exporters.formats.fixed_width_exporter import FixedWidthExporter
from datamimic_ce.engine.io.exporters.formats.json_exporter import JsonExporter
from datamimic_ce.engine.io.exporters.formats.txt_exporter import TXTExporter
from datamimic_ce.engine.io.exporters.formats.xlsx_exporter import XLSXExporter
from datamimic_ce.engine.io.exporters.formats.xml_exporter import XMLExporter
from datamimic_ce.engine.io.exporters.memory.memstore import Memstore

_BufferedExporterFactory = Callable[[ExporterConfig, dict], UnifiedBufferedExporter]
_BUFFERED_EXPORTERS: dict[str, _BufferedExporterFactory] = {
    EXPORTER_CSV: CSVExporter,
    EXPORTER_JSON: JsonExporter,
    EXPORTER_XML: XMLExporter,
    EXPORTER_XLSX: XLSXExporter,
    EXPORTER_TXT: TXTExporter,
    EXPORTER_DBUNIT: DbUnitExporter,
    EXPORTER_FIXED_WIDTH: FixedWidthExporter,
}


def buffered_exporter_names() -> frozenset[str]:
    """Return the registered buffered file-export target names."""

    return frozenset(_BUFFERED_EXPORTERS)


def create_exporter_list(
    setup_context: ExporterContext,
    product_name: str,
    export_uri: str | None,
    targets: list[str],
) -> tuple[list[tuple[Exporter, ExportOperation]], list[Exporter]]:
    """Build operation and ordinary exporters from the statement's target strings."""
    consumers_with_operation: list[tuple[Exporter, ExportOperation]] = []
    consumers_without_operation: list[Exporter] = []

    try:
        parsed_targets = parse_function_string(",".join(list(targets)))
    except ValueError as e:
        raise ValueError(f"Error parsing target string: {e}") from e

    for target in parsed_targets:
        exporter_name = target["function_name"]
        params = target.get("params") or {}
        if "." in exporter_name:
            consumer_name, operation_raw = exporter_name.split(".", 1)
            try:
                operation = ExportOperation(operation_raw)
            except ValueError:
                valid = ", ".join(op.value for op in ExportOperation)
                raise ValueError(
                    f"Unknown client operation '{operation_raw}' in target '{exporter_name}'. "
                    f"Valid operations: {valid}; a plain client id inserts."
                ) from None
            client = setup_context.get_client_by_id(consumer_name)
            consumer = _create_exporter_from_client(client, consumer_name)
            consumers_with_operation.append((consumer, operation))
        else:
            exporter = _get_exporter_by_name(setup_context, exporter_name, product_name, export_uri, params)
            if exporter is not None:
                consumers_without_operation.append(exporter)

    return consumers_with_operation, consumers_without_operation


def _create_exporter_from_client(client: RegisteredClient | None, client_name: str) -> Exporter:
    if isinstance(client, MongoDBClient):
        return MongoDBExporter(client)
    if isinstance(client, RdbmsClient):
        return DatabaseExporter(client)
    raise ValueError(f"Cannot create target for client {client_name}")


def _get_exporter_by_name(
    setup_context: ExporterContext,
    name: str,
    product_name: str,
    export_uri: str | None,
    exporter_params_dict: dict,
) -> Exporter | None:
    if name is None or name == "":
        return None

    if name in _BUFFERED_EXPORTERS:
        config = ExporterConfig(
            product_name=product_name,
            chunk_size=exporter_params_dict.get("chunk_size"),
            encoding=exporter_params_dict.get("encoding"),
            export_uri=export_uri,
            default_encoding=setup_context.default_encoding,
            default_separator=setup_context.default_separator,
            default_line_separator=setup_context.default_line_separator,
            descriptor_dir=setup_context.descriptor_dir,
            task_id=setup_context.task_id,
            use_mp=setup_context.use_mp,
        )
        return _BUFFERED_EXPORTERS[name](config, exporter_params_dict)

    if name == EXPORTER_CONSOLE_EXPORTER:
        return ConsoleExporter()
    if name == EXPORTER_LOG_EXPORTER:
        return LogExporter()
    if name == EXPORTER_TEST_RESULT_EXPORTER:
        return setup_context.test_result_exporter
    if name in setup_context.clients:
        return _create_exporter_from_client(setup_context.get_client_by_id(name), name)
    if setup_context.memstore_manager.contain(name):
        return setup_context.memstore_manager.get_memstore(name)
    raise ValueError(
        f"Target not found: {name}, please check the target name again. "
        f"Expected: {', '.join(_BUFFERED_EXPORTERS)}, {EXPORTER_TEST_RESULT_EXPORTER}, "
        f"{EXPORTER_CONSOLE_EXPORTER}, {EXPORTER_LOG_EXPORTER}, "
        f"or client {list(setup_context.clients.keys())} "
        f"or memstore {setup_context.memstore_manager.get_memstores_list()}"
    )


def capture_test_results(
    setup_context: ExporterContext,
    products: Mapping[str, list[dict[str, object]]],
) -> None:
    """Capture after worker merge so SP and MP expose the same product set."""
    exporter = setup_context.test_result_exporter
    if not isinstance(exporter, TestResultExporter):
        raise TypeError("Test capture requires TestResultExporter")
    for product_name, product_rows in products.items():
        exporter.consume((product_name, product_rows))


def consume_memstore_target(
    setup_context: ExporterContext,
    targets: list[str],
    target_entity: str | None,
    product_type: str | None,
    product_name: str,
    full_name: str,
    products: Mapping[str, list[dict[str, object]]],
) -> None:
    """Preserve the existing first-memstore-target write rule."""
    for target in targets:
        if setup_context.memstore_manager.contain(target):
            entity = resolve_target_entity(target_entity, product_type, product_name)
            rows = products.get(full_name, [])
            exporter = setup_context.memstore_manager.get_memstore(target)
            if not isinstance(exporter, Memstore):
                raise TypeError("Memstore target requires Memstore exporter")
            exporter.consume((entity, rows))
            return


def smoke_export(request: SmokeExportRequest) -> int:
    """Run one bounded buffered export for an authoring smoke check."""
    params = request.params
    rows = request.rows
    chunk_size = params.get("chunk_size")
    if chunk_size is not None and not isinstance(chunk_size, int):
        raise TypeError("chunk_size target option must be an integer")
    encoding = params.get("encoding")
    if encoding is not None and not isinstance(encoding, str):
        raise TypeError("encoding target option must be a string")

    config = ExporterConfig(
        product_name=request.basename,
        chunk_size=chunk_size,
        encoding=encoding,
        export_uri=None,
        track_serialized_rows=True,
        default_encoding="utf-8",
        default_separator=request.default_separator,
        default_line_separator=request.default_line_separator,
        descriptor_dir=request.descriptor_dir,
        task_id=request.task_id,
        use_mp=False,
    )
    exporter = _BUFFERED_EXPORTERS[request.exporter_name](config, dict(params))
    state_manager = ExporterStateManager(worker_id=1)
    exporter.consume((request.basename, rows), request.full_name, state_manager)
    exporter.finalize_chunks(1)
    return exporter.count_buffered_rows(1)
