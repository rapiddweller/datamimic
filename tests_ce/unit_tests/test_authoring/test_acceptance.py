# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Gate-D acceptance contracts over one complete bounded capture."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from pydantic import ValidationError

import datamimic_ce.authoring.acceptance as acceptance_module
import datamimic_ce.authoring.service as service_module
from datamimic_ce.authoring.acceptance import evaluate_acceptance
from datamimic_ce.authoring.compiler import compile_authoring_spec
from datamimic_ce.authoring.contracts import (
    MAX_DRY_RUN_COUNT,
    AcceptanceSource,
    AcceptanceStatus,
    AuthoringStage,
    CaptureCompletenessStatus,
    CaptureStatus,
    MemstoreCompletenessAcceptanceResult,
    PerParentCountAcceptanceResult,
    ProductCaptureEvidence,
    RetryWithParameterRemediation,
    ScaffoldParameter,
    ScaffoldRequest,
    UniqueAcceptanceResult,
)
from datamimic_ce.authoring.dryrun import CapturedProduct, CapturedProducts
from datamimic_ce.authoring.spec import AuthoringSpecV1, RowConditionExpectation


def _complete_product(name: str, rows: tuple[object, ...]) -> CapturedProduct:
    observed = len(rows)
    return CapturedProduct(
        name,
        rows,
        capture=ProductCaptureEvidence(
            status=CaptureStatus.COMPLETE,
            requested=observed,
            observed=observed,
            limit=max(1, observed),
            reason="test fixture proves the complete requested capture",
        ),
    )


def _spec(
    *,
    unsafe_condition: bool = False,
    condition: str | None = None,
) -> AuthoringSpecV1:
    condition = condition or (
        "__import__('os').getcwd()"
        if unsafe_condition
        else "age >= 18 and tier in ['A', 'B']"
    )
    return AuthoringSpecV1.model_validate(
        {
            "version": "1",
            "seed": 7,
            "products": [
                {
                    "kind": "generated",
                    "name": "customers",
                    "count": 8,
                    "targets": [{"kind": "memstore", "id": "customer_mem"}],
                    "fields": [
                        {
                            "kind": "increment",
                            "name": "customer_id",
                            "roles": [{"kind": "identifier"}],
                        },
                        {"kind": "values", "name": "tier", "values": ["A", "B"]},
                        {"kind": "int_range", "name": "age", "minimum": 18, "maximum": 90},
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
                                    "name": "order_id",
                                    "script": "parent.customer_id * 10 + order_no",
                                    "roles": [{"kind": "identifier"}],
                                },
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
            "expectations": [
                {"kind": "exact_count", "product": "orders", "count": 16},
                {
                    "kind": "per_parent_count",
                    "parent_product": "customers",
                    "child_product": "orders",
                    "count": 2,
                },
                {
                    "kind": "unique",
                    "product": "orders",
                    "field": "order_no",
                    "scope": "per_parent",
                },
                {"kind": "unique", "product": "orders", "field": "order_id"},
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
                    "condition": condition,
                },
            ],
        }
    )


def _memstore_service_spec(*, count: int, consumer_fk: bool) -> dict[str, object]:
    roles = (
        [
            {
                "kind": "foreign_key",
                "parent_product": "customers",
                "parent_field": "customer_id",
            }
        ]
        if consumer_fk
        else []
    )
    return {
        "version": "1",
        "seed": 7,
        "products": [
            {
                "kind": "generated",
                "name": "customers",
                "count": count,
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
                    "product": "customers",
                },
                "fields": [
                    {
                        "kind": "script",
                        "name": "customer_id",
                        "script": "customer_id",
                        "roles": roles,
                    }
                ],
            },
        ],
    }


def _capture(*, malformed_distribution: bool = False) -> CapturedProducts:
    customers = tuple(
        {"customer_id": customer_id, "tier": "A" if customer_id % 2 else "B", "age": 20 + customer_id}
        for customer_id in range(1, 9)
    )
    orders = [
        {
            "order_no": order_no,
            "order_id": customer_id * 10 + order_no,
            "customer_id": customer_id,
        }
        for customer_id in range(1, 9)
        for order_no in (1, 2)
    ]
    if malformed_distribution:
        # Total remains 16, but customer 1 gets 3 children and customer 2 gets 1.
        orders[2]["customer_id"] = 1
    copies = tuple({"customer_id": customer_id} for customer_id in range(1, 9))
    return CapturedProducts(
        (
            _complete_product("customers", customers),
            _complete_product("orders", tuple(orders)),
            _complete_product("customer_copy", copies),
        ),
        max_count=10,
    )


def test_acceptance_verifies_counts_local_sequence_global_id_fk_and_memstore() -> None:
    spec = _spec()
    report = evaluate_acceptance(compile_authoring_spec(spec).plan, spec, _capture())

    assert report.verified
    assert report.failed == report.unevaluable == 0
    per_parent = next(
        item
        for item in report.results
        if isinstance(item, PerParentCountAcceptanceResult)
    )
    unique = {
        item.scope: item
        for item in report.results
        if isinstance(item, UniqueAcceptanceResult)
    }
    assert per_parent.observed_counts is not None
    assert set(per_parent.observed_counts.values()) == {2}
    assert unique["per_parent"].distinct_count == 16
    assert unique["global"].distinct_count in {8, 16}
    memstore = next(
        item
        for item in report.results
        if isinstance(item, MemstoreCompletenessAcceptanceResult)
    )
    assert (memstore.producer_count, memstore.consumer_count) == (8, 8)


def test_per_parent_count_never_passes_from_matching_global_totals() -> None:
    spec = _spec()
    report = evaluate_acceptance(
        compile_authoring_spec(spec).plan,
        spec,
        _capture(malformed_distribution=True),
    )

    result = next(item for item in report.results if item.kind == "per_parent_count")
    assert result.status is AcceptanceStatus.FAIL
    assert result.observed_counts is not None
    assert sorted(result.observed_counts.values()) == [1, 2, 2, 2, 2, 2, 2, 3]
    assert not report.verified


def test_each_supported_expectation_has_structured_failure_evidence() -> None:
    spec = _spec()
    plan = compile_authoring_spec(spec).plan
    capture = _capture()
    products = {product.name: product for product in capture.products}
    customers = [dict(row) for row in products["customers"].rows]
    orders = [dict(row) for row in products["orders"].rows]
    customers[0]["tier"] = "C"
    customers[1]["age"] = 17
    orders[1]["order_id"] = orders[0]["order_id"]
    orders[2]["customer_id"] = 1
    failing_capture = CapturedProducts(
        (
            _complete_product("customers", tuple(customers)),
            _complete_product("orders", tuple(orders)),
            _complete_product("customer_copy", products["customer_copy"].rows[:-1]),
        ),
        max_count=10,
    )

    report = evaluate_acceptance(plan, spec, failing_capture)

    def has_status(kind: str, status: AcceptanceStatus) -> bool:
        return any(item.kind == kind and item.status is status for item in report.results)

    assert has_status("exact_count", AcceptanceStatus.FAIL)
    assert has_status("per_parent_count", AcceptanceStatus.FAIL)
    assert has_status("unique", AcceptanceStatus.FAIL)
    assert has_status("allowed_values", AcceptanceStatus.FAIL)
    assert has_status("range", AcceptanceStatus.FAIL)
    assert has_status("row_condition", AcceptanceStatus.FAIL)
    assert has_status("memstore_completeness", AcceptanceStatus.FAIL)
    assert not report.verified

    orphan_orders = [dict(row) for row in orders]
    orphan_orders[2]["customer_id"] = 999
    fk_report = evaluate_acceptance(
        plan,
        spec,
        CapturedProducts(
            (
                _complete_product("customers", tuple(customers)),
                _complete_product("orders", tuple(orphan_orders)),
                _complete_product("customer_copy", products["customer_copy"].rows),
            ),
            max_count=10,
        ),
    )
    assert any(
        item.kind == "foreign_key"
        and item.status is AcceptanceStatus.FAIL
        and item.missing_values == ["999"]
        for item in fk_report.results
    )


def test_missing_capture_and_unsafe_row_condition_are_unevaluable() -> None:
    spec = _spec(unsafe_condition=True)
    plan = compile_authoring_spec(spec).plan
    capture = CapturedProducts(
        tuple(product for product in _capture().products if product.name != "orders"),
        max_count=10,
    )

    report = evaluate_acceptance(plan, spec, capture)

    assert report.unevaluable > 0
    assert any(
        item.kind == "row_condition" and item.status is AcceptanceStatus.UNEVALUABLE
        for item in report.results
    )
    assert not report.verified


def test_per_parent_without_explicit_compile_plan_join_is_unevaluable() -> None:
    spec = AuthoringSpecV1.model_validate(
        {
            "version": "1",
            "products": [
                {
                    "kind": "generated",
                    "name": "parents",
                    "count": 2,
                    "fields": [{"kind": "increment", "name": "parent_id"}],
                    "children": [
                        {
                            "kind": "generated",
                            "name": "children",
                            "count": 2,
                            "fields": [{"kind": "increment", "name": "child_no"}],
                        }
                    ],
                }
            ],
            "expectations": [
                {
                    "kind": "per_parent_count",
                    "parent_product": "parents",
                    "child_product": "children",
                    "count": 2,
                }
            ],
        }
    )
    captured = CapturedProducts(
        (
            _complete_product("parents", ({"parent_id": 1}, {"parent_id": 2})),
            _complete_product(
                "children",
                ({"child_no": 1}, {"child_no": 2}, {"child_no": 1}, {"child_no": 2}),
            ),
        ),
        max_count=10,
    )

    report = evaluate_acceptance(compile_authoring_spec(spec).plan, spec, captured)

    per_parent = next(item for item in report.results if item.kind == "per_parent_count")
    assert per_parent.status is AcceptanceStatus.UNEVALUABLE
    assert "explicit FK role" in per_parent.message
    assert not report.verified


def test_orphan_join_value_cannot_make_per_parent_count_pass() -> None:
    spec = _spec()
    capture = _capture()
    products = {product.name: product for product in capture.products}
    orphan_rows = (
        {"order_no": 1, "order_id": 991, "customer_id": 999},
        {"order_no": 2, "order_id": 992, "customer_id": 999},
    )
    captured = CapturedProducts(
        tuple(
            _complete_product(product.name, product.rows + orphan_rows)
            if product.name == "orders"
            else product
            for product in products.values()
        ),
        max_count=10,
    )

    report = evaluate_acceptance(compile_authoring_spec(spec).plan, spec, captured)

    per_parent = next(item for item in report.results if item.kind == "per_parent_count")
    assert per_parent.status is AcceptanceStatus.UNEVALUABLE
    assert "has no captured" in per_parent.message


def test_row_condition_uses_python_short_circuit_without_division_error() -> None:
    spec = _spec(condition="age != 0 and 10 / age > 1")
    capture = _capture()
    products = {product.name: product for product in capture.products}
    customers = [dict(row) for row in products["customers"].rows]
    customers[0]["age"] = 0
    captured = CapturedProducts(
        tuple(
            _complete_product(product.name, tuple(customers))
            if product.name == "customers"
            else product
            for product in products.values()
        ),
        max_count=10,
    )

    report = evaluate_acceptance(compile_authoring_spec(spec).plan, spec, captured)

    condition = next(item for item in report.results if item.kind == "row_condition")
    assert condition.status is AcceptanceStatus.FAIL
    assert condition.evaluation_errors == []


@pytest.mark.parametrize(
    "hostile_condition",
    [
        "['x'] * 1000000000 == []",
        f"{'x' * 1025!r} == tier",
        f"tier in {[str(index) for index in range(65)]!r}",
        "not " * 14 + "True",
        "2 ** 1000000 == 1",
    ],
)
def test_row_condition_rejects_resource_hostile_expressions(
    hostile_condition: str,
) -> None:
    spec = _spec(condition=hostile_condition)

    report = evaluate_acceptance(compile_authoring_spec(spec).plan, spec, _capture())

    condition = next(item for item in report.results if item.kind == "row_condition")
    assert condition.status is AcceptanceStatus.UNEVALUABLE
    assert condition.evaluation_errors
    assert not report.verified


def test_nested_runtime_cap_blocks_every_affected_whole_product_expectation() -> None:
    spec = {
        "version": "1",
        "seed": 1,
        "products": [
            {
                "kind": "generated",
                "name": "parents",
                "count": 1,
                "fields": [
                    {
                        "kind": "increment",
                        "name": "parent_id",
                        "roles": [{"kind": "identifier"}],
                    }
                ],
                "children": [
                    {
                        "kind": "generated",
                        "name": "children",
                        "count": 3,
                        "fields": [
                            {"kind": "increment", "name": "child_no"},
                            {
                                "kind": "script",
                                "name": "child_id",
                                "script": "parent.parent_id * 10 + child_no",
                                "roles": [{"kind": "identifier"}],
                            },
                            {
                                "kind": "script",
                                "name": "parent_id",
                                "script": "parent.parent_id",
                                "roles": [
                                    {
                                        "kind": "foreign_key",
                                        "parent_product": "parents",
                                        "parent_field": "parent_id",
                                    }
                                ],
                            },
                        ],
                    }
                ],
            }
        ],
        "expectations": [
            {
                "kind": "per_parent_count",
                "parent_product": "parents",
                "child_product": "children",
                "count": 3,
            },
            {
                "kind": "unique",
                "product": "children",
                "field": "child_no",
                "scope": "per_parent",
            },
            {
                "kind": "foreign_key",
                "child_product": "children",
                "child_field": "parent_id",
                "parent_product": "parents",
                "parent_field": "parent_id",
            },
        ],
    }

    result = service_module.scaffold(
        ScaffoldRequest(spec=spec, max_count=1, sample_rows=1)
    )

    affected = [
        expectation
        for expectation in result.acceptance.results
        if (
            expectation.kind in {"per_parent_count", "foreign_key"}
            or (
                expectation.kind in {"exact_count", "unique"}
                and expectation.product == "children"
            )
        )
    ]
    assert affected
    assert all(
        expectation.status is AcceptanceStatus.UNEVALUABLE
        for expectation in affected
    )
    child_proofs = [
        proof
        for expectation in affected
        if expectation.capture_completeness is not None
        for proof in expectation.capture_completeness.products
        if proof.product == "children"
    ]
    assert child_proofs
    assert all(
        proof.status is CaptureCompletenessStatus.PARTIAL
        and proof.runtime_status is CaptureStatus.CAPPED
        and proof.requested == 3
        and proof.observed == proof.limit == 1
        for proof in child_proofs
    )
    assert not result.verified


@pytest.mark.parametrize(
    ("max_count", "runtime_status", "completeness_status", "acceptance_status"),
    [
        (
            1,
            CaptureStatus.CAPPED,
            CaptureCompletenessStatus.PARTIAL,
            AcceptanceStatus.UNEVALUABLE,
        ),
        (
            4,
            CaptureStatus.EXHAUSTED,
            CaptureCompletenessStatus.COMPLETE,
            AcceptanceStatus.PASS,
        ),
        (
            10,
            CaptureStatus.EXHAUSTED,
            CaptureCompletenessStatus.COMPLETE,
            AcceptanceStatus.PASS,
        ),
    ],
)
def test_file_source_acceptance_uses_runtime_exhaustion_evidence(
    tmp_path: Path,
    max_count: int,
    runtime_status: CaptureStatus,
    completeness_status: CaptureCompletenessStatus,
    acceptance_status: AcceptanceStatus,
) -> None:
    source = tmp_path / "rows.csv"
    source.write_text("status\nA\nB\nA\n", encoding="utf-8")
    spec = {
        "version": "1",
        "seed": 1,
        "products": [
            {
                "kind": "source",
                "name": "rows",
                "source": {
                    "kind": "file",
                    "path": str(source),
                    "separator": ",",
                },
                "fields": [
                    {"kind": "script", "name": "status", "script": "status"}
                ],
            }
        ],
        "expectations": [
            {
                "kind": "allowed_values",
                "product": "rows",
                "field": "status",
                "values": ["A", "B"],
            }
        ],
    }

    result = service_module.scaffold(
        ScaffoldRequest(spec=spec, max_count=max_count, sample_rows=1)
    )

    allowed = next(
        item for item in result.acceptance.results if item.kind == "allowed_values"
    )
    assert result.ok
    assert allowed.capture_completeness is not None
    proof = allowed.capture_completeness.products[0]
    assert allowed.status is acceptance_status
    assert allowed.capture_completeness.status is completeness_status
    assert proof.runtime_status is runtime_status
    assert proof.requested == 3
    assert proof.observed == min(max_count, 3)
    assert proof.limit == max_count
    assert allowed.observed_count == min(max_count, 3)
    assert result.verified is (acceptance_status is AcceptanceStatus.PASS)


def test_missing_runtime_capture_evidence_fails_closed_without_plan_fallback() -> None:
    spec = _spec()
    capture = _capture()
    products = tuple(
        CapturedProduct(product.name, product.rows)
        if product.name == "customers"
        else product
        for product in capture.products
    )

    report = evaluate_acceptance(
        compile_authoring_spec(spec).plan,
        spec,
        CapturedProducts(products, max_count=10),
    )

    allowed = next(item for item in report.results if item.kind == "allowed_values")
    assert allowed.status is AcceptanceStatus.UNEVALUABLE
    assert allowed.capture_completeness is not None
    assert allowed.capture_completeness.status is CaptureCompletenessStatus.UNKNOWN
    proof = allowed.capture_completeness.products[0]
    assert proof.runtime_status is None
    assert proof.requested is proof.observed is proof.limit is None
    aggregates = [
        result
        for result in report.results
        if result.kind in {"foreign_key", "memstore_completeness"}
    ]
    assert aggregates
    assert all(
        result.status is AcceptanceStatus.UNEVALUABLE
        and result.capture_completeness is not None
        and result.capture_completeness.status is CaptureCompletenessStatus.UNKNOWN
        for result in aggregates
    )
    assert {
        proof.product
        for result in aggregates
        if result.capture_completeness is not None
        for proof in result.capture_completeness.products
    } == {"customers", "orders", "customer_copy"}
    assert not report.verified


def test_non_finite_range_value_is_unevaluable_not_an_exception() -> None:
    spec = _spec()
    capture = _capture()
    products = {product.name: product for product in capture.products}
    customers = [dict(row) for row in products["customers"].rows]
    customers[0]["age"] = float("nan")
    captured = CapturedProducts(
        tuple(
            _complete_product(product.name, tuple(customers))
            if product.name == "customers"
            else product
            for product in products.values()
        ),
        max_count=10,
    )

    report = evaluate_acceptance(compile_authoring_spec(spec).plan, spec, captured)

    age_range = next(
        item
        for item in report.results
        if item.kind == "range" and item.product == "customers" and item.field == "age"
    )
    assert age_range.status is AcceptanceStatus.UNEVALUABLE
    assert not report.verified


def test_memstore_same_count_different_identities_fails_with_key_evidence() -> None:
    spec = _spec()
    capture = _capture()
    products = {product.name: product for product in capture.products}
    different_copy = tuple({"customer_id": value} for value in range(101, 109))
    captured = CapturedProducts(
        tuple(
            _complete_product(product.name, different_copy)
            if product.name == "customer_copy"
            else product
            for product in products.values()
        ),
        max_count=10,
    )

    report = evaluate_acceptance(compile_authoring_spec(spec).plan, spec, captured)

    completeness = next(
        item for item in report.results if item.kind == "memstore_completeness"
    )
    assert completeness.status is AcceptanceStatus.FAIL
    assert completeness.producer_key_field == "customer_id"
    assert completeness.consumer_key_field == "customer_id"
    assert completeness.missing_keys == [str(value) for value in range(1, 9)]
    assert completeness.unexpected_keys == [str(value) for value in range(101, 109)]
    assert not report.verified


def test_memstore_without_typed_identity_join_is_unevaluable() -> None:
    payload = _spec().model_dump(mode="json")
    copy_product = payload["products"][1]
    copy_product["fields"][0]["roles"] = []
    spec = AuthoringSpecV1.model_validate(payload)

    report = evaluate_acceptance(compile_authoring_spec(spec).plan, spec, _capture())

    completeness = next(
        item for item in report.results if item.kind == "memstore_completeness"
    )
    assert completeness.status is AcceptanceStatus.UNEVALUABLE
    assert "typed producer identifier" in completeness.message
    assert completeness.required_consumer_foreign_key is not None
    assert completeness.required_consumer_foreign_key.parent_product == "customers"
    assert completeness.required_consumer_foreign_key.parent_field == "customer_id"
    assert completeness.required_consumer_foreign_key.required_count == 1
    assert completeness.required_consumer_foreign_key.observed_count == 0
    assert not report.verified


def test_count_cap_emits_one_typed_memstore_retry_remediation() -> None:
    result = service_module.scaffold(
        ScaffoldRequest(
            spec=_memstore_service_spec(count=15, consumer_fk=True),
            max_count=10,
            sample_rows=1,
        )
    )

    assert not result.verified
    assert len(result.remediations) == 1
    remediation = result.remediations[0]
    assert remediation.parameter is ScaffoldParameter.MAX_COUNT
    assert remediation.minimum_value == 15
    assert remediation.affected_products == ("customers", "customer_readback")


def test_complete_memstore_capture_reports_missing_typed_consumer_role() -> None:
    result = service_module.scaffold(
        ScaffoldRequest(
            spec=_memstore_service_spec(count=15, consumer_fk=False),
            max_count=15,
            sample_rows=1,
        )
    )

    assert result.acceptance is not None
    completeness = next(
        item
        for item in result.acceptance.results
        if item.kind == "memstore_completeness"
    )
    assert completeness.status is AcceptanceStatus.UNEVALUABLE
    assert completeness.required_consumer_foreign_key is not None
    assert completeness.required_consumer_foreign_key.parent_product == "customers"
    assert completeness.required_consumer_foreign_key.parent_field == "customer_id"
    assert completeness.required_consumer_foreign_key.observed_count == 0
    assert result.remediations == []
    assert not result.verified


def test_complete_memstore_capture_with_one_typed_consumer_role_verifies() -> None:
    result = service_module.scaffold(
        ScaffoldRequest(
            spec=_memstore_service_spec(count=15, consumer_fk=True),
            max_count=15,
            sample_rows=1,
        )
    )

    assert result.acceptance is not None
    completeness = next(
        item
        for item in result.acceptance.results
        if item.kind == "memstore_completeness"
    )
    assert completeness.status is AcceptanceStatus.PASS
    assert completeness.required_consumer_foreign_key is not None
    assert completeness.required_consumer_foreign_key.observed_count == 1
    assert result.remediations == []
    assert result.verified


def test_memstore_ambiguous_identity_join_is_unevaluable() -> None:
    payload = _spec().model_dump(mode="json")
    copy_product = payload["products"][1]
    copy_product["fields"].append(
        {
            "kind": "script",
            "name": "customer_id_again",
            "script": "customer_id",
            "roles": [
                {
                    "kind": "foreign_key",
                    "parent_product": "customers",
                    "parent_field": "customer_id",
                }
            ],
        }
    )
    spec = AuthoringSpecV1.model_validate(payload)
    capture = _capture()
    captured = CapturedProducts(
        tuple(
            _complete_product(
                product.name,
                tuple(
                    {**row, "customer_id_again": row["customer_id"]}
                    for row in product.rows
                ),
            )
            if product.name == "customer_copy"
            else product
            for product in capture.products
        ),
        max_count=10,
    )

    report = evaluate_acceptance(compile_authoring_spec(spec).plan, spec, captured)

    completeness = next(
        item for item in report.results if item.kind == "memstore_completeness"
    )
    assert completeness.status is AcceptanceStatus.UNEVALUABLE
    assert "found 2" in completeness.message
    assert completeness.required_consumer_foreign_key is not None
    assert completeness.required_consumer_foreign_key.observed_count == 2
    assert not report.verified


def test_sample_projection_does_not_change_acceptance_and_uses_gateway_once(monkeypatch) -> None:
    spec = _spec()
    gateway_calls = 0
    original_gateway = service_module.dry_run_source_captured

    def counted(*args, **kwargs):
        nonlocal gateway_calls
        gateway_calls += 1
        return original_gateway(*args, **kwargs)

    monkeypatch.setattr(service_module, "dry_run_source_captured", counted)
    result = service_module.scaffold(
        ScaffoldRequest(spec=spec.model_dump(mode="json"), sample_rows=1, max_count=10)
    )

    assert gateway_calls == 1
    assert result.stage is AuthoringStage.ACCEPTANCE
    assert result.ok
    assert result.verified
    assert all(len(product.sample) <= 1 for product in result.products)
    assert {product.name: product.count for product in result.products} == {
        "customer_copy": 8,
        "customers": 8,
        "orders": 16,
    }
    exact_orders = next(
        item
        for item in result.acceptance.results
        if item.kind == "exact_count" and item.product == "orders"
    )
    assert exact_orders.observed_count == 16
    memstore = next(
        item
        for item in result.acceptance.results
        if item.kind == "memstore_completeness"
    )
    assert memstore.status is AcceptanceStatus.PASS
    assert memstore.required_consumer_foreign_key is not None
    assert memstore.required_consumer_foreign_key.observed_count == 1
    assert memstore.producer_key_field == "customer_id"
    assert memstore.consumer_key_field == "customer_id"
    assert (memstore.producer_count, memstore.consumer_count) == (8, 8)
    assert memstore.missing_keys == memstore.unexpected_keys == []
    assert memstore.duplicate_producer_keys == memstore.duplicate_consumer_keys == []
    assert result.remediations == []


def test_count_above_bound_is_unevaluable_not_a_false_verification() -> None:
    spec = AuthoringSpecV1.model_validate(
        {
            "version": "1",
            "seed": 1,
            "products": [
                {
                    "kind": "generated",
                    "name": "rows",
                    "count": 15,
                    "fields": [{"kind": "increment", "name": "id"}],
                }
            ],
        }
    )

    result = service_module.scaffold(
        ScaffoldRequest(spec=spec.model_dump(mode="json"), max_count=10, sample_rows=1)
    )

    exact = next(item for item in result.acceptance.results if item.kind == "exact_count")
    assert exact.status is AcceptanceStatus.UNEVALUABLE
    assert exact.observed_count == 10
    assert result.stage is AuthoringStage.ACCEPTANCE
    assert not result.verified
    assert len(result.remediations) == 1
    remediation = result.remediations[0]
    assert remediation.parameter is ScaffoldParameter.MAX_COUNT
    assert remediation.minimum_value == 15
    assert remediation.affected_products == ("rows",)


@pytest.mark.parametrize(
    ("requested_count", "expected_minimum"),
    [
        (MAX_DRY_RUN_COUNT, MAX_DRY_RUN_COUNT),
        (MAX_DRY_RUN_COUNT + 1, None),
    ],
)
def test_count_retry_is_emitted_only_when_canonical_limit_can_execute_it(
    requested_count: int,
    expected_minimum: int | None,
) -> None:
    spec = AuthoringSpecV1.model_validate(
        {
            "version": "1",
            "seed": 1,
            "products": [
                {
                    "kind": "generated",
                    "name": "rows",
                    "count": requested_count,
                    "fields": [{"kind": "increment", "name": "id"}],
                }
            ],
        }
    )

    result = service_module.scaffold(
        ScaffoldRequest(spec=spec.model_dump(mode="json"), max_count=10, sample_rows=1)
    )

    exact = next(item for item in result.acceptance.results if item.kind == "exact_count")
    assert exact.status is AcceptanceStatus.UNEVALUABLE
    if expected_minimum is None:
        assert result.remediations == []
    else:
        assert len(result.remediations) == 1
        assert result.remediations[0].minimum_value == expected_minimum


def test_retry_contract_rejects_minimum_above_canonical_limit() -> None:
    with pytest.raises(ValidationError):
        RetryWithParameterRemediation(
            minimum_value=MAX_DRY_RUN_COUNT + 1,
            affected_products=("rows",),
        )


def test_time_series_count_above_bound_is_unevaluable() -> None:
    spec = AuthoringSpecV1.model_validate(
        {
            "version": "1",
            "seed": 1,
            "products": [
                {
                    "kind": "time_series",
                    "name": "readings",
                    "series_count": 20,
                    "window": {
                        "start": "2025-01-01T00:00:00",
                        "end": "2025-01-01T02:00:00",
                        "interval": "PT1H",
                    },
                    "fields": [{"kind": "script", "name": "at", "script": "ts.now"}],
                }
            ],
        }
    )

    result = service_module.scaffold(
        ScaffoldRequest(spec=spec.model_dump(mode="json"), max_count=10, sample_rows=1)
    )

    exact = next(item for item in result.acceptance.results if item.kind == "exact_count")
    assert exact.status is AcceptanceStatus.UNEVALUABLE
    assert result.stage is AuthoringStage.ACCEPTANCE
    assert not result.verified


def test_acceptance_has_no_xml_or_transport_dependency() -> None:
    source = Path(acceptance_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert not any(module.endswith("xml") or ".xml" in module for module in imported_modules)
    assert "datamimic_ce.cli" not in imported_modules
    assert not any(module.startswith("datamimic_ce.mcp") for module in imported_modules)
    assert "eval(" not in source


def test_acceptance_merge_deduplicates_identical_but_retains_conflicts() -> None:
    spec = _spec()
    plan = compile_authoring_spec(spec).plan

    entries = acceptance_module.merge_expectations(plan, spec)
    order_exact = [
        entry
        for entry in entries
        if type(entry.expectation).__name__ == "_Exact"
        and entry.expectation.product == "orders"
    ]

    assert len(order_exact) == 1
    assert order_exact[0].source is AcceptanceSource.DERIVED_AND_EXPLICIT


def test_duplicate_explicit_expectations_are_rejected_at_intent_boundary() -> None:
    payload = _spec().model_dump(mode="json")
    duplicate = {
        "kind": "row_condition",
        "product": "customers",
        "condition": "age >= 18",
    }
    payload["expectations"] = [duplicate, duplicate]

    with pytest.raises(ValidationError, match="explicit expectations must be unique"):
        AuthoringSpecV1.model_validate(payload)


def test_merge_cannot_relabel_explicit_only_duplicate_as_derived() -> None:
    base = _spec()
    explicit = RowConditionExpectation(product="customers", condition="age >= 18")
    bypassed_boundary = base.model_copy(update={"expectations": (explicit, explicit)})

    entries = acceptance_module.merge_expectations(
        compile_authoring_spec(base).plan,
        bypassed_boundary,
    )
    conditions = [
        entry
        for entry in entries
        if type(entry.expectation).__name__ == "_RowCondition"
        and entry.expectation.condition == "age >= 18"
    ]

    assert len(conditions) == 1
    assert conditions[0].source is AcceptanceSource.EXPLICIT


def test_contradictory_explicit_expectations_remain_explicit_and_both_evaluate() -> None:
    payload = _spec().model_dump(mode="json")
    payload["expectations"] = [
        {"kind": "exact_count", "product": "customers", "count": 7},
        {"kind": "exact_count", "product": "customers", "count": 9},
    ]
    spec = AuthoringSpecV1.model_validate(payload)
    plan = compile_authoring_spec(spec).plan

    entries = acceptance_module.merge_expectations(plan, spec)
    explicit_counts = [
        entry
        for entry in entries
        if type(entry.expectation).__name__ == "_Exact"
        and entry.expectation.product == "customers"
        and entry.source is AcceptanceSource.EXPLICIT
    ]
    report = evaluate_acceptance(plan, spec, _capture())
    evaluated = [
        result
        for result in report.results
        if result.kind == "exact_count"
        and result.product == "customers"
        and result.source is AcceptanceSource.EXPLICIT
    ]

    assert len(explicit_counts) == 2
    assert len(evaluated) == 2
    assert all(result.status is AcceptanceStatus.FAIL for result in evaluated)
