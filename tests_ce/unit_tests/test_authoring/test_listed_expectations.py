# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Build lists each expectation, declared or derived, with its result (#688)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError
from pydantic_core import to_json, to_jsonable_python

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.acceptance_contract import (
    AcceptanceCheckV1,
    AcceptanceProductV1,
    AcceptanceSpecV1,
)
from datamimic_ce.authoring.domain.acceptance_evaluation import list_expectations
from datamimic_ce.authoring.domain.coverage import (
    MAX_LISTED_EXPECTATIONS,
    ExpectationResult,
    ListedExpectations,
)
from datamimic_ce.authoring.domain.expectations import (
    DeclaredSinkIdentity,
    DeclaredSinkRowsSubject,
    ExactCountExpectation,
    ExpectationIntentKind,
    ExpectationSubjectKind,
    ProductRowsSubject,
)
from datamimic_ce.authoring.domain.proof import AcceptanceOrigin
from datamimic_ce.authoring.domain.requests import (
    PROJECT_ENTRY_PATH,
    ReadyBuild,
    ReadyWithGapsBuild,
    RejectedBuild,
)
from datamimic_ce.interfaces.mcp.server import MAX_RESULT_CHARACTERS
from tests_ce.authoring_project import build_project

_SCENARIOS = Path(__file__).parents[2] / "scenarios"
_SEEDED = (
    '<setup rngSeed="7"><generate name="cities" count="3">'
    '<key name="id" generator="IncrementGenerator"/></generate></setup>'
)
# No literal count: Build derives no exact_count, so every expectation of this project is declared.
_NO_LITERAL_COUNT = (
    '<setup rngSeed="7"><generate name="rows" count="{1 + 1}"><key name="id" constant="1"/></generate></setup>'
)
_ROWS_TWO = {"kind": "exact_count", "subject": {"kind": "product", "product": "rows"}, "count": 2}
_ROWS_ID = {"kind": "field_present", "subject": {"kind": "product", "product": "rows"}, "field": "id"}
_CITIES = {"kind": "exact_count", "subject": {"kind": "product", "product": "cities"}, "count": 3}


def _proven(result: object) -> ReadyBuild | ReadyWithGapsBuild:
    assert isinstance(result, ReadyBuild | ReadyWithGapsBuild), result
    return result


def test_a_declared_only_project_lists_its_declared_expectations_as_passed(tmp_path: Path) -> None:
    result = _proven(build_project(tmp_path, _NO_LITERAL_COUNT, expectations=[_ROWS_TWO, _ROWS_ID]))

    listed = result.expectations
    assert (listed.total, listed.truncated) == (result.coverage.expectation_count, False)
    assert len(listed.items) == listed.total == 2
    assert {item.origin for item in listed.items} == {AcceptanceOrigin.MODEL}
    assert {item.result for item in listed.items} == {ExpectationResult.PASSED}
    assert [(item.kind, item.field) for item in listed.items] == [
        (ExpectationIntentKind.EXACT_COUNT, None),
        (ExpectationIntentKind.FIELD_PRESENT, "id"),
    ]


def test_a_derived_only_project_lists_the_checks_that_build_added(tmp_path: Path) -> None:
    result = _proven(build_project(tmp_path, _SEEDED))

    listed = result.expectations
    assert len(listed.items) == listed.total == result.coverage.expectation_count >= 1
    assert {item.origin for item in listed.items} == {AcceptanceOrigin.DERIVED}
    assert {item.result for item in listed.items} == {ExpectationResult.PASSED}
    assert ExpectationIntentKind.EXACT_COUNT in {item.kind for item in listed.items}


def test_a_mixed_project_marks_each_origin(tmp_path: Path) -> None:
    caller = {"expectation": _CITIES | {"count": 3}, "origin": "caller"}
    declared_key = {"kind": "unique", "subject": {"kind": "product", "product": "cities"}, "field": "id"}

    result = _proven(build_project(tmp_path, _SEEDED, expectations=[declared_key], acceptance_requirements=[caller]))

    listed = result.expectations
    assert len(listed.items) == listed.total == result.coverage.expectation_count
    assert {item.origin for item in listed.items} == set(AcceptanceOrigin)


def test_a_nested_project_names_the_subject_and_the_field_of_each_kind(tmp_path: Path) -> None:
    shutil.copytree(_SCENARIOS / "s02_parent_child", tmp_path, dirs_exist_ok=True)

    result = _proven(create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH).build())

    by_kind = {item.kind: item for item in result.expectations.items if item.origin is AcceptanceOrigin.MODEL}
    assert len(result.expectations.items) == result.coverage.expectation_count
    per_parent = by_kind[ExpectationIntentKind.PER_PARENT_COUNT]
    assert per_parent.subject.kind is ExpectationSubjectKind.PER_PARENT and per_parent.field is None
    foreign_key = by_kind[ExpectationIntentKind.FOREIGN_KEY]
    assert (foreign_key.subject.kind, foreign_key.field) == (ExpectationSubjectKind.PRODUCT, "customer_id")
    assert {item.result for item in result.expectations.items} == {ExpectationResult.PASSED}


def test_a_failing_expectation_is_listed_as_failed_and_the_others_as_passed(tmp_path: Path) -> None:
    wrong = _CITIES | {"count": 4}

    result = build_project(tmp_path, _SEEDED, expectations=[wrong, {"kind": "field_present", **_field("id")}])

    assert isinstance(result, RejectedBuild)
    listed = result.expectations
    assert len(listed.items) == listed.total == 2 + 1  # the derived exact_count joins the two declared ones
    failed = [item for item in listed.items if item.result is ExpectationResult.FAILED]
    assert [(item.origin, item.kind) for item in failed] == [
        (AcceptanceOrigin.MODEL, ExpectationIntentKind.EXACT_COUNT)
    ]
    assert {item.result for item in listed.items if item not in failed} == {ExpectationResult.PASSED}


def test_a_run_that_fails_leaves_every_expectation_not_evaluated(tmp_path: Path) -> None:
    broken = _NO_LITERAL_COUNT.replace('constant="1"', 'script="no_such_name"')

    result = build_project(tmp_path, broken, expectations=[_ROWS_TWO, _ROWS_ID])

    assert isinstance(result, RejectedBuild)
    assert result.expectations.total == 2
    assert {item.result for item in result.expectations.items} == {ExpectationResult.NOT_EVALUATED}


def test_a_rejection_before_the_acceptance_is_projected_lists_nothing(tmp_path: Path) -> None:
    result = build_project(tmp_path, "<setup><generate", expectations=[_ROWS_TWO])

    assert isinstance(result, RejectedBuild)
    assert result.expectations == ListedExpectations(total=0, truncated=False, items=())


def _field(name: str) -> dict[str, object]:
    return {"subject": {"kind": "product", "product": "cities"}, "field": name}


def _spec(count: int) -> AcceptanceSpecV1:
    product = AcceptanceProductV1(name="rows", runtime_name="rows", capture_name="rows")
    checks = tuple(
        AcceptanceCheckV1(
            expectation=ExactCountExpectation(subject=ProductRowsSubject(product="rows"), count=index),
            path=("expectations", index),
        )
        for index in range(count)
    )
    return AcceptanceSpecV1(products=(product,), checks=checks)


@pytest.mark.parametrize(
    ("count", "truncated"), [(MAX_LISTED_EXPECTATIONS, False), (MAX_LISTED_EXPECTATIONS + 1, True)]
)
def test_the_list_is_capped_with_a_truncated_flag_and_leaves_most_of_the_mcp_limit(count: int, truncated: bool) -> None:
    listed = list_expectations(_spec(count), None)

    assert (listed.total, listed.truncated, len(listed.items)) == (count, truncated, MAX_LISTED_EXPECTATIONS)
    # A declared sink is the longest subject; names of 20 characters are already long for a product or a table.
    sink = DeclaredSinkRowsSubject(sink=DeclaredSinkIdentity(kind="database", environment="e" * 20, entity="t" * 20))
    heavy = listed.items[0].model_copy(update={"subject": sink})
    size = len(
        to_json(
            to_jsonable_python(
                ListedExpectations(total=count, truncated=truncated, items=(heavy,) * MAX_LISTED_EXPECTATIONS)
            )
        )
    )
    # The evidence and the diagnostics need the rest of the limit.
    assert size < MAX_RESULT_CHARACTERS // 2


def test_a_ready_build_whose_list_disagrees_with_its_coverage_is_refused(tmp_path: Path) -> None:
    result = _proven(build_project(tmp_path, _SEEDED))
    wrong = result.coverage.model_copy(update={"expectation_count": result.coverage.expectation_count + 1})

    with pytest.raises(ValidationError, match="must count the expectations of coverage"):
        type(result)(**{**dict(result), "coverage": wrong})


@pytest.mark.parametrize(("total", "truncated", "items"), [(1, False, 2), (3, False, 1), (3, True, 3), (0, True, 0)])
def test_a_list_must_be_all_of_the_expectations_or_the_capped_first_ones(
    total: int, truncated: bool, items: int
) -> None:
    item = list_expectations(_spec(1), None).items[0]

    with pytest.raises(ValidationError, match="truncated must say so"):
        ListedExpectations(total=total, truncated=truncated, items=(item,) * items)
