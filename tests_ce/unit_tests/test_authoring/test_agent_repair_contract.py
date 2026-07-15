# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.

"""Repair-oriented intent errors and compact reference projections."""

import json

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring.compiler import compile_authoring_spec
from datamimic_ce.authoring.contracts import (
    AcceptanceStatus,
    IntentValidationIssueCode,
    RunRequest,
    ScaffoldRequest,
)
from datamimic_ce.authoring.reference import ReferenceTopic
from datamimic_ce.authoring.reference_projection import (
    AuthoringExampleKind,
    ExampleReferenceQuery,
    ProductReferenceQuery,
    SourceReferenceQuery,
    authoring_reference_projection,
    list_authoring_reference_queries,
    projection_catalog_is_exhaustive,
    reference_fragment_is_valid,
)
from datamimic_ce.authoring.service import run, scaffold
from datamimic_ce.authoring.spec import (
    AuthoringSpecV1,
    MemstoreSource,
    ProductIntentKind,
    SourceIntentKind,
)
from datamimic_ce.cli import app
from datamimic_ce.mcp.models import ReferenceArgs
from datamimic_ce.mcp.server import reference_impl


def test_unknown_generated_columns_returns_one_repairable_root_cause() -> None:
    result = scaffold(
        ScaffoldRequest(
            spec={
                "version": "1",
                "products": [
                    {
                        "kind": "generated",
                        "name": "customers",
                        "count": 5,
                        "columns": [{"name": "id", "kind": "increment"}],
                    }
                ],
            }
        )
    )

    assert result.ok is False
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.path == ("products", 0, "columns")
    assert issue.code is IntentValidationIssueCode.UNKNOWN_FIELD
    assert "fields" in issue.allowed_fields
    assert issue.expected_fragment is not None
    assert issue.expected_fragment["kind"] == "generated"
    assert issue.expected_fragment["fields"]
    assert result.error == issue.summary()
    assert "Tuple should have at least 1 item" not in result.error
    assert ".generated." not in result.error


def test_expectation_validation_paths_hide_union_implementation_labels() -> None:
    result = scaffold(
        ScaffoldRequest(
            spec={
                "version": "1",
                "products": [
                    {
                        "kind": "generated",
                        "name": "records",
                        "count": 1,
                        "fields": [{"kind": "increment", "name": "id"}],
                    }
                ],
                "expectations": [
                    {
                        "kind": "range",
                        "product": "records",
                        "field": "id",
                        "minimum": 0,
                        "upper": 10,
                    }
                ],
            }
        )
    )

    assert result.issues
    assert all("range" not in issue.path for issue in result.issues)
    assert {issue.path for issue in result.issues} == {
        ("expectations", 0, "maximum"),
        ("expectations", 0, "upper"),
    }


def test_nested_product_children_are_classified_as_unsupported_intent() -> None:
    result = scaffold(
        ScaffoldRequest(
            spec={
                "version": "1",
                "seed": 42,
                "products": [
                    {
                        "kind": "generated",
                        "name": "customers",
                        "count": 2,
                        "fields": [{"kind": "increment", "name": "customer_id"}],
                        "children": [
                            {
                                "kind": "generated",
                                "name": "accounts",
                                "count": 2,
                                "fields": [{"kind": "increment", "name": "account_id"}],
                                "children": [
                                    {
                                        "kind": "generated",
                                        "name": "transactions",
                                        "count": 2,
                                        "fields": [
                                            {"kind": "increment", "name": "transaction_id"}
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        )
    )

    assert result.ok is False
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.path == ("products", 0, "children", 0, "children")
    assert issue.code is IntentValidationIssueCode.UNSUPPORTED_INTENT
    assert issue.allowed_fields == ()
    assert issue.expected_fragment is None
    assert "cannot define child products" in issue.message


def test_children_on_nested_increment_field_remain_unknown_field() -> None:
    result = scaffold(
        ScaffoldRequest(
            spec={
                "version": "1",
                "products": [
                    {
                        "kind": "generated",
                        "name": "customers",
                        "count": 1,
                        "fields": [{"kind": "increment", "name": "customer_id"}],
                        "children": [
                            {
                                "kind": "generated",
                                "name": "accounts",
                                "count": 1,
                                "fields": [
                                    {
                                        "kind": "increment",
                                        "name": "account_id",
                                        "children": [],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        )
    )

    assert result.ok is False
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.path == (
        "products",
        0,
        "children",
        0,
        "fields",
        0,
        "children",
    )
    assert issue.code is IntentValidationIssueCode.UNKNOWN_FIELD


def _memstore_source_with_rejected_field(field: str) -> dict[str, object]:
    return {
        "version": "1",
        "seed": 42,
        "products": [
            {
                "kind": "generated",
                "name": "customers",
                "count": 2,
                "fields": [
                    {
                        "kind": "increment",
                        "name": "customer_id",
                        "roles": [{"kind": "identifier"}],
                    }
                ],
                "targets": [{"kind": "memstore", "id": "customer_mem"}],
            },
            {
                "kind": "source",
                "name": "customer_readback",
                "source": {
                    "kind": "memstore",
                    "id": "customer_mem",
                    field: "customers",
                },
                "fields": [
                    {
                        "kind": "script",
                        "name": "customer_id",
                        "script": "customer_id",
                        "roles": [
                            {
                                "kind": "foreign_key",
                                "parent_product": "customers",
                                "parent_field": "customer_id",
                            }
                        ],
                    }
                ],
            },
        ],
    }


def test_unknown_memstore_source_field_repairs_exact_owner_and_validates() -> None:
    raw = _memstore_source_with_rejected_field("type")

    result = scaffold(ScaffoldRequest(spec=raw))

    assert result.ok is False
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.path == ("products", 1, "source", "type")
    assert issue.code is IntentValidationIssueCode.UNKNOWN_FIELD
    assert issue.allowed_fields == tuple(MemstoreSource.model_fields)
    assert issue.repair is not None
    assert issue.repair.replacement_field == "product"
    assert issue.repair.rejected_value == "customers"
    assert issue.expected_fragment == issue.repair.corrected_fragment
    MemstoreSource.model_validate(issue.repair.corrected_fragment)

    corrected = json.loads(json.dumps(raw))
    source = corrected["products"][1]["source"]
    source[issue.repair.replacement_field] = source.pop("type")
    AuthoringSpecV1.model_validate(corrected)


def test_source_repair_survives_unrelated_root_validation_error() -> None:
    raw = _memstore_source_with_rejected_field("type")
    raw["unknown_root"] = True

    result = scaffold(ScaffoldRequest(spec=raw))

    assert len(result.issues) == 2
    issues = {issue.path: issue for issue in result.issues}
    source_issue = issues[("products", 1, "source", "type")]
    assert source_issue.repair is not None
    assert source_issue.repair.replacement_field == "product"
    assert source_issue.repair.rejected_value == "customers"
    root_issue = issues[("unknown_root",)]
    assert root_issue.code is IntentValidationIssueCode.UNKNOWN_FIELD
    assert root_issue.repair is None


def test_source_repair_rejects_candidate_with_owner_local_validation_error() -> None:
    raw = _memstore_source_with_rejected_field("type")
    source = raw["products"][1]["source"]
    source["type"] = 123

    result = scaffold(ScaffoldRequest(spec=raw))

    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.path == ("products", 1, "source", "type")
    assert issue.repair is None
    assert issue.expected_fragment is None


def test_unknown_memstore_source_field_without_validated_match_has_no_repair() -> None:
    result = scaffold(
        ScaffoldRequest(spec=_memstore_source_with_rejected_field("oops"))
    )

    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.code is IntentValidationIssueCode.UNKNOWN_FIELD
    assert issue.allowed_fields == tuple(MemstoreSource.model_fields)
    assert issue.repair is None
    assert issue.expected_fragment is None


def test_every_compact_reference_is_exact_model_valid_and_small() -> None:
    assert projection_catalog_is_exhaustive()
    for query in list_authoring_reference_queries():
        projection = authoring_reference_projection(query)
        assert reference_fragment_is_valid(query)
        assert projection.allowed_fields
        assert set(projection.required_fields) <= set(projection.allowed_fields)
        assert len(projection.model_dump_json()) < 4_000


def test_source_reference_queries_are_exhaustive_and_exact() -> None:
    source_queries = [
        query
        for query in list_authoring_reference_queries()
        if isinstance(query, SourceReferenceQuery)
    ]

    assert {query.kind for query in source_queries} == set(SourceIntentKind)
    assert len(source_queries) == len(SourceIntentKind)
    for query in source_queries:
        projection = authoring_reference_projection(query)
        assert projection.fragment["kind"] == query.kind
        assert reference_fragment_is_valid(query)


def test_cli_and_mcp_return_identical_compact_authoring_reference() -> None:
    query = ProductReferenceQuery(kind=ProductIntentKind.GENERATED)
    mcp_result = reference_impl(ReferenceArgs(topic=ReferenceTopic.AUTHORING, query=query))
    cli_result = CliRunner().invoke(
        app,
        [
            "reference",
            ReferenceTopic.AUTHORING,
            "--category",
            query.category,
            "--kind",
            query.kind,
        ],
    )

    assert mcp_result["ok"] is True
    assert cli_result.exit_code == 0, cli_result.stdout
    assert json.loads(cli_result.stdout) == json.loads(mcp_result["content"])


@pytest.mark.parametrize("extra_field", ["range", "generated", "script", "source", "unique"])
def test_discriminator_named_extra_field_remains_in_public_path(extra_field: str) -> None:
    result = scaffold(
        ScaffoldRequest(
            spec={
                "version": "1",
                "products": [
                    {
                        "kind": "generated",
                        "name": "records",
                        "count": 1,
                        "fields": [{"kind": "increment", "name": "id"}],
                        extra_field: True,
                    }
                ],
            }
        )
    )

    issue = result.issues[0]
    assert issue.path == ("products", 0, extra_field)
    assert issue.message == f"Unknown field '{extra_field}' for GeneratedProduct"


@pytest.mark.parametrize(
    ("field", "expectation", "expected_path"),
    [
        (
            {
                "kind": "increment",
                "name": "id",
                "roles": [{"kind": "identifier"}],
                "script": "1",
            },
            {"kind": "exact_count", "product": "records", "count": 1},
            ("products", 0, "fields", 0, "script"),
        ),
        (
            {
                "kind": "increment",
                "name": "id",
                "roles": [{"kind": "identifier", "unique": True}],
            },
            {"kind": "exact_count", "product": "records", "count": 1},
            ("products", 0, "fields", 0, "roles", 0, "unique"),
        ),
        (
            {
                "kind": "increment",
                "name": "id",
                "roles": [{"kind": "identifier"}],
            },
            {
                "kind": "exact_count",
                "product": "records",
                "count": 1,
                "source": "input.csv",
            },
            ("expectations", 0, "source"),
        ),
    ],
)
def test_nested_union_paths_remove_only_structural_branch_labels(
    field: dict[str, object],
    expectation: dict[str, object],
    expected_path: tuple[str | int, ...],
) -> None:
    result = scaffold(
        ScaffoldRequest(
            spec={
                "version": "1",
                "products": [
                    {
                        "kind": "generated",
                        "name": "records",
                        "count": 1,
                        "fields": [field],
                    }
                ],
                "expectations": [expectation],
            }
        )
    )
    assert expected_path in {issue.path for issue in result.issues}


def test_all_full_examples_compile() -> None:
    for kind in AuthoringExampleKind:
        query = ExampleReferenceQuery(kind=kind)
        spec = AuthoringSpecV1.model_validate(authoring_reference_projection(query).fragment)
        assert compile_authoring_spec(spec).xml


def test_memstore_pipeline_example_is_acceptance_ready() -> None:
    fragment = authoring_reference_projection(
        ExampleReferenceQuery(kind=AuthoringExampleKind.MEMSTORE_PIPELINE)
    ).fragment

    result = scaffold(ScaffoldRequest(spec=fragment, sample_rows=1))

    assert result.verified
    assert result.acceptance is not None
    memstore = next(
        item
        for item in result.acceptance.results
        if item.kind == "memstore_completeness"
    )
    assert memstore.status is AcceptanceStatus.PASS
    assert memstore.required_consumer_foreign_key is not None
    assert memstore.required_consumer_foreign_key.observed_count == 1


@pytest.mark.parametrize(
    "kind",
    [AuthoringExampleKind.FLAT, AuthoringExampleKind.NESTED, AuthoringExampleKind.TIME_SERIES],
)
def test_generated_examples_complete_bounded_run(kind: AuthoringExampleKind) -> None:
    fragment = authoring_reference_projection(ExampleReferenceQuery(kind=kind)).fragment
    result = scaffold(ScaffoldRequest(spec=fragment))
    assert result.ok is True
    assert result.verified is True


def test_source_example_executes_with_same_scope_column_access(tmp_path) -> None:
    (tmp_path / "input.csv").write_text("id\n1\n2\n", encoding="utf-8")
    fragment = authoring_reference_projection(
        ExampleReferenceQuery(kind=AuthoringExampleKind.SOURCE)
    ).fragment
    spec = AuthoringSpecV1.model_validate(fragment)
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(compile_authoring_spec(spec).xml, encoding="utf-8")

    result = run(RunRequest(path=str(descriptor), max_count=2, sample_rows=2))
    assert result.ok is True
    assert result.products[0].sample == [{"id": "1"}, {"id": "2"}]
