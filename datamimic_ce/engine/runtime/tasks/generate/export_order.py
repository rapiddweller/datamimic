# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.api import (
    META_SELECTOR,
    META_TARGET_ENTITY,
    META_TYPE,
    GenerateStatement,
)
from datamimic_ce.engine.io.api import ExportSession
from datamimic_ce.engine.io.contracts import ExportMetadata
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.contexts.products import GenerationResult, NestedExport


def export_product_by_page(
    stmt: GenerateStatement,
    xml_result: dict[str, list[dict[str, object]]],
    export_session: ExportSession,
    setup_context: SetupContext | None = None,
    statement_operation: bool = False,
) -> None:
    """Dispatch a page and recurse in dependency-safe parent/child order. ``statement_operation`` applies to this
    statement only: a one-time clear or drop, not a page of rows."""
    xml_rows = xml_result[stmt.full_name]
    if setup_context is not None:
        export_session.register(
            setup_context,
            stmt.full_name,
            stmt.target_entity or stmt.name,
            stmt.export_uri,
            list(stmt.targets),
            execution_id=str(id(stmt)),
        )
    children = xml_result.nested_exports if isinstance(xml_result, GenerationResult) else []
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
        for child in children:
            _export_nested_products_by_page(child, export_session, setup_context)

    export_session.dispatch_page(stmt.full_name, prepared_page, statement_operation)

    if not own_targets_delete:
        for child in children:
            _export_nested_products_by_page(child, export_session, setup_context)


def _export_nested_products_by_page(
    export: NestedExport,
    export_session: ExportSession,
    setup_context: SetupContext | None,
) -> None:
    result = GenerationResult()
    result[export.statement.full_name] = export.rows
    result.nested_exports = export.children
    export_product_by_page(export.statement, result, export_session, setup_context)
