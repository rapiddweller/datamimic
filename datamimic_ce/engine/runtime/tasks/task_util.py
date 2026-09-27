# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from __future__ import annotations

from datamimic_ce.engine.dsl.api import (
    META_SELECTOR,
    META_TARGET_ENTITY,
    META_TYPE,
    ExportOperation,
    GenerateStatement,
)
from datamimic_ce.engine.io.api import (
    ConsoleExporter,
    DatabaseExporter,
    Exporter,
    ExporterStateManager,
    LogExporter,
    Memstore,
    MongoDBExporter,
    TestResultExporter,
    UnifiedBufferedExporter,
    XMLExporter,
)
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.logging import logger


class TaskUtil:
    @staticmethod
    def export_product_by_page(
        root_context: SetupContext,
        stmt: GenerateStatement,
        xml_result: dict[str, list[dict]],
        exporter_state_manager: ExporterStateManager,
    ) -> None:
        """
        Export single page of product in generate statement.

        :param root_context: SetupContext instance.
        :param stmt: GenerateStatement instance.
        :param xml_result: Dictionary of product data.
        :param exporter_state_manager: ExporterStateManager instance.
        :return: None
        """
        # If product is in XML format, convert it to JSON
        json_result = [TaskUtil.convert_xml_dict_to_json_dict(product) for product in xml_result[stmt.full_name]]

        # Wrap product key and value into a tuple
        # for iterate database may have key, value, and other statement attribute info
        # Carry every routing hint that is set (not mutually exclusive): targetEntity/type name the
        # write collection/table, selector carries the query. A Mongo upsert needs BOTH the collection
        # (targetEntity) AND the filter (selector), so they must not shadow each other.
        metadata: dict = {}
        if stmt.target_entity:
            metadata[META_TARGET_ENTITY] = stmt.target_entity
        if stmt.selector:
            metadata[META_SELECTOR] = stmt.selector
        if stmt.type:
            metadata[META_TYPE] = stmt.type
        json_product = (stmt.name, json_result, metadata) if metadata else (stmt.name, json_result)

        # Create a unique cache key incorporating task_id and statement details
        exporters_cache_key = stmt.full_name

        # Get cached exporters
        exporters = root_context.task_exporters[exporters_cache_key]
        exporters["page_count"] += 1

        # A nested <generate> defers its page export to here (generate_worker skips it for
        # GenIterContext): this statement's own rows and its children's are ordered relative to
        # each other so neither direction of the FK constraint is violated:
        # - insert/update/upsert (any operation but delete): own rows first, then children -
        #   a child row's FK to the not-yet-existing parent would otherwise fail.
        # - delete: children FIRST, then own rows - a child row's FK to this (still existing)
        #   parent would otherwise block the parent's deletion.
        # Each recursion level re-checks its OWN targets, so a cascade of nested deletes becomes
        # deepest-first automatically. The operation itself comes from the same parsed
        # (exporter, operation) pairs the engine already built via ExporterUtil.parse_function_string
        # (see create_exporter_list) - not a re-parse of the raw target string.
        own_targets_delete = any(operation is ExportOperation.DELETE for _, operation in exporters["with_operation"])

        if own_targets_delete:
            for sub_stmt in stmt.sub_statements:
                TaskUtil._export_nested_products_by_page(root_context, sub_stmt, xml_result, exporter_state_manager)

        # Use cached exporters
        # Run exporters with operations first. Operations are ExportOperation members (parsed
        # once at the target boundary); dispatch is explicit per member — no getattr on a string.
        for exporter, operation in exporters["with_operation"]:
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
            else:  # unreachable while ExportOperation has exactly these members
                raise ValueError(f"Exporter does not support operation: {exporter}.{operation}")

        TaskUtil.exporter_without_operation(
            json_product,
            xml_result,
            stmt,
            exporters["without_operation"],
            exporter_state_manager,
        )

        if not own_targets_delete:
            for sub_stmt in stmt.sub_statements:
                TaskUtil._export_nested_products_by_page(root_context, sub_stmt, xml_result, exporter_state_manager)

    @staticmethod
    def _export_nested_products_by_page(
        root_context: SetupContext,
        sub_stmt,
        xml_result: dict,
        exporter_state_manager: ExporterStateManager,
    ) -> None:
        """Export a nested generate's page products (own rows already handled by the caller, either
        before or after this call - see export_product_by_page); walk through composite statements
        (condition/if) so a generate inside them is not missed."""
        from datamimic_ce.engine.dsl.api import CompositeStatement

        if isinstance(sub_stmt, GenerateStatement):
            if xml_result.get(sub_stmt.full_name):
                TaskUtil.export_product_by_page(root_context, sub_stmt, xml_result, exporter_state_manager)
        elif isinstance(sub_stmt, CompositeStatement):  # condition/if/else wrappers
            for child in sub_stmt.sub_statements:
                TaskUtil._export_nested_products_by_page(root_context, child, xml_result, exporter_state_manager)

    @staticmethod
    def exporter_without_operation(
        json_product: tuple,
        xml_result: dict,
        stmt: GenerateStatement,
        exporters_without_operation: list[Exporter],
        exporter_state_manager: ExporterStateManager,
    ):
        # Run exporters without operations
        for exporter in exporters_without_operation:
            try:
                # Skip lazy exporters
                if isinstance(exporter, Memstore):
                    continue
                elif isinstance(exporter, XMLExporter):
                    exporter.consume(
                        (json_product[0], xml_result[stmt.full_name]), stmt.full_name, exporter_state_manager
                    )
                elif isinstance(exporter, UnifiedBufferedExporter):
                    # every buffered exporter (JSON/CSV/TXT/XLSX/DbUnit/...) shares this consume
                    # signature; dispatch on the base class so new ones work without editing this list.
                    exporter.consume(json_product, stmt.full_name, exporter_state_manager)
                elif isinstance(
                    exporter,
                    ConsoleExporter | DatabaseExporter | MongoDBExporter | LogExporter | TestResultExporter,
                ):
                    exporter.consume(json_product)
                else:
                    raise TypeError(f"Unsupported exporter type: {type(exporter).__name__}")
            except Exception as e:
                # import traceback
                # traceback.print_exc()
                logger.error(f"Error in exporter {type(exporter).__name__}: {str(e)}")
                raise ValueError(f"Error in exporter {type(exporter).__name__}: {e}") from e

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
                    res[key] = TaskUtil.convert_xml_dict_to_json_dict(value)
                elif isinstance(value, list):
                    res[key] = [TaskUtil.convert_xml_dict_to_json_dict(v) if isinstance(v, dict) else v for v in value]
                else:
                    res[key] = value
        return res
