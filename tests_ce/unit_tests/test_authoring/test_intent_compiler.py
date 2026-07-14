# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Gate-C contracts for the authoring Intent SPOT and pure compiler."""

from __future__ import annotations

import ast
import dataclasses
import inspect
from pathlib import Path

import pytest
from pydantic import ValidationError

import datamimic_ce.authoring.compiler as compiler_module
import datamimic_ce.authoring.normalization as normalization_module
import datamimic_ce.authoring.rules.cross_statement as cross_statement_module
from datamimic_ce.authoring.compiler import CompileError, compile_authoring_spec
from datamimic_ce.authoring.contracts import (
    AllowedValuesAcceptancePlan,
    CompilePlan,
    ExactCountAcceptancePlan,
    FileSourceBindingPlan,
    FileTargetBindingPlan,
    ForeignKeyRolePlan,
    GeneratedProductCompilePlan,
    LeafFieldPlan,
    MemstoreSourceBindingPlan,
    NestedListFieldPlan,
    RangeAcceptancePlan,
    SourceProductCompilePlan,
    TimeSeriesProductCompilePlan,
)
from datamimic_ce.authoring.dryrun import dry_run_source
from datamimic_ce.authoring.normalization import normalize_authoring_spec
from datamimic_ce.authoring.reference import capabilities_manifest, scaffold_reference
from datamimic_ce.authoring.schema import SchemaIndex, build_schema_index
from datamimic_ce.authoring.spec import (
    AuthoringSpecV1,
    FieldIntentKind,
    FileExportTarget,
    FileSource,
    MemstoreSource,
    authoring_spec_json_schema,
)
from datamimic_ce.constants.element_constants import EL_GENERATE
from datamimic_ce.exporters.exporter_util import buffered_exporter_names
from datamimic_ce.model.constraints import (
    SourceFileFormat,
    source_file_format,
    supported_source_file_formats,
)

_V1_SPEC = {
    "version": "1",
    "seed": 7,
    "products": [
        {
            "kind": "generated",
            "name": "customers",
            "count": 8,
            "targets": [
                {"kind": "memstore", "id": "customer_mem"},
                {"kind": "file_export", "format": "JSON"},
            ],
            "fields": [
                {
                    "kind": "increment",
                    "name": "customer_id",
                    "roles": [{"kind": "identifier"}],
                },
                {"kind": "person_name", "name": "name"},
                {"kind": "person_email", "name": "email"},
                {"kind": "int_range", "name": "age", "minimum": 18, "maximum": 90},
                {
                    "kind": "decimal_range",
                    "name": "balance",
                    "minimum": "0.00",
                    "maximum": "999.99",
                },
                {
                    "kind": "string_length",
                    "name": "note",
                    "minimum": 2,
                    "maximum": 12,
                },
                {"kind": "values", "name": "tier", "values": ["A", "B"]},
                {
                    "kind": "weighted",
                    "name": "region",
                    "values": ["EU", "US"],
                    "weights": [0.6, 0.4],
                },
                {"kind": "pattern", "name": "code", "pattern": "[A-Z]{3}"},
                {"kind": "constant", "name": "active", "value": "true"},
                {"kind": "script", "name": "double_age", "script": "age * 2"},
                {
                    "kind": "nested_list",
                    "name": "tags",
                    "minimum_count": 1,
                    "maximum_count": 2,
                    "fields": [{"kind": "pattern", "name": "tag", "pattern": "[a-z]{4}"}],
                },
            ],
            "children": [
                {
                    "kind": "generated",
                    "name": "orders",
                    "count": 2,
                    "relationship": {"kind": "nested"},
                    "targets": [{"kind": "file_export", "format": "JSON"}],
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
        },
        {
            "kind": "source",
            "name": "customer_copy",
            "source": {
                "kind": "memstore",
                "id": "customer_mem",
                "product": "customers",
                "distribution": "ordered",
            },
            "targets": [{"kind": "file_export", "format": "CSV"}],
            "fields": [{"kind": "script", "name": "customer_id", "script": "customer_id"}],
        },
        {
            "kind": "time_series",
            "name": "readings",
            "series_count": 2,
            "window": {
                "start": "2025-01-01T00:00:00",
                "end": "2025-01-02T00:00:00",
                "interval": "PT1H",
            },
            "fields": [
                {
                    "kind": "script",
                    "name": "at",
                    "script": "ts.now",
                    "roles": [{"kind": "timestamp"}],
                }
            ],
        },
    ],
    "expectations": [
        {"kind": "exact_count", "product": "customers", "count": 8},
        {
            "kind": "per_parent_count",
            "parent_product": "customers",
            "child_product": "orders",
            "count": 2,
        },
        {"kind": "unique", "product": "customers", "field": "customer_id"},
        {
            "kind": "foreign_key",
            "child_product": "orders",
            "child_field": "customer_id",
            "parent_product": "customers",
            "parent_field": "customer_id",
        },
        {
            "kind": "allowed_values",
            "product": "customers",
            "field": "tier",
            "values": ["A", "B"],
        },
        {
            "kind": "range",
            "product": "customers",
            "field": "age",
            "minimum": 18,
            "maximum": 90,
        },
        {
            "kind": "row_condition",
            "product": "customers",
            "condition": "age >= 18",
            "result_type": "bool",
        },
    ],
}


def test_authoring_spec_v1_json_round_trip_preserves_discriminated_intent() -> None:
    spec = AuthoringSpecV1.model_validate(_V1_SPEC)

    dumped = spec.model_dump(mode="json")
    restored = AuthoringSpecV1.model_validate(dumped)

    assert restored == spec
    assert [product.kind for product in restored.products] == [
        "generated",
        "source",
        "time_series",
    ]
    assert {expectation.kind for expectation in restored.expectations} == {
        "exact_count",
        "per_parent_count",
        "unique",
        "foreign_key",
        "allowed_values",
        "range",
        "row_condition",
    }


def test_field_intent_kind_spot_drives_canonical_and_legacy_inputs() -> None:
    canonical = AuthoringSpecV1.model_validate(
        {
            "version": "1",
            "products": [
                {
                    "kind": "generated",
                    "name": "rows",
                    "count": 1,
                    "fields": [{"kind": "increment", "name": "id"}],
                }
            ],
        }
    )
    legacy = normalize_authoring_spec(
        {
            "generates": [
                {
                    "name": "rows",
                    "count": 1,
                    "fields": [{"kind": "id", "name": "id"}],
                }
            ]
        }
    )

    assert canonical.products[0].fields[0].kind is FieldIntentKind.INCREMENT
    assert legacy.spec is not None
    assert legacy.spec.products[0].fields[0].kind is FieldIntentKind.INCREMENT
    assert "_CANONICAL_KINDS" not in vars(normalization_module)


def test_legacy_field_kind_does_not_coerce_non_string_json_values() -> None:
    result = normalize_authoring_spec(
        {
            "generates": [
                {
                    "name": "rows",
                    "count": 1,
                    "fields": [{"kind": 1, "name": "id"}],
                }
            ]
        }
    )

    assert result.spec is None
    assert any("unsupported field kind '1'" in error for error in result.errors)


def test_reference_and_capabilities_project_the_intent_spot() -> None:
    schema = authoring_spec_json_schema()

    assert capabilities_manifest()["authoring_spec"] == schema
    rendered = scaffold_reference()
    assert "AuthoringSpecV1" in rendered
    assert '"AuthoringSpecV1"' in rendered
    assert '"version"' in rendered


def test_compiler_is_byte_deterministic_and_builds_complete_plan() -> None:
    spec = AuthoringSpecV1.model_validate(_V1_SPEC)

    first = compile_authoring_spec(spec)
    second = compile_authoring_spec(spec)

    assert first.xml == second.xml
    assert first.plan == second.plan
    products = {product.name: product for product in first.plan.products}
    assert products["customers"].children == ["orders"]
    assert products["customers"].static_count == 8
    tags = next(field for field in products["customers"].fields if field.name == "tags")
    assert (tags.minimum_count, tags.maximum_count) == (1, 2)
    assert products["orders"].parent == "customers"
    assert products["orders"].count_per_parent == 2
    assert products["orders"].static_count == 16
    assert products["customer_copy"].static_count == 8
    assert products["customer_copy"].source is not None
    assert products["customer_copy"].source.kind == "memstore"
    assert products["readings"].static_count == 48
    assert {(edge.kind, edge.parent, edge.child) for edge in first.plan.relationships} == {
        ("nested", "customers", "orders"),
        ("memstore_source", "customers", "customer_copy"),
    }
    assert any(
        item.kind == "foreign_key" and item.product == "orders" and item.parent_product == "customers"
        for item in first.plan.derived_acceptance
    )
    assert CompilePlan.model_validate(first.plan.model_dump(mode="json")) == first.plan


def test_values_and_weighted_literals_round_trip_through_real_runtime() -> None:
    special_values = {
        "singleton": "only",
        "backslash": r"C:\temp\new\file.txt",
        "quotes": "single ' and double \"",
        "controls": "line one\nline two\tend\x00",
    }
    fields: list[dict] = []
    for suffix, value in special_values.items():
        fields.extend(
            [
                {"kind": "values", "name": f"values_{suffix}", "values": [value]},
                {
                    "kind": "weighted",
                    "name": f"weighted_{suffix}",
                    "values": [value],
                    "weights": [1],
                },
            ]
        )
    spec = AuthoringSpecV1.model_validate(
        {
            "version": "1",
            "seed": 7,
            "products": [
                {
                    "kind": "generated",
                    "name": "rows",
                    "count": 1,
                    "fields": fields,
                }
            ],
        }
    )

    compiled = compile_authoring_spec(spec)
    runtime = dry_run_source(compiled.xml, max_count=1, sample_rows=1)

    assert runtime.ok, [(item.rule, item.message) for item in runtime.diagnostics]
    sample = runtime.products[0].sample[0]
    for suffix, value in special_values.items():
        assert sample[f"values_{suffix}"] == value
        assert sample[f"weighted_{suffix}"] == value


def test_compile_plan_dtos_reject_invalid_direct_construction() -> None:
    valid_field = LeafFieldPlan(name="id", kind="increment")
    valid_source = MemstoreSourceBindingPlan(id="rows")

    with pytest.raises(ValidationError):
        LeafFieldPlan(name="", kind="increment")
    with pytest.raises(ValidationError):
        GeneratedProductCompilePlan(
            name="rows",
            fields=[valid_field],
            static_count=-1,
        )
    with pytest.raises(ValidationError):
        NestedListFieldPlan(
            name="items",
            minimum_count=2,
            maximum_count=1,
        )
    with pytest.raises(ValidationError):
        GeneratedProductCompilePlan(
            name="rows",
            fields=[valid_field],
            static_count="3",
        )
    with pytest.raises(ValidationError):
        ForeignKeyRolePlan(parent_product="", parent_field="id")
    with pytest.raises(ValidationError):
        SourceProductCompilePlan(
            name="rows",
            fields=[valid_field],
            static_count=-1,
            source=valid_source,
        )
    with pytest.raises(ValidationError):
        SourceProductCompilePlan(
            name="rows",
            fields=[],
            static_count=0,
            source=valid_source,
        )
    with pytest.raises(ValidationError):
        TimeSeriesProductCompilePlan(
            name="rows",
            fields=[valid_field],
            static_count=0,
            series_count=1,
        )
    with pytest.raises(ValidationError):
        ExactCountAcceptancePlan(product="rows", exact_count=-1)
    with pytest.raises(ValidationError):
        AllowedValuesAcceptancePlan(product="rows", field="state", allowed_values=[])
    with pytest.raises(ValidationError):
        RangeAcceptancePlan(product="rows", field="amount", minimum="2", maximum="1")
    with pytest.raises(ValidationError):
        CompilePlan(products=[])


def _minimal_compile_plan_product(name: str = "rows") -> dict:
    return {
        "kind": "generated",
        "name": name,
        "fields": [{"kind": "increment", "name": "id"}],
        "targets": [],
        "static_count": 1,
    }


def test_compile_plan_rejects_duplicate_products_in_isolation() -> None:
    with pytest.raises(ValidationError, match="duplicate product name 'rows'"):
        CompilePlan.model_validate(
            {
                "products": [
                    _minimal_compile_plan_product(),
                    _minimal_compile_plan_product(),
                ]
            }
        )


def test_compile_plan_rejects_dangling_relationship_in_isolation() -> None:
    with pytest.raises(ValidationError, match="relationship references unknown product 'missing'"):
        CompilePlan.model_validate(
            {
                "products": [_minimal_compile_plan_product()],
                "relationships": [
                    {"kind": "nested", "parent": "rows", "child": "missing"}
                ],
            }
        )


def test_compile_plan_rejects_dangling_acceptance_product_in_isolation() -> None:
    with pytest.raises(
        ValidationError,
        match="derived acceptance references unknown product 'missing'",
    ):
        CompilePlan.model_validate(
            {
                "products": [_minimal_compile_plan_product()],
                "derived_acceptance": [
                    {"kind": "exact_count", "product": "missing", "exact_count": 1}
                ],
            }
        )


def test_compile_plan_rejects_dangling_unique_field_in_isolation() -> None:
    with pytest.raises(
        ValidationError,
        match="unique acceptance references unknown field 'missing' on product 'rows'",
    ):
        CompilePlan.model_validate(
            {
                "products": [_minimal_compile_plan_product()],
                "derived_acceptance": [
                    {
                        "kind": "unique",
                        "product": "rows",
                        "field": "missing",
                        "scope": "global",
                    }
                ],
            }
        )


@pytest.mark.parametrize(
    "payload",
    [
        {
            "products": [
                {
                    "kind": "source",
                    "name": "rows",
                    "fields": [],
                    "targets": [],
                    "static_count": None,
                    "source": {"kind": "file", "distribution": "ordered"},
                }
            ]
        },
        {
            "products": [],
            "relationships": [
                {
                    "kind": "nested",
                    "parent": "parents",
                    "child": "children",
                    "source_id": "impossible",
                }
            ],
        },
        {
            "products": [],
            "derived_acceptance": [{"kind": "unique", "product": "rows", "scope": "global"}],
        },
        {
            "products": [
                {
                    "kind": "generated",
                    "name": "rows",
                    "fields": [],
                    "targets": [{"kind": "file_export", "format": "BOGUS"}],
                    "static_count": 1,
                }
            ]
        },
        {
            "products": [
                {
                    "kind": "source",
                    "name": "rows",
                    "fields": [],
                    "targets": [],
                    "static_count": None,
                    "source": {
                        "kind": "file",
                        "path": "rows.parquet",
                        "distribution": "ordered",
                    },
                }
            ]
        },
        {
            "products": [
                {
                    "kind": "source",
                    "name": "rows",
                    "fields": [],
                    "targets": [],
                    "static_count": None,
                    "source": {
                        "kind": "memstore",
                        "id": "rows.csv",
                        "distribution": "ordered",
                    },
                }
            ]
        },
    ],
)
def test_compile_plan_rejects_optional_invalid_union_states(payload: dict) -> None:
    with pytest.raises(ValidationError):
        CompilePlan.model_validate(payload)


def _nested_unique_spec(*, maximum: int, roles: list[dict] | None = None) -> AuthoringSpecV1:
    child_field: dict = {
        "kind": "int_range",
        "name": "order_no",
        "minimum": 1,
        "maximum": maximum,
        "unique": True,
    }
    if roles is not None:
        child_field["roles"] = roles
    return AuthoringSpecV1.model_validate(
        {
            "version": "1",
            "products": [
                {
                    "kind": "generated",
                    "name": "customers",
                    "count": 8,
                    "fields": [{"kind": "increment", "name": "customer_id"}],
                    "children": [
                        {
                            "kind": "generated",
                            "name": "orders",
                            "count": 2,
                            "fields": [child_field],
                        }
                    ],
                }
            ],
            "expectations": [
                {
                    "kind": "unique",
                    "product": "orders",
                    "field": "order_no",
                    "scope": "per_parent",
                }
            ],
        }
    )


def test_nested_unique_capacity_is_global_not_per_parent() -> None:
    with pytest.raises(CompileError, match="only 2 possible values.*requires 16"):
        compile_authoring_spec(_nested_unique_spec(maximum=2))

    spec = _nested_unique_spec(maximum=16)
    result = compile_authoring_spec(spec)
    derived = [item for item in result.plan.derived_acceptance if item.kind == "unique" and item.product == "orders"]

    assert len(derived) == 1
    assert derived[0].scope == "global"
    assert spec.expectations[0].scope == "per_parent"


def test_identifier_role_derives_unique_once_and_nested_increment_fails_closed() -> None:
    top_level = AuthoringSpecV1.model_validate(
        {
            "version": "1",
            "products": [
                {
                    "kind": "generated",
                    "name": "rows",
                    "count": 2,
                    "fields": [
                        {
                            "kind": "int_range",
                            "name": "id",
                            "minimum": 1,
                            "maximum": 2,
                            "unique": True,
                            "roles": [{"kind": "identifier"}],
                        }
                    ],
                }
            ],
        }
    )
    result = compile_authoring_spec(top_level)
    unique = [item for item in result.plan.derived_acceptance if item.kind == "unique"]
    assert len(unique) == 1

    invalid = {
        "version": "1",
        "products": [
            {
                "kind": "generated",
                "name": "parents",
                "count": 2,
                "fields": [{"kind": "increment", "name": "id"}],
                "children": [
                    {
                        "kind": "generated",
                        "name": "children",
                        "count": 2,
                        "fields": [
                            {
                                "kind": "increment",
                                "name": "local_id",
                                "roles": [{"kind": "identifier"}],
                            }
                        ],
                    }
                ],
            }
        ],
    }
    with pytest.raises(ValidationError, match="local per parent"):
        AuthoringSpecV1.model_validate(invalid)


def test_nested_composite_script_may_claim_identifier_role() -> None:
    raw = {
        "version": "1",
        "products": [
            {
                "kind": "generated",
                "name": "parents",
                "count": 2,
                "fields": [{"kind": "increment", "name": "id"}],
                "children": [
                    {
                        "kind": "generated",
                        "name": "children",
                        "count": 2,
                        "fields": [
                            {
                                "kind": "script",
                                "name": "id",
                                "script": "parent.id * 10 + 1",
                                "roles": [{"kind": "identifier"}],
                            }
                        ],
                    }
                ],
            }
        ],
    }
    result = compile_authoring_spec(AuthoringSpecV1.model_validate(raw))

    unique = [item for item in result.plan.derived_acceptance if item.kind == "unique"]
    assert [(item.product, item.field, item.scope) for item in unique] == [("children", "id", "global")]


def test_compile_plan_records_file_source_cardinality_as_unknown() -> None:
    spec = AuthoringSpecV1.model_validate(
        {
            "version": "1",
            "products": [
                {
                    "kind": "source",
                    "name": "rows",
                    "source": {"kind": "file", "path": "input.csv"},
                    "fields": [{"kind": "script", "name": "id", "script": "id"}],
                }
            ],
        }
    )

    result = compile_authoring_spec(spec)

    assert result.plan.products[0].static_count is None
    assert result.plan.unresolved[0].product == "rows"
    assert result.plan.unresolved[0].aspect == "cardinality"
    assert "requires I/O" in result.plan.unresolved[0].reason


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ({"version": "2", "products": []}, "version"),
        (
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
            "mongodb",
        ),
        (
            {
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
            },
            "children",
        ),
        (
            {
                "generates": [
                    {
                        "name": "rows",
                        "count": 2,
                        "fields": [
                            {
                                "kind": "script",
                                "name": "seat",
                                "script": "random.unique(1, 10)",
                            }
                        ],
                    }
                ]
            },
            "invented unique helper",
        ),
        (
            {
                "generates": [
                    {
                        "name": "rows",
                        "count": 2,
                        "source": "input.csv",
                        "fields": [{"kind": "script", "name": "id", "script": "id"}],
                    }
                ]
            },
            "cannot define count",
        ),
        (
            {
                "generates": [
                    {
                        "name": "rows",
                        "count": 2,
                        "source_type": "orders",
                        "fields": [{"kind": "increment", "name": "id"}],
                    }
                ]
            },
            "without a source",
        ),
        (
            {
                "version": "1",
                "products": [
                    {
                        "kind": "generated",
                        "name": "rows",
                        "count": 1,
                        "fields": [{"kind": "increment", "name": "id"}],
                    }
                ],
                "expectations": [{"kind": "unique", "product": "rows", "field": "missing"}],
            },
            "unknown field 'missing'",
        ),
    ],
)
def test_unsupported_or_ambiguous_intent_fails_closed(raw: dict, message: str) -> None:
    result = normalize_authoring_spec(raw)

    assert result.spec is None
    assert any(message in error for error in result.errors)


def test_legacy_happy_path_has_visible_deterministic_notes() -> None:
    raw = {
        "rngSeed": 3,
        "generate": {
            "name": "customers",
            "count": 2,
            "target": "JSON",
            "columns": {"field": "customer_id", "type": "id"},
        },
    }

    first = normalize_authoring_spec(raw)
    second = normalize_authoring_spec(raw)

    assert first == second
    assert first.spec is not None
    assert first.spec.products[0].kind == "generated"
    assert first.notes == (
        "legacy scaffold document normalized to AuthoringSpecV1",
        "root key 'rngSeed' normalized to 'seed'",
        "root key 'generate' normalized to 'generates'",
        "object-shaped 'generates' normalized to a one-item list",
        "generate 'customers': key 'columns' normalized to 'fields'",
        "object-shaped 'fields of generate 'customers'' normalized to a one-item list",
        "field 'customer_id': key 'field' normalized to 'name'",
        "field 'customer_id': key 'type' normalized to 'kind'",
        "field 'customer_id': kind 'id' normalized to 'increment'",
    )


@pytest.mark.parametrize("script", ["customer_unique_key + 1", "customer_unique_key()"])
def test_legacy_script_identifier_containing_unique_is_not_rejected(script: str) -> None:
    result = normalize_authoring_spec(
        {
            "generates": [
                {
                    "name": "rows",
                    "count": 1,
                    "fields": [{"kind": "script", "name": "value", "script": script}],
                }
            ]
        }
    )
    assert result.errors == ()
    assert result.spec is not None


@pytest.mark.parametrize("script", ["random.unique(1, 10)", "unique_range(1, 10)"])
def test_legacy_invented_unique_helper_call_is_rejected(script: str) -> None:
    result = normalize_authoring_spec(
        {
            "generates": [
                {
                    "name": "rows",
                    "count": 1,
                    "fields": [{"kind": "script", "name": "value", "script": script}],
                }
            ]
        }
    )
    assert any("invented unique helper" in error for error in result.errors)


@pytest.mark.parametrize(
    "fields",
    [
        [
            {"kind": "increment", "name": "id"},
            {"kind": "script", "name": "id", "script": "1"},
        ],
        [
            {
                "kind": "nested_list",
                "name": "items",
                "minimum_count": 1,
                "maximum_count": 1,
                "fields": [
                    {"kind": "script", "name": "value", "script": "1"},
                    {"kind": "constant", "name": "value", "value": "x"},
                ],
            }
        ],
    ],
)
def test_duplicate_field_names_fail_closed(fields: list[dict]) -> None:
    result = normalize_authoring_spec(
        {
            "version": "1",
            "products": [{"kind": "generated", "name": "rows", "count": 1, "fields": fields}],
        }
    )
    assert result.spec is None
    assert any("names must be unique" in error for error in result.errors)


def test_duplicate_targets_fail_closed() -> None:
    result = normalize_authoring_spec(
        {
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
    )
    assert result.spec is None
    assert any("targets must be unique" in error for error in result.errors)


def test_source_suffix_and_exporter_facts_have_one_authoring_projection() -> None:
    generate_formats = supported_source_file_formats(EL_GENERATE)
    assert generate_formats[0] is SourceFileFormat.DBUNIT_XML
    assert source_file_format("dataset.dbunit.xml") is SourceFileFormat.DBUNIT_XML
    assert source_file_format("rows.fcw") is SourceFileFormat.FIXED_WIDTH
    assert "_FILE_SOURCE_SUFFIXES" not in vars(normalization_module)
    assert "_SOURCE_FILE_SUFFIXES" not in vars(cross_statement_module)

    schema_formats = set(authoring_spec_json_schema()["$defs"]["FileExportTarget"]["properties"]["format"]["enum"])
    assert schema_formats == buffered_exporter_names()
    assert set(capabilities_manifest()["targets"]["file_exporters"]) == buffered_exporter_names()


def test_intent_and_compile_plan_share_registered_exporter_validation() -> None:
    for exporter in buffered_exporter_names():
        assert FileExportTarget(format=exporter).format == exporter
        assert FileTargetBindingPlan(format=exporter).format == exporter

    for contract in (FileExportTarget, FileTargetBindingPlan):
        with pytest.raises(ValidationError, match="unsupported file exporter"):
            contract(format="BOGUS")


def test_intent_and_compile_plan_share_runtime_source_classification() -> None:
    for file_format in supported_source_file_formats(EL_GENERATE):
        path = f"rows{file_format.value}"
        assert FileSource(path=path).path == path
        assert FileSourceBindingPlan(path=path).path == path

    for contract in (FileSource, FileSourceBindingPlan):
        with pytest.raises(ValidationError, match="runtime-supported source-file suffix"):
            contract(path="rows.parquet")

    assert MemstoreSource(id="rows").id == "rows"
    assert MemstoreSourceBindingPlan(id="rows").id == "rows"
    for contract in (MemstoreSource, MemstoreSourceBindingPlan):
        with pytest.raises(ValidationError, match="dispatched as a file source"):
            contract(id="rows.csv")


@pytest.mark.parametrize("path", ["rows.csv", "rows.json", "rows.xlsx", "rows.xml", "rows.dbunit.xml", "rows.fcw"])
def test_canonical_file_source_accepts_every_runtime_suffix(path: str) -> None:
    spec = AuthoringSpecV1.model_validate(
        {
            "version": "1",
            "products": [
                {
                    "kind": "source",
                    "name": "rows",
                    "source": {"kind": "file", "path": path},
                    "fields": [{"kind": "script", "name": "id", "script": "id"}],
                }
            ],
        }
    )
    assert spec.products[0].kind == "source"


@pytest.mark.parametrize("path", ["rows.dbunit.xml", "rows.fcw"])
def test_legacy_file_source_uses_the_central_runtime_suffix_fact(path: str) -> None:
    result = normalize_authoring_spec(
        {
            "generates": [
                {
                    "name": "rows",
                    "source": path,
                    "fields": [{"kind": "script", "name": "id", "script": "id"}],
                }
            ]
        }
    )
    assert result.spec is not None
    assert result.spec.products[0].source.kind == "file"


@pytest.mark.parametrize(
    "source",
    [
        {"kind": "file", "path": "rows.parquet"},
        {"kind": "memstore", "id": "rows.csv"},
    ],
)
def test_canonical_source_kind_cannot_disagree_with_runtime_dispatch(source: dict) -> None:
    with pytest.raises(ValidationError):
        AuthoringSpecV1.model_validate(
            {
                "version": "1",
                "products": [
                    {
                        "kind": "source",
                        "name": "rows",
                        "source": source,
                        "fields": [{"kind": "script", "name": "id", "script": "id"}],
                    }
                ],
            }
        )


def test_legacy_unknown_source_and_target_tokens_are_explicit_memstores() -> None:
    result = normalize_authoring_spec(
        {
            "generates": [
                {
                    "name": "rows",
                    "source": "upstream_rows",
                    "target": "downstream_rows",
                    "fields": [{"kind": "script", "name": "id", "script": "id"}],
                }
            ]
        }
    )
    assert result.spec is not None
    product = result.spec.products[0]
    assert product.source.kind == "memstore"
    assert product.targets[0].kind == "memstore"


@pytest.mark.parametrize("target", ["database.insert", "mongo.upsert", "mongo.delete"])
def test_legacy_database_and_mongo_target_operations_fail_closed(target: str) -> None:
    result = normalize_authoring_spec(
        {
            "generates": [
                {
                    "name": "rows",
                    "count": 1,
                    "target": target,
                    "fields": [{"kind": "increment", "name": "id"}],
                }
            ]
        }
    )
    assert result.spec is None
    assert any("unsupported by authoring V1" in error for error in result.errors)


def test_compiler_has_no_transport_execution_or_file_io_dependencies() -> None:
    tree = ast.parse(inspect.getsource(compiler_module))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
    rendered = "\n".join(sorted(imported))

    for forbidden in ("cli", "mcp", "service", "linter", "dryrun", "pathlib"):
        assert forbidden not in rendered
    assert not any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open"
        for node in ast.walk(tree)
    )


def test_runtime_registry_relationships_are_a_live_compiler_gate(monkeypatch) -> None:
    spec = AuthoringSpecV1.model_validate(
        {
            "version": "1",
            "products": [
                {
                    "kind": "generated",
                    "name": "rows",
                    "count": 1,
                    "fields": [{"kind": "increment", "name": "id"}],
                }
            ],
        }
    )
    live = build_schema_index()
    setup = live.get("setup")
    assert setup is not None
    elements = dict(live.elements)
    elements["setup"] = dataclasses.replace(setup, allowed_children=set())
    monkeypatch.setattr(compiler_module, "build_schema_index", lambda: SchemaIndex(elements))

    with pytest.raises(CompileError, match="runtime registry does not allow <generate>"):
        compile_authoring_spec(spec)


def test_runtime_registry_attributes_are_a_live_compiler_gate(monkeypatch) -> None:
    spec = AuthoringSpecV1.model_validate(
        {
            "version": "1",
            "products": [
                {
                    "kind": "generated",
                    "name": "rows",
                    "count": 1,
                    "fields": [{"kind": "increment", "name": "id"}],
                }
            ],
        }
    )
    live = build_schema_index()
    generate = live.get("generate")
    assert generate is not None
    elements = dict(live.elements)
    elements["generate"] = dataclasses.replace(
        generate,
        attributes={name: value for name, value in generate.attributes.items() if name != "count"},
    )
    monkeypatch.setattr(compiler_module, "build_schema_index", lambda: SchemaIndex(elements))

    with pytest.raises(CompileError, match="attribute.*count"):
        compile_authoring_spec(spec)


def test_model_package_never_imports_authoring() -> None:
    model_dir = Path(__file__).parents[3] / "datamimic_ce" / "model"
    offenders: list[str] = []
    for path in model_dir.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            module = node.module if isinstance(node, ast.ImportFrom) else None
            names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else []
            if (module and "datamimic_ce.authoring" in module) or any(
                "datamimic_ce.authoring" in name for name in names
            ):
                offenders.append(path.name)
    assert offenders == []
