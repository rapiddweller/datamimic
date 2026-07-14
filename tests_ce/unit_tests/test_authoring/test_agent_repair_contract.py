# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.

"""Repair-oriented intent errors and compact reference projections."""

import json

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring.compiler import compile_authoring_spec
from datamimic_ce.authoring.contracts import (
    IntentValidationIssueCode,
    RunRequest,
    ScaffoldRequest,
)
from datamimic_ce.authoring.reference import ReferenceTopic
from datamimic_ce.authoring.reference_projection import (
    AuthoringExampleKind,
    ExampleReferenceQuery,
    ProductReferenceQuery,
    authoring_reference_projection,
    list_authoring_reference_queries,
    projection_catalog_is_exhaustive,
    reference_fragment_is_valid,
)
from datamimic_ce.authoring.service import run, scaffold
from datamimic_ce.authoring.spec import AuthoringSpecV1, ProductIntentKind
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


def test_every_compact_reference_is_exact_model_valid_and_small() -> None:
    assert projection_catalog_is_exhaustive()
    for query in list_authoring_reference_queries():
        projection = authoring_reference_projection(query)
        assert reference_fragment_is_valid(query)
        assert projection.allowed_fields
        assert set(projection.required_fields) <= set(projection.allowed_fields)
        assert len(projection.model_dump_json()) < 4_000


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
