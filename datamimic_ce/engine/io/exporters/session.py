# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file in the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import logging
from typing import TypedDict

from datamimic_ce.engine.dsl.vocabulary.enums.operation_enums import ExportOperation
from datamimic_ce.engine.io.exporters.core.exporter import Exporter
from datamimic_ce.engine.io.exporters.core.exporter_context import ExporterContext
from datamimic_ce.engine.io.exporters.core.exporter_state_manager import ExporterStateManager
from datamimic_ce.engine.io.exporters.core.serialization import convert_xml_dict_to_json_dict
from datamimic_ce.engine.io.exporters.core.unified_buffered_exporter import UnifiedBufferedExporter
from datamimic_ce.engine.io.exporters.database.database_exporter import DatabaseExporter
from datamimic_ce.engine.io.exporters.database.mongodb_exporter import MongoDBExporter
from datamimic_ce.engine.io.exporters.diagnostics.console_exporter import ConsoleExporter
from datamimic_ce.engine.io.exporters.diagnostics.log_exporter import LogExporter
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.io.exporters.formats.xml_exporter import XMLExporter
from datamimic_ce.engine.io.exporters.memory.memstore import Memstore
from datamimic_ce.engine.io.exporters.registry import create_exporter_list

logger = logging.getLogger("DATAMIMIC")


class _ProductExporters(TypedDict):
    with_operation: list[tuple[Exporter, ExportOperation]]
    without_operation: list[Exporter]


PreparedPage = tuple[
    tuple[str, list[object]] | tuple[str, list[object], dict[str, str]], list[dict]
]


class ExportSession:
    """Own exporter registration and page dispatch for one generation worker."""

    def __init__(self, worker_id: int) -> None:
        self._state_manager = ExporterStateManager(worker_id)
        self._products: dict[str, _ProductExporters] = {}

    def register(
        self,
        setup_context: ExporterContext,
        full_name: str,
        product_name: str,
        export_uri: str | None,
        targets: list[str],
    ) -> None:
        with_operation, without_operation = create_exporter_list(
            setup_context, product_name, export_uri, targets
        )
        self._register_exporters(full_name, with_operation, without_operation)

    def _register_exporters(
        self,
        full_name: str,
        with_operation: list[tuple[Exporter, ExportOperation]],
        without_operation: list[Exporter],
    ) -> None:
        self._products[full_name] = {
            "with_operation": with_operation,
            "without_operation": without_operation,
        }

    def children_first(self, full_name: str) -> bool:
        exporters = self._products[full_name]
        return any(operation is ExportOperation.DELETE for _, operation in exporters["with_operation"])

    def prepare_page(
        self,
        full_name: str,
        product_name: str,
        xml_rows: list[dict],
        metadata: dict[str, str],
    ) -> PreparedPage:
        json_rows = [convert_xml_dict_to_json_dict(row) for row in xml_rows]
        json_product = (product_name, json_rows, metadata) if metadata else (product_name, json_rows)
        # Reject an unregistered parent before Runtime can write its children.
        self._products[full_name]
        return json_product, xml_rows

    def dispatch_page(self, full_name: str, prepared_page: PreparedPage) -> None:
        json_product, xml_rows = prepared_page
        exporters = self._products[full_name]
        consume_exporters(
            json_product,
            xml_rows,
            full_name,
            exporters["with_operation"],
            exporters["without_operation"],
            self._state_manager,
        )


def consume_exporters(
    json_product: tuple,
    xml_rows: list[dict],
    full_name: str,
    exporters_with_operation: list[tuple[Exporter, ExportOperation]],
    exporters_without_operation: list[Exporter],
    exporter_state_manager: ExporterStateManager,
) -> None:
    """Dispatch one product page to its already-constructed exporters."""
    for exporter, operation in exporters_with_operation:
        if not isinstance(exporter, DatabaseExporter | MongoDBExporter):
            raise ValueError(f"Exporter does not support operation: {exporter}.{operation}")
        if isinstance(exporter, MongoDBExporter) and operation is ExportOperation.UPSERT:
            json_product = exporter.upsert(product=json_product)
        elif operation is ExportOperation.UPDATE:
            exporter.update(json_product)
        elif operation is ExportOperation.UPSERT:
            exporter.upsert(json_product)
        elif operation is ExportOperation.DELETE:
            exporter.delete(json_product)
        else:
            raise ValueError(f"Exporter does not support operation: {exporter}.{operation}")

    for exporter in exporters_without_operation:
        try:
            if isinstance(exporter, Memstore):
                continue
            if isinstance(exporter, XMLExporter):
                exporter.consume((json_product[0], xml_rows), full_name, exporter_state_manager)
            elif isinstance(exporter, UnifiedBufferedExporter):
                exporter.consume(json_product, full_name, exporter_state_manager)
            elif isinstance(
                exporter,
                ConsoleExporter | DatabaseExporter | MongoDBExporter | LogExporter | TestResultExporter,
            ):
                exporter.consume(json_product)
            else:
                raise TypeError(f"Unsupported exporter type: {type(exporter).__name__}")
        except Exception as e:
            logger.error(f"Error in exporter {type(exporter).__name__}: {str(e)}")
            raise ValueError(f"Error in exporter {type(exporter).__name__}: {e}") from e
