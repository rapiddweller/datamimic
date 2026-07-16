# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.

"""Repair-oriented canonical intent errors and schema-only discovery."""

import json

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring.contracts import (
    AuthoringReferenceCategory,
    FieldReferenceQuery,
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
    source_product_repair_guidance,
)
from datamimic_ce.authoring.script_semantics import current_scope_reference
from datamimic_ce.authoring.service import reference, scaffold
from datamimic_ce.authoring.spec import (
    AuthoringSpecV1,
    FieldIntentKind,
    MemstoreSource,
    ProductIntentKind,
    SourceIntentKind,
)
from datamimic_ce.cli import app


def test_unknown_field_reports_exact_owner_without_synthetic_example() -> None:
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

    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.path == ("products", 0, "columns")
    assert issue.code is IntentValidationIssueCode.UNKNOWN_FIELD
    assert "fields" in issue.allowed_fields
    assert issue.repair is None


def test_expectation_paths_hide_union_implementation_labels() -> None:
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

    assert {issue.path for issue in result.issues} == {
        ("expectations", 0, "maximum"),
        ("expectations", 0, "upper"),
    }


@pytest.mark.parametrize(
    ("path", "mutate", "expected_kinds"),
    [
        (
            ("products", 0),
            lambda spec: spec["products"][0].pop("kind"),
            ("generated", "source", "time_series"),
        ),
        (
            ("products", 0, "fields", 0),
            lambda spec: spec["products"][0]["fields"][0].pop("kind"),
            (
                "increment",
                "person_name",
                "person_email",
                "int_range",
                "decimal_range",
                "string_length",
                "values",
                "weighted",
                "pattern",
                "constant",
                "script",
                "nested_list",
            ),
        ),
        (
            ("expectations", 0),
            lambda spec: spec["expectations"][0].pop("kind"),
            ("exact_count", "per_parent_count", "unique", "foreign_key", "allowed_values", "range", "row_condition"),
        ),
    ],
)
def test_missing_discriminator_lists_the_live_union_vocabulary(path, mutate, expected_kinds) -> None:
    spec = {
        "version": "1",
        "products": [
            {
                "kind": "generated",
                "name": "records",
                "count": 1,
                "fields": [{"kind": "increment", "name": "id"}],
            }
        ],
        "expectations": [{"kind": "exact_count", "product": "records", "count": 1}],
    }
    mutate(spec)

    result = scaffold(ScaffoldRequest(spec=spec))

    issue = next(issue for issue in result.issues if issue.path == path)
    assert issue.code is IntentValidationIssueCode.INVALID_DISCRIMINATOR
    assert all(kind in issue.message for kind in expected_kinds)
    assert "reference authoring" in issue.message
    if path[0] == "expectations":
        assert "range(kind, product, field, minimum, maximum)" in issue.message


def test_invalid_discriminator_uses_typed_minimal_forms() -> None:
    result = scaffold(
        ScaffoldRequest(
            spec={
                "version": "1",
                "products": [
                    {
                        "kind": "generated",
                        "name": "records",
                        "count": 1,
                        "fields": [{"kind": "reference", "name": "id", "sourceKey": "id"}],
                    }
                ],
            }
        )
    )

    issue = next(issue for issue in result.issues if issue.path == ("products", 0, "fields", 0))

    assert issue.code is IntentValidationIssueCode.INVALID_DISCRIMINATOR
    assert issue.message.startswith("Invalid discriminator 'kind'.")
    assert "script(kind, name, script)" in issue.message
    assert "reference authoring" in issue.message


def _memstore_discriminator_spec() -> dict[str, object]:
    return {
        "version": "1",
        "products": [
            {
                "kind": "generated",
                "name": "records",
                "count": 1,
                "fields": [{"kind": "increment", "name": "id"}],
                "targets": [{"kind": "memstore", "id": "store"}],
            },
            {
                "kind": "source",
                "name": "readback",
                "source": {"kind": "memstore", "id": "store", "product": "records"},
                "fields": [{"kind": "script", "name": "id", "script": "this.id"}],
            },
        ],
    }


def test_missing_source_discriminator_minimal_forms_use_typed_projection_catalog() -> None:
    spec = _memstore_discriminator_spec()
    products = spec["products"]
    assert isinstance(products, list)
    readback = products[1]
    assert isinstance(readback, dict)
    readback["source"] = {"id": "store", "product": "records"}

    result = scaffold(ScaffoldRequest(spec=spec))

    issue = next(issue for issue in result.issues if issue.path == ("products", 1, "source"))
    assert "memstore(kind, id)" in issue.message


def test_missing_target_discriminator_minimal_forms_use_typed_projection_catalog() -> None:
    spec = _memstore_discriminator_spec()
    products = spec["products"]
    assert isinstance(products, list)
    records = products[0]
    assert isinstance(records, dict)
    records["targets"] = [{"id": "store"}]

    result = scaffold(ScaffoldRequest(spec=spec))

    issue = next(issue for issue in result.issues if issue.path == ("products", 0, "targets", 0))
    assert "memstore(kind, id)" in issue.message


def test_nested_product_children_are_unsupported_intent() -> None:
    result = scaffold(
        ScaffoldRequest(
            spec={
                "version": "1",
                "products": [
                    {
                        "kind": "generated",
                        "name": "parents",
                        "count": 1,
                        "fields": [{"kind": "increment", "name": "id"}],
                        "children": [
                            {
                                "kind": "generated",
                                "name": "children",
                                "count": 1,
                                "fields": [{"kind": "increment", "name": "id"}],
                                "children": [],
                            }
                        ],
                    }
                ],
            }
        )
    )

    issue = result.issues[0]
    assert issue.path == ("products", 0, "children", 0, "children")
    assert issue.code is IntentValidationIssueCode.UNSUPPORTED_INTENT
    assert issue.allowed_fields == ()


def _memstore_source_with_rejected_field(field: str) -> dict[str, object]:
    return {
        "version": "1",
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
                "name": "readback",
                "source": {"kind": "memstore", "id": "customer_mem", field: "customers"},
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


def test_exact_count_output_spelling_has_a_validated_count_repair() -> None:
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
                "expectations": [{"kind": "exact_count", "product": "records", "exact_count": 1}],
            }
        )
    )

    issue = next(issue for issue in result.issues if issue.path[-1] == "exact_count")
    assert issue.code is IntentValidationIssueCode.UNKNOWN_FIELD
    assert "did you mean 'count'?" in issue.message
    assert issue.repair is not None
    assert issue.repair.replacement_field == "count"


def test_unvalidated_field_guess_has_no_repair() -> None:
    result = scaffold(ScaffoldRequest(spec=_memstore_source_with_rejected_field("oops")))
    issue = result.issues[0]
    assert issue.allowed_fields == tuple(MemstoreSource.model_fields)
    assert issue.repair is None


@pytest.mark.parametrize(
    ("mutate", "expected_message"),
    [
        (lambda spec: spec["products"][1]["source"].pop("id"), "Missing required source.id"),
        (lambda spec: spec["products"][1].update({"count": 2}), "do not accept count"),
        (lambda spec: spec["products"][1].update({"fields": []}), "require at least one explicit field"),
    ],
)
def test_source_product_shape_errors_show_typed_memstore_guidance(mutate, expected_message) -> None:
    spec = _memstore_source_with_rejected_field("product")
    mutate(spec)

    result = scaffold(ScaffoldRequest(spec=spec))

    assert any(expected_message in issue.message for issue in result.issues)
    message = next(issue.message for issue in result.issues if expected_message in issue.message)
    assert message.endswith(source_product_repair_guidance(SourceIntentKind.MEMSTORE))
    assert "required source-product fields: " + ", ".join(
        authoring_reference_projection(
            ProductReferenceQuery(kind=ProductIntentKind.SOURCE)
        ).required_fields
    ) in message
    assert "memstore source required fields: " + ", ".join(
        authoring_reference_projection(
            SourceReferenceQuery(kind=SourceIntentKind.MEMSTORE)
        ).required_fields
    ) in message
    assert 'script="this.<column>"' in message


@pytest.mark.parametrize("source_kind", SourceIntentKind)
def test_source_product_repair_guidance_uses_each_typed_source_variant(source_kind: SourceIntentKind) -> None:
    guidance = source_product_repair_guidance(source_kind)
    source = authoring_reference_projection(SourceReferenceQuery(kind=source_kind))
    script = authoring_reference_projection(FieldReferenceQuery(kind=FieldIntentKind.SCRIPT))

    assert f"{source_kind.value} source required fields: {', '.join(source.required_fields)}" in guidance
    assert f"script field ({', '.join(script.required_fields)})" in guidance
    assert f'script="{current_scope_reference("<column>")}"' in guidance


def test_reference_catalog_is_schema_only_and_exhaustive() -> None:
    assert projection_catalog_is_exhaustive()
    for query in list_authoring_reference_queries():
        projection = authoring_reference_projection(query)
        assert projection.allowed_fields
        assert set(projection.required_fields) <= set(projection.allowed_fields)
        assert projection.json_schema["title"] == projection.model
        assert "fragment" not in projection.model_fields


def test_compact_authoring_reference_includes_variant_field_summaries() -> None:
    result = reference(ReferenceRequest(topic=ReferenceTopic.AUTHORING))

    assert result.ok is True
    assert result.content is not None
    content = json.loads(result.content)
    exact_count = next(
        variant
        for variant in content["variants"]
        if variant == {
            "category": "expectation",
            "kind": "exact_count",
            "required_fields": ["product", "count"],
            "allowed_fields": ["kind", "product", "count"],
        }
    )
    assert exact_count["kind"] == "exact_count"


def test_category_reference_lists_only_its_schema_owned_variants() -> None:
    result = reference(
        ReferenceRequest(topic=ReferenceTopic.AUTHORING, category=AuthoringReferenceCategory.FIELD)
    )

    assert result.ok is True
    assert result.category is AuthoringReferenceCategory.FIELD
    assert result.content is not None
    content = json.loads(result.content)
    assert content["category"] == "field"
    assert content["variants"]
    assert {variant["category"] for variant in content["variants"]} == {"field"}
    assert {variant["kind"] for variant in content["variants"]} == set(FieldIntentKind)


def test_time_series_projection_explains_series_and_field_domain_semantics() -> None:
    product = authoring_reference_projection(
        ProductReferenceQuery(kind=ProductIntentKind.TIME_SERIES)
    ).json_schema
    values = authoring_reference_projection(
        FieldReferenceQuery(kind=FieldIntentKind.VALUES)
    ).json_schema

    assert (
        "does not create an implicit data field, dimension, or value domain"
        in product["properties"]["series_count"]["description"]
    )
    assert "place that dimension's values on the same field" in product["properties"]["series_count"]["description"]
    assert "business-domain values" in values["properties"]["values"]["description"]
    assert "series_count" not in values["properties"]["values"]["description"]


def test_source_reference_queries_cover_canonical_union() -> None:
    queries = [query for query in list_authoring_reference_queries() if isinstance(query, SourceReferenceQuery)]
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


def test_cli_category_listing_matches_the_service_contract() -> None:
    result = reference(
        ReferenceRequest(topic=ReferenceTopic.AUTHORING, category=AuthoringReferenceCategory.FIELD)
    )
    cli_result = CliRunner().invoke(app, ["reference", "authoring", "--category", "field"])

    assert result.ok is True
    assert result.content is not None
    assert cli_result.exit_code == 0, cli_result.stdout
    assert json.loads(cli_result.stdout) == json.loads(result.content)


def test_invalid_authoring_reference_queries_list_the_live_taxonomy() -> None:
    runner = CliRunner()

    unknown_category = runner.invoke(
        app,
        ["reference", "authoring", "--category", "entity", "--kind", "record"],
    )
    assert unknown_category.exit_code == 2
    assert all(category.value in unknown_category.output for category in AuthoringReferenceCategory)

    unknown_kind = runner.invoke(
        app,
        ["reference", "authoring", "--category", "field", "--kind", "enum"],
    )
    assert unknown_kind.exit_code == 1
    assert all(kind.value in unknown_kind.output for kind in FieldIntentKind)


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
    assert result.issues[0].path == ("products", 0, extra_field)
