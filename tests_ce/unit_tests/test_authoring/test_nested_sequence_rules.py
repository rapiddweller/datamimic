# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

"""Finite numeric sequence exhaustion at nested-generate scope."""

import pytest

from datamimic_ce.authoring.contracts import AuthoringStage
from datamimic_ce.authoring.dryrun import dry_run_source
from datamimic_ce.authoring.linter import lint_source
from datamimic_ce.enums.distribution_enums import POSITIONAL_NUMBER_SEQUENCES, NumberDistribution


def _nested_model(
    distribution: str,
    *,
    parent: str = 'count="8"',
    child: str = 'count="2"',
    maximum: str = "2",
    field_condition: str = "",
) -> str:
    return (
        '<setup rngSeed="1">'
        f'<generate name="parents" {parent}>'
        f'<generate name="children" {child}>'
        f'<key name="line_no" type="int" min="1" max="{maximum}" '
        f'distribution="{distribution}" {field_condition}/>'
        "</generate></generate></setup>"
    )


@pytest.mark.parametrize("distribution", sorted(member.value for member in POSITIONAL_NUMBER_SEQUENCES))
def test_dm317_rejects_proven_finite_nested_exhaustion(distribution: str) -> None:
    result = lint_source(_nested_model(distribution))
    diagnostic = next(diag for diag in result.diagnostics if diag.rule == "DM317")
    assert diagnostic.severity.value == "error"
    assert "demand=16" in diagnostic.message
    assert not result.ok


def test_dm317_stops_dry_run_before_runtime_execution() -> None:
    result = dry_run_source(_nested_model("step"))
    assert result.stage is AuthoringStage.LINT
    assert not result.products
    assert any(diag.rule == "DM317" for diag in result.diagnostics)


@pytest.mark.parametrize(
    "distribution",
    sorted(member.value for member in NumberDistribution if member not in POSITIONAL_NUMBER_SEQUENCES),
)
def test_non_finite_numeric_distributions_do_not_emit_nested_exhaustion(distribution: str) -> None:
    result = lint_source(_nested_model(distribution))
    assert not [diag for diag in result.diagnostics if diag.rule in {"DM317", "DM318"}]


@pytest.mark.parametrize(
    ("distribution", "maximum"),
    (
        ("step", "16"),
        ("increment", "16"),
        ("shuffle", "16"),
        ("wedge", "16"),
        ("bitreverse", "16"),
        ("fibonacci", "1000"),
        ("padovan", "100"),
    ),
)
def test_enough_finite_capacity_is_clean(distribution: str, maximum: str) -> None:
    enough = lint_source(_nested_model(distribution, maximum=maximum))
    assert not [diag for diag in enough.diagnostics if diag.rule in {"DM317", "DM318"}]


def test_top_level_finite_sequence_is_out_of_nested_scope() -> None:
    top_level = lint_source(
        '<setup rngSeed="1"><generate name="rows" count="16">'
        '<key name="n" type="int" min="1" max="2" distribution="step"/>'
        "</generate></setup>"
    )
    assert not [diag for diag in top_level.diagnostics if diag.rule in {"DM317", "DM318"}]


def test_nested_key_count_contributes_to_proven_sequence_demand() -> None:
    model = (
        '<setup rngSeed="1"><generate name="parents" count="2">'
        '<generate name="children" count="2">'
        '<nestedKey name="items" type="list" count="2">'
        '<key name="n" type="int" min="1" max="4" distribution="step"/>'
        "</nestedKey></generate></generate></setup>"
    )
    result = lint_source(model)
    diagnostic = next(diag for diag in result.diagnostics if diag.rule == "DM317")
    assert "demand=8" in diagnostic.message


def test_top_level_nested_key_is_nested_but_dict_scope_has_cardinality_one() -> None:
    list_model = (
        '<setup rngSeed="1"><generate name="parents" count="2">'
        '<nestedKey name="items" type="list" count="2">'
        '<key name="n" type="int" min="1" max="2" distribution="step"/>'
        "</nestedKey></generate></setup>"
    )
    assert any(diag.rule == "DM317" for diag in lint_source(list_model).diagnostics)

    dict_model = (
        '<setup rngSeed="1"><generate name="parents" count="2">'
        '<nestedKey name="item" type="dict">'
        '<key name="n" type="int" min="1" max="2" distribution="step"/>'
        "</nestedKey></generate></setup>"
    )
    assert not [diag for diag in lint_source(dict_model).diagnostics if diag.rule in {"DM317", "DM318"}]


@pytest.mark.parametrize(
    ("parent", "child", "field_condition"),
    (
        ('source="rows.csv" distribution="ordered"', 'count="2"', ""),
        ('count="{parent_count}"', 'count="2"', ""),
        ('count="8"', 'count="{child_count}"', ""),
        ('count="8"', 'count="2"', 'condition="is_active"'),
    ),
)
def test_dm318_hints_when_nested_demand_cannot_be_proven(
    parent: str,
    child: str,
    field_condition: str,
) -> None:
    result = lint_source(_nested_model("step", parent=parent, child=child, field_condition=field_condition))
    diagnostics = [diag for diag in result.diagnostics if diag.rule in {"DM317", "DM318"}]
    assert [(diag.rule, diag.severity.value) for diag in diagnostics] == [("DM318", "hint")]


def test_conditional_nested_key_cardinality_is_not_claimed_as_static() -> None:
    model = (
        '<setup rngSeed="1"><generate name="parents" count="8">'
        '<nestedKey name="items" type="list" count="2" condition="is_active">'
        '<key name="n" type="int" min="1" max="2" distribution="step"/>'
        "</nestedKey></generate></setup>"
    )
    diagnostics = [diag for diag in lint_source(model).diagnostics if diag.rule in {"DM317", "DM318"}]
    assert [(diag.rule, diag.severity.value) for diag in diagnostics] == [("DM318", "hint")]
    assert "has condition=" in diagnostics[0].message


def test_dm315_is_non_blocking_local_sequence_guidance() -> None:
    xml = (
        '<setup rngSeed="1"><generate name="parents" count="8">'
        '<generate name="children" count="2">'
        '<key name="line_no" generator="IncrementGenerator"/>'
        '<key name="order_id" script="parent.customer_id * 100 + this.line_no"/>'
        "</generate></generate></setup>"
    )
    result = lint_source(xml)
    diagnostic = next(diag for diag in result.diagnostics if diag.rule == "DM315")
    assert diagnostic.severity.value == "hint"
    assert "valid local sequence" in diagnostic.message
    assert "Only when global uniqueness is required" in diagnostic.fix_hint
    assert result.ok
