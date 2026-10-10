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
    GenerateStatement,
)
from datamimic_ce.engine.io.api import ExportSession
from datamimic_ce.engine.io.contracts import ExportMetadata


def export_product_by_page(
    stmt: GenerateStatement,
    xml_result: dict[str, list[dict[str, object]]],
    export_session: ExportSession,
) -> None:
    """Dispatch a page and recurse in dependency-safe parent/child order."""
    xml_rows = xml_result[stmt.full_name]
    metadata: ExportMetadata = {}
    if stmt.target_entity:
        metadata[META_TARGET_ENTITY] = stmt.target_entity
    if stmt.selector:
        metadata[META_SELECTOR] = stmt.selector
    if stmt.type:
        metadata[META_TYPE] = stmt.type
    prepared_page = export_session.prepare_page(stmt.full_name, stmt.name, xml_rows, metadata)
    own_targets_delete = export_session.children_first(stmt.full_name)

    if own_targets_delete:
        for sub_stmt in stmt.sub_statements:
            _export_nested_products_by_page(sub_stmt, xml_result, export_session)

    export_session.dispatch_page(stmt.full_name, prepared_page)

    if not own_targets_delete:
        for sub_stmt in stmt.sub_statements:
            _export_nested_products_by_page(sub_stmt, xml_result, export_session)


def _export_nested_products_by_page(
    sub_stmt: object,
    xml_result: dict[str, list[dict[str, object]]],
    export_session: ExportSession,
) -> None:
    if isinstance(sub_stmt, GenerateStatement):
        if xml_result.get(sub_stmt.full_name):
            export_product_by_page(sub_stmt, xml_result, export_session)
    elif isinstance(sub_stmt, CompositeStatement):
        for child in sub_stmt.sub_statements:
            _export_nested_products_by_page(child, xml_result, export_session)
