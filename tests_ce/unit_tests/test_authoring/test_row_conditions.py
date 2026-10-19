from decimal import Decimal

import pytest

from datamimic_ce.authoring.domain.row_conditions import evaluate_row_condition, parse_row_condition

@pytest.mark.parametrize("expression", ["1 and True", "not 1", "True + 1 == 2", "name * 1000000 == ''", "value * value > 0"])
def test_rejects_non_boolean_or_unbounded_operands(expression):
    with pytest.raises(ValueError):
        evaluate_row_condition(expression, {"name": "abc", "value": 2 ** 200})

@pytest.mark.parametrize("expression", ["x" * 4097, " + ".join(["1"] * 100), repr("x" * 1025), "[1] * 3 == [1,1,1]"])
def test_parse_has_resource_budgets(expression):
    with pytest.raises(ValueError):
        parse_row_condition(expression)

@pytest.mark.parametrize("expression", ["False and missing > 0", "True or missing > 0"])
def test_boolean_operators_short_circuit(expression):
    assert evaluate_row_condition(expression, {}) is expression.startswith("True")


def test_nested_mapping_and_indexed_values_are_data_only():
    row = {"customer": {"balances": [Decimal("1.25")]}}
    assert evaluate_row_condition("len(customer.balances) == 1 and customer.balances[0] > 0", row)
    with pytest.raises(ValueError):
        evaluate_row_condition("customer.callback == 1", {"customer": {"callback": lambda: 1}})

@pytest.mark.parametrize("expression", ["__import__('os')", "customer.__class__", "customer[index]", "len(a, b)"])
def test_rejects_open_python_grammar(expression):
    with pytest.raises(ValueError):
        parse_row_condition(expression)
