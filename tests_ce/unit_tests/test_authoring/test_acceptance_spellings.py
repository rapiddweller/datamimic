# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Build and the published schema accept the same acceptance spellings (campaign at 89f304b9): each document is
accepted by both or by neither, and an accepted spelling is dumped in its canonical form. The flat foreign_key
side, per_parent_count with parent and child, and unique with fields stay rejected: they need a raw-input
validator, which the ArchKeel typing budget does not allow yet."""

import pytest
from jsonschema import Draft202012Validator
from pydantic import TypeAdapter, ValidationError

from datamimic_ce.authoring.domain.expectations import ExpectationIntent
from datamimic_ce.authoring.domain.requests import BuildRequestV5

_ROWS = {"kind": "product", "product": "orders"}
_PER_PARENT = {"kind": "per_parent", "parent_product": "customers", "child_product": "orders"}
_PARENT = {"subject": {"kind": "product", "product": "customers"}, "field": "id"}


def _range(**bounds: object) -> dict[str, object]:
    return {"kind": "range", "subject": _ROWS, "field": "amount", **bounds}


def _foreign_key(child: object) -> dict[str, object]:
    return {"kind": "foreign_key", "child": child, "parent": _PARENT}


def _unique(**field: object) -> dict[str, object]:
    return {"kind": "unique", "subject": _ROWS, **field}


def _per_parent(**subject: object) -> dict[str, object]:
    return {"kind": "per_parent_count", "count": 3, **subject}


def _condition(**result_type: object) -> dict[str, object]:
    return {"kind": "row_condition", "subject": _ROWS, "condition": "amount >= 0", **result_type}


_CASES = [
    pytest.param(_range(minimum="0", maximum="9"), True, id="range-canonical"),
    pytest.param(_range(min=0, max=9), True, id="range-min-max"),
    pytest.param(_range(min=0, maximum=9), True, id="range-mixed"),
    pytest.param(_range(min=0, minimum=0, maximum=9), False, id="range-both-spellings"),
    pytest.param(_range(max=9), False, id="range-missing-lower-bound"),
    pytest.param(_foreign_key({"subject": _ROWS, "field": "customer_id"}), True, id="side-canonical"),
    pytest.param(_foreign_key({"product": "orders", "field": "customer_id"}), False, id="side-flat"),
    pytest.param(_foreign_key({"kind": "product", "product": "orders", "field": "customer_id"}), False, id="side-kind"),
    pytest.param(_foreign_key({"subject": _ROWS, "product": "orders", "field": "id"}), False, id="side-both"),
    pytest.param(_foreign_key({"kind": "declared_sink", "product": "orders", "field": "id"}), False, id="side-sink"),
    pytest.param(_foreign_key({"product": "orders"}), False, id="side-missing-field"),
    pytest.param(_foreign_key({"product": 7, "field": "id"}), False, id="side-product-type"),
    pytest.param(_unique(field="id"), True, id="unique-canonical"),
    pytest.param(_unique(fields=["id"]), False, id="unique-one-field-list"),
    pytest.param(_unique(fields=[]), False, id="unique-empty-list"),
    pytest.param(_unique(fields=["id", "code"]), False, id="unique-two-fields"),
    pytest.param(_unique(fields="id"), False, id="unique-fields-string"),
    pytest.param(_unique(field="id", fields=["id"]), False, id="unique-both"),
    pytest.param(_per_parent(subject=_PER_PARENT), True, id="per-parent-canonical"),
    pytest.param(_per_parent(parent={"product": "customers"}, child={"product": "orders"}), False, id="sides"),
    pytest.param(
        _per_parent(parent={"kind": "product", "product": "customers"}, child={"kind": "product", "product": "orders"}),
        False,
        id="sides-kind",
    ),
    pytest.param(
        _per_parent(parent={"product": "customers", "field": "id"}, child={"product": "orders"}),
        False,
        id="sides-with-a-grouping-field",
    ),
    pytest.param(_per_parent(parent={"product": "customers"}), False, id="parent-without-child"),
    pytest.param(
        _per_parent(subject=_PER_PARENT, parent={"product": "customers"}, child={"product": "orders"}),
        False,
        id="per-parent-both",
    ),
    pytest.param(_per_parent(parent="customers", child="orders"), False, id="sides-as-strings"),
    pytest.param(_condition(), True, id="result-type-omitted"),
    pytest.param(_condition(result_type="bool"), True, id="result-type-bool"),
    pytest.param(_condition(result_type="boolean"), True, id="result-type-boolean"),
    pytest.param(_condition(result_type="int"), False, id="result-type-int"),
]


def _accepted(document: dict[str, object]) -> bool:
    try:
        BuildRequestV5.model_validate(document)
    except ValidationError:
        return False
    return True


@pytest.mark.parametrize(("expectation", "accepted"), _CASES)
def test_build_and_the_published_schema_accept_the_same_spellings(expectation: dict, accepted: bool) -> None:
    document = {"version": "5.0", "expectations": [expectation]}
    validator = Draft202012Validator(BuildRequestV5.model_json_schema())
    reference = Draft202012Validator(TypeAdapter(ExpectationIntent).json_schema())

    assert (_accepted(document), validator.is_valid(document), reference.is_valid(expectation)) == (accepted,) * 3


@pytest.mark.parametrize(
    ("spelled", "canonical"),
    [
        (_range(min=0, max=9), _range(minimum=0, maximum=9)),
        (_condition(result_type="boolean"), _condition(result_type="bool")),
    ],
)
def test_an_accepted_spelling_is_dumped_and_identified_as_its_canonical_form(spelled: dict, canonical: dict) -> None:
    def dump(expectation: dict) -> object:
        return BuildRequestV5.model_validate({"expectations": [expectation]}).model_dump(mode="json")

    assert dump(spelled) == dump(canonical)
    with pytest.raises(ValidationError, match="build expectations must be unique"):
        BuildRequestV5.model_validate({"expectations": [spelled, canonical]})


def test_the_published_range_bounds_carry_no_repair_alias() -> None:
    properties = BuildRequestV5.model_json_schema()["$defs"]["RangeExpectation"]["properties"]

    assert "x-datamimic-repair-aliases" not in properties["minimum"]
    assert properties["min"] == properties["minimum"] and properties["max"] == properties["maximum"]
