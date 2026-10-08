"""Keep unused exporter implementations out of the IO facade."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import get_type_hints

from datamimic_ce.engine.io import api as io_api
from datamimic_ce.engine.io.api import (
    database_count_table_length as direct_database_count_table_length,
)
from datamimic_ce.engine.io.api import (
    database_get_by_page_with_query as direct_database_get_by_page_with_query,
)
from datamimic_ce.engine.io.api import (
    is_database_client as direct_is_database_client,
)
from datamimic_ce.engine.io.contracts import SmokeExportRequest

ROOT = Path(__file__).resolve().parents[2]

CONCRETE_EXPORTERS = {
    "DatabaseExporter": "datamimic_ce.engine.io.exporters.database.database_exporter",
    "ConsoleExporter": "datamimic_ce.engine.io.exporters.diagnostics.console_exporter",
    "LogExporter": "datamimic_ce.engine.io.exporters.diagnostics.log_exporter",
    "MongoDBExporter": "datamimic_ce.engine.io.exporters.database.mongodb_exporter",
    "XMLExporter": "datamimic_ce.engine.io.exporters.formats.xml_exporter",
}

INTERNAL_EXPORT_HELPERS = {
    "consume_exporters": "datamimic_ce.engine.io.exporters.session",
    "convert_xml_dict_to_json_dict": "datamimic_ce.engine.io.exporters.core.serialization",
}

INTERNAL_IO_TYPES = {
    "ExporterConfig": "datamimic_ce.engine.io.exporters.core.exporter_config",
    "ExporterStateManager": "datamimic_ce.engine.io.exporters.core.exporter_state_manager",
    "UnifiedBufferedExporter": "datamimic_ce.engine.io.exporters.core.unified_buffered_exporter",
    "create_exporter_list": "datamimic_ce.engine.io.exporters.registry",
}

IO_ONLY_CLIENT_AND_COLLECTION_BINDINGS = {
    "database_count_query_length": "datamimic_ce.engine.io.clients.operations",
    "database_get_by_page_with_type": "datamimic_ce.engine.io.clients.operations",
    "database_get_random_rows_by_columns": "datamimic_ce.engine.io.clients.operations",
    "is_mongodb_client": "datamimic_ce.engine.io.clients.operations",
    "is_rdbms_client": "datamimic_ce.engine.io.clients.operations",
    "mongodb_count_collection": "datamimic_ce.engine.io.clients.operations",
    "resolve_source_collection": "datamimic_ce.engine.io.data_sources.boundary.entities",
}

IO_INTERNAL_SOURCE_BINDINGS = {
    "load_source_rows": "datamimic_ce.engine.io.files.readers",
    "weighted_csv_has_header": "datamimic_ce.engine.io.files.readers",
    "rdbms_count_source_query": "datamimic_ce.engine.io.clients.operations",
}


def test_io_root_hides_client_and_collection_operations_but_keeps_owners() -> None:
    for name, owner_name in IO_ONLY_CLIENT_AND_COLLECTION_BINDINGS.items():
        assert name not in io_api.__all__
        assert not hasattr(io_api, name)
        assert hasattr(importlib.import_module(owner_name), name)


def test_io_source_helpers_stay_internal_to_their_owners() -> None:
    for name, owner_name in IO_INTERNAL_SOURCE_BINDINGS.items():
        assert name not in io_api.__all__
        assert not hasattr(io_api, name)
        assert hasattr(importlib.import_module(owner_name), name)


def test_io_root_retains_live_database_script_operations() -> None:
    operations = importlib.import_module("datamimic_ce.engine.io.clients.operations")
    contracts = importlib.import_module("datamimic_ce.engine.io.contracts")
    assert direct_database_count_table_length is operations.database_count_table_length
    assert direct_database_get_by_page_with_query is operations.database_get_by_page_with_query
    assert direct_is_database_client is operations.is_database_client
    assert io_api.database_count_table_length is direct_database_count_table_length
    assert io_api.database_get_by_page_with_query is direct_database_get_by_page_with_query
    assert io_api.is_database_client is direct_is_database_client
    assert "execute_sql_script" in io_api.__all__
    assert io_api.execute_sql_script is operations.execute_sql_script
    assert "RegisteredClient" in io_api.__all__
    assert contracts.SqlScriptClient.__module__ == "datamimic_ce.engine.io.contracts"
    contract = json.loads(
        (ROOT / "docs/architecture/inner/io/architecture-contract.json").read_text(encoding="utf-8")
    )
    io_api_component = next(component for component in contract["components"] if component["id"] == "IO-API")
    assert "datamimic_ce.engine.io.api:RegisteredClient" in io_api_component["public"]
    assert "datamimic_ce.engine.io.api:execute_sql_script" in io_api_component["public"]
    contracts_component = next(component for component in contract["components"] if component["id"] == "IO-CONTRACTS")
    assert "datamimic_ce.engine.io.contracts:SqlScriptClient" in contracts_component["public"]


def test_io_root_exposes_only_the_runtime_used_row_iterator() -> None:
    selection = importlib.import_module("datamimic_ce.engine.io.data_sources.selection")
    assert "select_row_iterator" in io_api.__all__
    assert io_api.select_row_iterator is selection.select_row_iterator
    assert "select_rows" not in io_api.__all__

    contract = json.loads(
        (ROOT / "docs/architecture/inner/io/architecture-contract.json").read_text(encoding="utf-8")
    )
    io_api_component = next(component for component in contract["components"] if component["id"] == "IO-API")
    assert "datamimic_ce.engine.io.api:select_row_iterator" in io_api_component["public"]


def test_io_api_does_not_reexport_unused_concrete_exporters() -> None:
    for name, module_name in CONCRETE_EXPORTERS.items():
        assert name not in io_api.__all__
        assert not hasattr(io_api, name)
        assert hasattr(importlib.import_module(module_name), name)


def test_io_api_keeps_export_helpers_internal() -> None:
    for name, module_name in INTERNAL_EXPORT_HELPERS.items():
        assert name not in io_api.__all__
        assert not hasattr(io_api, name)
        assert hasattr(importlib.import_module(module_name), name)


def test_io_api_keeps_registry_and_exporter_implementation_types_internal() -> None:
    for name, module_name in INTERNAL_IO_TYPES.items():
        assert name not in io_api.__all__
        assert not hasattr(io_api, name)
        assert hasattr(importlib.import_module(module_name), name)


def test_io_api_exposes_exporter_context_support_type() -> None:
    owner = importlib.import_module("datamimic_ce.engine.io.exporters.core.exporter_context")
    assert "MemstoreProvider" in io_api.__all__
    assert io_api.MemstoreProvider is owner.MemstoreProvider
    contract = json.loads((ROOT / "architecture-contract.json").read_text(encoding="utf-8"))
    io_public = next(component["public"] for component in contract["components"] if component["id"] == "COMP-IO")
    assert all(not entry.startswith("datamimic_ce.engine.io.exporters.core.") for entry in io_public)


def test_smoke_export_request_uses_native_payload_annotations() -> None:
    annotations = get_type_hints(SmokeExportRequest)
    assert annotations["rows"] == list[dict[str, object]]
    assert annotations["params"] == dict[str, object]

    contracts = importlib.import_module("datamimic_ce.engine.io.contracts")
    assert "SmokeExportRows" not in contracts.__all__
    assert "SmokeExportParameters" not in contracts.__all__
    assert not hasattr(contracts, "SmokeExportRows")
    assert not hasattr(contracts, "SmokeExportParameters")


def test_exporter_registry_has_only_exact_memstore_visibility() -> None:
    contract = json.loads(
        (ROOT / "docs/architecture/inner/io/exporters/architecture-contract.json").read_text(encoding="utf-8")
    )
    components = {component["id"]: component for component in contract["components"]}
    assert components["EXPORTERS-MEMORY"]["public"] == [
        "datamimic_ce.engine.io.exporters.memory.memstore:Memstore"
    ]
    registry = components["EXPORTERS-REGISTRY"]
    assert any(requirement["component"] == "memory" for requirement in registry["requires"])
    assert all("Memstore" not in symbol for symbol in registry["public"])


def test_nested_exporter_contract_keeps_internal_owners() -> None:
    contract = json.loads(
        (ROOT / "docs/architecture/inner/io/exporters/architecture-contract.json").read_text(encoding="utf-8")
    )
    components = {component["id"]: component for component in contract["components"]}
    assert {
        "datamimic_ce.engine.io.exporters.core.exporter_config:ExporterConfig",
        "datamimic_ce.engine.io.exporters.core.exporter_state_manager:ExporterStateManager",
        "datamimic_ce.engine.io.exporters.core.unified_buffered_exporter:UnifiedBufferedExporter",
    } <= set(components["EXPORTERS-CORE"]["public"])
    assert (
        "datamimic_ce.engine.io.exporters.registry:create_exporter_list"
        in components["EXPORTERS-REGISTRY"]["public"]
    )


def test_smoke_export_open_values_keep_their_container_shapes() -> None:
    hints = get_type_hints(SmokeExportRequest)
    assert hints["params"] == dict[str, object]
    assert hints["rows"] == list[dict[str, object]]
