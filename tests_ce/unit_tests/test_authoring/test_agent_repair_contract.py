# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.

"""Repair-oriented canonical intent errors and schema-only discovery."""

import json

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring.contracts import (
    IntentValidationIssueCode,
    ProductReferenceQuery,
    ReferenceRequest,
    ReferenceTopic,
    ScaffoldRequest,
    SourceReferenceQuery,
)
from datamimic_ce.authoring.reference_projection import (
    authoring_reference_projection,
    list_authoring_reference_queries,
    projection_catalog_is_exhaustive,
)
from datamimic_ce.authoring.service import reference, scaffold
from datamimic_ce.authoring.spec import AuthoringSpecV1, MemstoreSource, ProductIntentKind, SourceIntentKind
from datamimic_ce.cli import app


def test_unknown_field_reports_exact_owner_without_synthetic_example() -> None:
    result = scaffold(ScaffoldRequest(spec={
        "version": "1",
        "products": [{
            "kind": "generated", "name": "customers", "count": 5,
            "columns": [{"name": "id", "kind": "increment"}],
        }],
    }))

    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.path == ("products", 0, "columns")
    assert issue.code is IntentValidationIssueCode.UNKNOWN_FIELD
    assert "fields" in issue.allowed_fields
    assert issue.repair is None


def test_expectation_paths_hide_union_implementation_labels() -> None:
    result = scaffold(ScaffoldRequest(spec={
        "version": "1",
        "products": [{
            "kind": "generated", "name": "records", "count": 1,
            "fields": [{"kind": "increment", "name": "id"}],
        }],
        "expectations": [{
            "kind": "range", "product": "records", "field": "id",
            "minimum": 0, "upper": 10,
        }],
    }))

    assert {issue.path for issue in result.issues} == {
        ("expectations", 0, "maximum"),
        ("expectations", 0, "upper"),
    }


def test_nested_product_children_are_unsupported_intent() -> None:
    result = scaffold(ScaffoldRequest(spec={
        "version": "1",
        "products": [{
            "kind": "generated", "name": "parents", "count": 1,
            "fields": [{"kind": "increment", "name": "id"}],
            "children": [{
                "kind": "generated", "name": "children", "count": 1,
                "fields": [{"kind": "increment", "name": "id"}],
                "children": [],
            }],
        }],
    }))

    issue = result.issues[0]
    assert issue.path == ("products", 0, "children", 0, "children")
    assert issue.code is IntentValidationIssueCode.UNSUPPORTED_INTENT
    assert issue.allowed_fields == ()


def _memstore_source_with_rejected_field(field: str) -> dict[str, object]:
    return {
        "version": "1",
        "products": [
            {
                "kind": "generated", "name": "customers", "count": 2,
                "fields": [{
                    "kind": "increment", "name": "customer_id",
                    "roles": [{"kind": "identifier"}],
                }],
                "targets": [{"kind": "memstore", "id": "customer_mem"}],
            },
            {
                "kind": "source", "name": "readback",
                "source": {"kind": "memstore", "id": "customer_mem", field: "customers"},
                "fields": [{
                    "kind": "script", "name": "customer_id", "script": "customer_id",
                    "roles": [{
                        "kind": "foreign_key", "parent_product": "customers",
                        "parent_field": "customer_id",
                    }],
                }],
            },
        ],
    }


def test_typo_repair_is_derived_from_and_validated_against_user_input() -> None:
    raw = _memstore_source_with_rejected_field("type")
    result = scaffold(ScaffoldRequest(spec=raw))

    issue = result.issues[0]
    assert issue.path == ("products", 1, "source", "type")
    assert issue.allowed_fields == tuple(MemstoreSource.model_fields)
    assert issue.repair is not None
    assert issue.repair.replacement_field == "product"
    assert issue.repair.rejected_value == "customers"
    MemstoreSource.model_validate(issue.repair.corrected_fragment)

    corrected = json.loads(json.dumps(raw))
    source = corrected["products"][1]["source"]
    source[issue.repair.replacement_field] = source.pop("type")
    AuthoringSpecV1.model_validate(corrected)


def test_unvalidated_field_guess_has_no_repair() -> None:
    result = scaffold(ScaffoldRequest(spec=_memstore_source_with_rejected_field("oops")))
    issue = result.issues[0]
    assert issue.allowed_fields == tuple(MemstoreSource.model_fields)
    assert issue.repair is None


def test_reference_catalog_is_schema_only_and_exhaustive() -> None:
    assert projection_catalog_is_exhaustive()
    for query in list_authoring_reference_queries():
        projection = authoring_reference_projection(query)
        assert projection.allowed_fields
        assert set(projection.required_fields) <= set(projection.allowed_fields)
        assert projection.json_schema["title"] == projection.model
        assert "fragment" not in projection.model_fields


def test_source_reference_queries_cover_canonical_union() -> None:
    queries = [
        query for query in list_authoring_reference_queries()
        if isinstance(query, SourceReferenceQuery)
    ]
    assert {query.kind for query in queries} == set(SourceIntentKind)


def test_cli_and_service_return_identical_schema_projection() -> None:
    query = ProductReferenceQuery(kind=ProductIntentKind.GENERATED)
    result = reference(ReferenceRequest(topic=ReferenceTopic.AUTHORING, query=query))
    cli_result = CliRunner().invoke(
        app,
        ["reference", ReferenceTopic.AUTHORING, "--category", query.category, "--kind", query.kind],
    )

    assert result.ok is True
    assert result.content is not None
    assert cli_result.exit_code == 0, cli_result.stdout
    assert json.loads(cli_result.stdout) == json.loads(result.content)


@pytest.mark.parametrize("extra_field", ["range", "generated", "script", "source", "unique"])
def test_discriminator_named_extra_field_remains_in_public_path(extra_field: str) -> None:
    result = scaffold(ScaffoldRequest(spec={
        "version": "1",
        "products": [{
            "kind": "generated", "name": "records", "count": 1,
            "fields": [{"kind": "increment", "name": "id"}],
            extra_field: True,
        }],
    }))
    assert result.issues[0].path == ("products", 0, extra_field)
