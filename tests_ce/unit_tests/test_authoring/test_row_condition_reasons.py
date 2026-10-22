# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Row-condition grammar is advertised from the parser's own table, and evaluation failures carry typed reasons."""

import ast
import math
from datetime import datetime
from pathlib import Path

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import ReferenceRequest, ReferenceTopic
from datamimic_ce.authoring.domain.row_conditions import (
    _OPERATORS,
    _SUPPORTED_OPERATORS,
    MAX_CONDITION_LENGTH,
    MAX_DECIMAL_ADJUSTED_EXPONENT,
    MAX_FLOAT_MAGNITUDE,
    MAX_INTEGER_BITS,
    ROW_CONDITION_GRAMMAR,
    RowConditionError,
    RowConditionFailure,
    evaluate_row_condition,
    parse_row_condition,
)
from tests_ce.authoring_project import build_project

_SAMPLES = {
    ast.And: "a and b",
    ast.Or: "a or b",
    ast.Not: "not a",
    ast.Eq: "a == 1",
    ast.NotEq: "a != 1",
    ast.Lt: "a < 1",
    ast.LtE: "a <= 1",
    ast.Gt: "a > 1",
    ast.GtE: "a >= 1",
    ast.In: "a in b",
    ast.NotIn: "a not in b",
    ast.Add: "a + 1 == 2",
    ast.Sub: "a - 1 == 0",
    ast.Mult: "a * 1 == 1",
    ast.Div: "a / 1 == 1",
    ast.UAdd: "+a == 1",
    ast.USub: "-a == 1",
}


def test_every_advertised_operator_parses_and_unsupported_ones_name_the_list():
    assert set(_SAMPLES) == set(_OPERATORS)
    for sample in _SAMPLES.values():
        parse_row_condition(sample)
    with pytest.raises(ValueError) as error:
        parse_row_condition("a % 2 == 0")
    assert _SUPPORTED_OPERATORS in str(error.value)


def test_over_length_condition_names_the_length_budget():
    with pytest.raises(ValueError) as error:
        parse_row_condition("x" * (MAX_CONDITION_LENGTH + 1))
    assert str(MAX_CONDITION_LENGTH) in str(error.value)


def test_reference_row_condition_describes_the_grammar(tmp_path: Path):
    result = create_authoring_application(tmp_path).reference(
        ReferenceRequest(topic=ReferenceTopic.EXPECTATIONS, name="row_condition")
    )
    [entry] = result.entries
    condition = entry.json_schema["$defs"]["RowConditionExpectation"]["properties"]["condition"]
    assert ROW_CONDITION_GRAMMAR in condition["description"]


@pytest.mark.parametrize(
    "condition,row,failure",
    [
        ("when > '2026-01-01'", {"when": datetime(2026, 1, 1)}, RowConditionFailure.UNSUPPORTED_VALUE),
        ("id > 'x'", {"id": 5}, RowConditionFailure.TYPE_MISMATCH),
        ("id / 0 > 1", {"id": 1}, RowConditionFailure.ARITHMETIC),
        ("value * value > 0", {"value": 2**200}, RowConditionFailure.ARITHMETIC),
        ("customer.missing > 1", {"customer": {"id": 1}}, RowConditionFailure.MISSING_VALUE),
        ("note == 'x'", {"note": "x" * 2000}, RowConditionFailure.OVER_BUDGET),
        ("len(items) > 1", {"items": list(range(65))}, RowConditionFailure.OVER_BUDGET),
        ("first + last == 'ab'", {"first": "a", "last": "b"}, RowConditionFailure.TYPE_MISMATCH),
        ("flag + 1 == 2", {"flag": True}, RowConditionFailure.TYPE_MISMATCH),
        ("x + 1 == 2", {"x": None}, RowConditionFailure.TYPE_MISMATCH),
        ("-name == 1", {"name": "a"}, RowConditionFailure.TYPE_MISMATCH),
        ("score >= 0", {"score": math.nan}, RowConditionFailure.OVER_BUDGET),
        ("score >= 0", {"score": 1e101}, RowConditionFailure.OVER_BUDGET),
        ("x < 1e101", {"x": 1}, RowConditionFailure.OVER_BUDGET),
        ("{tags} == {1}", {"tags": [1]}, RowConditionFailure.TYPE_MISMATCH),
    ],
)
def test_evaluation_failures_carry_a_typed_reason(condition, row, failure):
    with pytest.raises(RowConditionError) as error:
        evaluate_row_condition(condition, row)
    assert error.value.failure is failure


def test_build_reports_a_date_operand_with_the_unsupported_reason(tmp_path: Path):
    build = build_project(
        tmp_path,
        '<setup rngSeed="1"><generate name="rows" count="2">'
        '<key name="when" generator="DateTimeGenerator"/></generate></setup>',
        expectations=[
            {
                "kind": "row_condition",
                "subject": {"kind": "product", "product": "rows"},
                "condition": "when > '2026-01-01'",
            }
        ],
    )
    assert build.diagnostics[0].message.endswith(RowConditionFailure.UNSUPPORTED_VALUE.value)


def test_grammar_names_the_string_budget():
    from datamimic_ce.authoring.domain.row_conditions import MAX_STRING_LENGTH, ROW_CONDITION_GRAMMAR

    assert str(MAX_STRING_LENGTH) in ROW_CONDITION_GRAMMAR


def test_grammar_names_the_numeric_budget_and_operand_rules():
    assert str(MAX_INTEGER_BITS) in ROW_CONDITION_GRAMMAR
    assert f"{MAX_FLOAT_MAGNITUDE:.0e}" in ROW_CONDITION_GRAMMAR
    assert str(MAX_DECIMAL_ADJUSTED_EXPONENT) in ROW_CONDITION_GRAMMAR
    assert "arithmetic is numeric only (no string concatenation)" in ROW_CONDITION_GRAMMAR.lower()
    assert "constant non-negative integer indexes" in ROW_CONDITION_GRAMMAR
