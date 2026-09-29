"""Keep unused exporter implementations out of the IO facade."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

from datamimic_ce.engine.io import api as io_api

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
    "DataSourceRegistry": "datamimic_ce.engine.io.data_sources.data_source_registry",
    "ExporterConfig": "datamimic_ce.engine.io.exporters.core.exporter_config",
    "ExporterStateManager": "datamimic_ce.engine.io.exporters.core.exporter_state_manager",
    "UnifiedBufferedExporter": "datamimic_ce.engine.io.exporters.core.unified_buffered_exporter",
    "create_exporter_list": "datamimic_ce.engine.io.exporters.registry",
}


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
