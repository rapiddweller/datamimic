# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A malformed expectation gets the shape of its kind as remediation (#426). The projects are DSL; the
acceptance shapes are the ones blind agents wrote."""

import json
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.expectations import ExpectationIntent, ExpectationIntentKind, expectation_example
from datamimic_ce.authoring.domain.reference import AuthoringVariantReference
from datamimic_ce.authoring.domain.requests import (
    PROJECT_ACCEPTANCE_PATH,
    PROJECT_ENTRY_PATH,
    ReferenceRequest,
    ReferenceTopic,
    RejectedBuild,
)

_XML = (
    '<setup rngSeed="1"><generate name="customers" count="2"><key name="customer_id" generator="IncrementGenerator"/>'
    '<key name="score" type="int" min="1" max="9"/>'
    '<generate name="orders" count="2"><key name="customer_id" script="parent.customer_id"/></generate>'
    "</generate></setup>"
)
_PRODUCT = {"kind": "product", "product": "customers"}


def _build(root: Path, acceptance: dict[str, object]) -> RejectedBuild:
    (root / PROJECT_ENTRY_PATH).write_text(_XML, encoding="utf-8")
    (root / PROJECT_ACCEPTANCE_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / PROJECT_ACCEPTANCE_PATH).write_text(json.dumps({"version": "5.0", **acceptance}), encoding="utf-8")
    result = create_authoring_application(root, descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(result, RejectedBuild)
    return result


def _remediations(result: RejectedBuild) -> dict[tuple[str | int, ...], str]:
    return {item.path: str(item.remediation) for item in result.diagnostics}


def _shape(kind: ExpectationIntentKind) -> str:
    return json.dumps(expectation_example(kind))


def test_range_with_min_and_max_names_the_field_to_rename(tmp_path: Path) -> None:
    range_ = {"kind": "range", "subject": _PRODUCT, "field": "score", "min": 1, "max": 9}

    remediations = _remediations(_build(tmp_path, {"expectations": [range_]}))

    assert remediations[("expectations", 0, "range", "min")].startswith("Rename min to minimum.")
    assert remediations[("expectations", 0, "range", "max")].startswith("Rename max to maximum.")
    assert all(_shape(ExpectationIntentKind.RANGE) in text for text in remediations.values())


def test_range_with_inverted_bounds_shows_the_shape(tmp_path: Path) -> None:
    range_ = {"kind": "range", "subject": _PRODUCT, "field": "score", "minimum": 9, "maximum": 1}

    [text] = _remediations(_build(tmp_path, {"expectations": [range_]})).values()

    assert _shape(ExpectationIntentKind.RANGE) in text


def test_per_parent_count_with_a_product_subject_shows_the_per_parent_shape(tmp_path: Path) -> None:
    count = {"kind": "per_parent_count", "subject": {"kind": "product", "product": "orders"}, "count": 2}

    remediations = _remediations(_build(tmp_path, {"expectations": [count]}))

    shape = _shape(ExpectationIntentKind.PER_PARENT_COUNT)
    assert '"parent_product"' in shape
    assert remediations and all(shape in text for text in remediations.values())


def test_acceptance_requirement_expectation_gets_the_same_shape(tmp_path: Path) -> None:
    range_ = {"kind": "range", "subject": _PRODUCT, "field": "score", "min": 1, "maximum": 9}
    requirement = {"expectation": range_, "origin": "caller"}

    remediations = _remediations(_build(tmp_path, {"acceptance_requirements": [requirement]}))

    path = ("acceptance_requirements", 0, "expectation", "range", "min")
    assert remediations[path].startswith("Rename min to minimum.")


def test_an_error_outside_an_expectation_keeps_the_model_remediation(tmp_path: Path) -> None:
    [text] = _remediations(_build(tmp_path, {"max_count": 0})).values()

    assert text == "Repair the canonical authoring model at the reported path."


@pytest.mark.parametrize("kind", list(ExpectationIntentKind))
def test_every_kind_has_an_example_that_is_a_valid_expectation(kind: ExpectationIntentKind) -> None:
    example = TypeAdapter(ExpectationIntent).validate_python(expectation_example(kind))

    assert example.kind is kind


def test_reference_publishes_the_example_of_each_kind(tmp_path: Path) -> None:
    application = create_authoring_application(tmp_path)
    result = application.reference(ReferenceRequest(topic=ReferenceTopic.EXPECTATIONS, name="range"))

    [entry] = result.entries or ()
    assert isinstance(entry, AuthoringVariantReference)
    assert entry.usage_example == expectation_example(ExpectationIntentKind.RANGE)


@pytest.mark.parametrize(
    ("expectation", "path", "declared"),
    [
        pytest.param(
            {"kind": "unique", "subject": _PRODUCT, "field": "input"},
            ("expectations", 0, "field"),
            ("customer_id", "score"),
            id="unknown-field",
        ),
        pytest.param(
            {"kind": "unique", "subject": {"kind": "product", "product": "clients"}, "field": "customer_id"},
            ("expectations", 0, "subject", "product"),
            ("customers", "orders"),
            id="unknown-product",
        ),
        pytest.param(
            {
                "kind": "unique",
                "subject": {"kind": "per_parent", "parent_product": "customers", "child_product": "orders"},
                "field": "line_no",
                "scope": "per_parent",
            },
            ("expectations", 0, "field"),
            ("customer_id",),
            id="unknown-child-field",
        ),
    ],
)
def test_an_unknown_name_lists_the_declared_names(
    tmp_path: Path, expectation: dict[str, object], path: tuple[str | int, ...], declared: tuple[str, ...]
) -> None:
    [diagnostic] = _build(tmp_path, {"expectations": [expectation]}).diagnostics

    assert (diagnostic.path, diagnostic.allowed_values) == (path, declared)
