# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.

"""Canonical AuthoringSpecV1 and pure compiler contracts."""

import ast
import inspect
from pathlib import Path

import pytest
from pydantic import ValidationError

import datamimic_ce.authoring.compiler as compiler_module
from datamimic_ce.authoring.compiler import compile_authoring_spec
from datamimic_ce.authoring.contracts import FileSourceBindingPlan, FileTargetBindingPlan
from datamimic_ce.authoring.dryrun import dry_run_source
from datamimic_ce.authoring.reference import capabilities_manifest, scaffold_reference
from datamimic_ce.authoring.spec import (
    AuthoringSpecV1,
    FileExportTarget,
    FileSource,
    MemstoreSource,
    authoring_spec_json_schema,
)
from datamimic_ce.constants.element_constants import EL_GENERATE
from datamimic_ce.exporters.exporter_util import buffered_exporter_names
from datamimic_ce.model.constraints import SourceFileFormat, source_file_format, supported_source_file_formats

_CANONICAL_SPEC = {
    "version": "1",
    "seed": 7,
    "products": [
        {
            "kind": "generated",
            "name": "customers",
            "count": 4,
            "targets": [{"kind": "file_export", "format": "JSON"}],
            "fields": [
                {
                    "kind": "increment",
                    "name": "customer_id",
                    "roles": [{"kind": "identifier"}],
                },
                {"kind": "person_name", "name": "name"},
                {
                    "kind": "weighted",
                    "name": "region",
                    "values": ["EU", "US"],
                    "weights": [0.6, 0.4],
                },
            ],
            "children": [
                {
                    "kind": "generated",
                    "name": "orders",
                    "count": 2,
                    "fields": [
                        {"kind": "increment", "name": "order_no"},
                        {
                            "kind": "script",
                            "name": "customer_id",
                            "script": "parent.customer_id",
                            "roles": [
                                {
                                    "kind": "foreign_key",
                                    "parent_product": "customers",
                                    "parent_field": "customer_id",
                                }
                            ],
                        },
                    ],
                }
            ],
        }
    ],
}


def test_authoring_spec_json_round_trip_preserves_intent() -> None:
    spec = AuthoringSpecV1.model_validate(_CANONICAL_SPEC)
    assert AuthoringSpecV1.model_validate_json(spec.model_dump_json()) == spec


def test_reference_and_capabilities_project_intent_spot() -> None:
    schema = authoring_spec_json_schema()
    assert capabilities_manifest()["authoring_spec"] == schema
    assert '"AuthoringSpecV1"' in scaffold_reference()


def test_compiler_is_byte_deterministic_and_plan_matches_relationships() -> None:
    spec = AuthoringSpecV1.model_validate(_CANONICAL_SPEC)
    first = compile_authoring_spec(spec)
    second = compile_authoring_spec(spec)
    assert first == second
    assert [product.name for product in first.plan.products] == ["customers", "orders"]
    assert [(edge.parent, edge.child) for edge in first.plan.relationships] == [
        ("customers", "orders")
    ]
    assert dry_run_source(first.xml, max_count=8, sample_rows=2).ok


@pytest.mark.parametrize(
    "raw",
    [
        {"version": "2", "products": []},
        {"generates": []},
        {"version": "1", "products": []},
        {
            "version": "1",
            "products": [
                {
                    "kind": "source",
                    "name": "rows",
                    "source": {"kind": "mongodb", "id": "mongo"},
                    "fields": [{"kind": "script", "name": "id", "script": "id"}],
                }
            ],
        },
    ],
)
def test_noncanonical_or_unsupported_intent_fails_closed(raw: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        AuthoringSpecV1.model_validate(raw)


def test_duplicate_fields_and_targets_fail_at_model_boundary() -> None:
    duplicate_fields = {
        "version": "1",
        "products": [
            {
                "kind": "generated",
                "name": "rows",
                "count": 1,
                "fields": [
                    {"kind": "increment", "name": "id"},
                    {"kind": "script", "name": "id", "script": "1"},
                ],
            }
        ],
    }
    duplicate_targets = {
        "version": "1",
        "products": [
            {
                "kind": "generated",
                "name": "rows",
                "count": 1,
                "fields": [{"kind": "increment", "name": "id"}],
                "targets": [
                    {"kind": "file_export", "format": "JSON"},
                    {"kind": "file_export", "format": "JSON"},
                ],
            }
        ],
    }
    for raw in (duplicate_fields, duplicate_targets):
        with pytest.raises(ValidationError, match="must be unique"):
            AuthoringSpecV1.model_validate(raw)


def test_source_and_exporter_facts_have_one_projection() -> None:
    formats = supported_source_file_formats(EL_GENERATE)
    assert formats[0] is SourceFileFormat.DBUNIT_XML
    assert source_file_format("dataset.dbunit.xml") is SourceFileFormat.DBUNIT_XML
    assert source_file_format("rows.fcw") is SourceFileFormat.FIXED_WIDTH
    schema_formats = set(
        authoring_spec_json_schema()["$defs"]["FileExportTarget"]["properties"]["format"]["enum"]
    )
    assert schema_formats == buffered_exporter_names()


def test_intent_and_plan_share_registered_exporter_validation() -> None:
    for exporter in buffered_exporter_names():
        assert FileExportTarget(format=exporter).format == exporter
        assert FileTargetBindingPlan(format=exporter).format == exporter
    for contract in (FileExportTarget, FileTargetBindingPlan):
        with pytest.raises(ValidationError, match="unsupported file exporter"):
            contract(format="BOGUS")


def test_intent_and_plan_share_runtime_source_classification() -> None:
    for file_format in supported_source_file_formats(EL_GENERATE):
        path = f"rows{file_format.value}"
        assert FileSource(path=path).path == path
        assert FileSourceBindingPlan(path=path).path == path
    for contract in (FileSource, FileSourceBindingPlan):
        with pytest.raises(ValidationError, match="runtime-supported source-file suffix"):
            contract(path="rows.parquet")
    with pytest.raises(ValidationError, match="dispatched as a file source"):
        MemstoreSource(id="rows.csv")


def test_compiler_has_no_transport_execution_or_file_io_dependencies() -> None:
    tree = ast.parse(inspect.getsource(compiler_module))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
    forbidden = ("datamimic_ce.cli", "datamimic_ce.mcp", "authoring.dryrun", "authoring.linter")
    assert not any(any(token in module for token in forbidden) for module in imported)
    assert "open(" not in inspect.getsource(compiler_module)


def test_model_package_never_imports_authoring() -> None:
    model_root = Path(compiler_module.__file__).parents[1] / "model"
    for path in model_root.glob("*.py"):
        assert "datamimic_ce.authoring" not in path.read_text(encoding="utf-8")
