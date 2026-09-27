# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.api import (
    META_SELECTOR,
    META_TARGET_ENTITY,
    META_TYPE,
    CompositeStatement,
    ExportOperation,
    GenerateStatement,
)
from datamimic_ce.engine.io.api import ExporterStateManager, consume_exporters, convert_xml_dict_to_json_dict
from datamimic_ce.engine.runtime.contexts.context import SetupContext


def export_product_by_page(
    root_context: SetupContext,
    stmt: GenerateStatement,
    xml_result: dict[str, list[dict]],
    exporter_state_manager: ExporterStateManager,
) -> None:
    """Dispatch a page and recurse in dependency-safe parent/child order."""
    xml_rows = xml_result[stmt.full_name]
    json_rows = [convert_xml_dict_to_json_dict(product) for product in xml_rows]

    metadata: dict[str, str] = {}
    if stmt.target_entity:
        metadata[META_TARGET_ENTITY] = stmt.target_entity
    if stmt.selector:
        metadata[META_SELECTOR] = stmt.selector
    if stmt.type:
        metadata[META_TYPE] = stmt.type
    json_product = (stmt.name, json_rows, metadata) if metadata else (stmt.name, json_rows)

    exporters = root_context.task_exporters[stmt.full_name]
    exporters["page_count"] += 1
    exporters_with_operation = exporters["with_operation"]
    exporters_without_operation = exporters["without_operation"]
    own_targets_delete = any(operation is ExportOperation.DELETE for _, operation in exporters_with_operation)

    if own_targets_delete:
        for sub_stmt in stmt.sub_statements:
            _export_nested_products_by_page(root_context, sub_stmt, xml_result, exporter_state_manager)

    consume_exporters(
        json_product,
        xml_rows,
        stmt.full_name,
        exporters_with_operation,
        exporters_without_operation,
        exporter_state_manager,
    )

    if not own_targets_delete:
        for sub_stmt in stmt.sub_statements:
            _export_nested_products_by_page(root_context, sub_stmt, xml_result, exporter_state_manager)


def _export_nested_products_by_page(
    root_context: SetupContext,
    sub_stmt: object,
    xml_result: dict[str, list[dict]],
    exporter_state_manager: ExporterStateManager,
) -> None:
    if isinstance(sub_stmt, GenerateStatement):
        if xml_result.get(sub_stmt.full_name):
            export_product_by_page(root_context, sub_stmt, xml_result, exporter_state_manager)
    elif isinstance(sub_stmt, CompositeStatement):
        for child in sub_stmt.sub_statements:
            _export_nested_products_by_page(root_context, child, xml_result, exporter_state_manager)
