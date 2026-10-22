# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Single parse, validation, and evaluation owner for bounded row conditions."""

from __future__ import annotations

import ast
import math
import operator
from collections.abc import Callable, Container, Mapping
from decimal import Decimal
from enum import StrEnum

MAX_CONDITION_LENGTH = 4096
MAX_CONDITION_NODES = 96
MAX_CONDITION_DEPTH = 12
MAX_CONTAINER_ITEMS = 64
MAX_STRING_LENGTH = 1024
MAX_INTEGER_BITS = 256
MAX_FLOAT_MAGNITUDE = 1e100
MAX_DECIMAL_ADJUSTED_EXPONENT = 128

# Keyed by node type because the evaluator dispatches on types, not on symbol strings.
_OPERATORS: Mapping[type[ast.AST], str] = {
    ast.And: "and",
    ast.Or: "or",
    ast.Not: "not",
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
    ast.In: "in",
    ast.NotIn: "not in",
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.UAdd: "+",
    ast.USub: "-",
}


def _supported_operators() -> str:
    # Unary and binary +/- share a symbol, so the list is de-duplicated for display.
    symbols: list[str] = []
    for symbol in _OPERATORS.values():
        if symbol not in symbols:
            symbols.append(symbol)
    return ", ".join(symbols)


_SUPPORTED_OPERATORS = _supported_operators()

_ALLOWED_NODES = (
    ast.Expression,
    ast.Name,
    ast.Attribute,
    ast.Subscript,
    ast.Call,
    ast.Constant,
    ast.Load,
    ast.Compare,
    ast.BoolOp,
    ast.BinOp,
    ast.UnaryOp,
    ast.List,
    ast.Tuple,
    ast.Set,
    *_OPERATORS,
)

ROW_CONDITION_GRAMMAR = (
    f"Operators: {_SUPPORTED_OPERATORS}. "
    "Operands: captured field names, dot access into nested mappings, numbers, strings, booleans, None, "
    "and list, tuple or set literals; len(value) is the only call. "
    "Indexes: constant non-negative integer indexes or constant string keys; negative indexes such as items[-1] "
    "are rejected. Arithmetic is numeric only (no string concatenation). "
    f"Numeric budget: integers up to {MAX_INTEGER_BITS} bits, finite floats up to magnitude "
    f"{MAX_FLOAT_MAGNITUDE:.0e}, decimals with an adjusted exponent between -{MAX_DECIMAL_ADJUSTED_EXPONENT} and {MAX_DECIMAL_ADJUSTED_EXPONENT}. "
    f"Budgets: {MAX_CONDITION_LENGTH} characters, {MAX_CONDITION_NODES} AST nodes, nesting depth "
    f"{MAX_CONDITION_DEPTH}, {MAX_CONTAINER_ITEMS} container items, strings up to {MAX_STRING_LENGTH} characters."
)


class RowConditionFailure(StrEnum):
    """Why a row condition could not be evaluated; the texts are static and never echo row values."""

    MISSING_VALUE = "a referenced field, attribute or index is absent from a captured row"
    UNSUPPORTED_VALUE = "a value is not None, bool, number, string, list or mapping; dates are not comparable"
    OVER_BUDGET = "a value exceeds the numeric, string length, container size or nesting budget"
    TYPE_MISMATCH = "operands have incompatible types"
    ARITHMETIC = "arithmetic failed or left the numeric budget"


class RowConditionError(ValueError):
    """Evaluation failure with a typed reason; a ValueError so the pydantic parse path still reports it."""

    def __init__(self, failure: RowConditionFailure) -> None:
        ValueError.__init__(self, failure.value)
        self.failure = failure


def parse_row_condition(condition: str) -> ast.Expression:
    """Parse and validate the complete closed row-condition grammar."""

    if len(condition) > MAX_CONDITION_LENGTH:
        raise ValueError(f"condition exceeds the {MAX_CONDITION_LENGTH}-character length budget")
    try:
        tree = ast.parse(condition, mode="eval")
    except SyntaxError as error:
        raise ValueError("row condition must be a valid expression") from error
    nodes = tuple(ast.walk(tree))
    if len(nodes) > MAX_CONDITION_NODES or _depth(tree) > MAX_CONDITION_DEPTH:
        raise ValueError(
            f"condition exceeds the AST budget of {MAX_CONDITION_NODES} nodes and depth {MAX_CONDITION_DEPTH}"
        )
    for node in nodes:
        if isinstance(node, ast.Constant):
            _safe_value(node.value)
        if isinstance(node, ast.List | ast.Tuple | ast.Set) and len(node.elts) > MAX_CONTAINER_ITEMS:
            raise ValueError(f"condition exceeds the container budget of {MAX_CONTAINER_ITEMS} items")
        if (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Mult)
            and any(
                isinstance(operand, ast.List | ast.Tuple | ast.Set)
                or (isinstance(operand, ast.Constant) and isinstance(operand.value, str))
                for operand in (node.left, node.right)
            )
        ):
            raise ValueError("sequence repetition is forbidden in row conditions")
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(
                f"row condition node '{type(node).__name__}' is not supported; "
                f"supported operators are {_SUPPORTED_OPERATORS}"
            )
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            raise ValueError("row condition names cannot start with '__'")
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise ValueError("row condition attributes cannot start with '_'")
        if isinstance(node, ast.Call) and (
            not isinstance(node.func, ast.Name) or node.func.id != "len" or len(node.args) != 1 or node.keywords
        ):
            raise ValueError("row conditions support only len(value)")
        if isinstance(node, ast.Subscript) and (
            not isinstance(node.slice, ast.Constant) or type(node.slice.value) not in (int, str)
        ):
            raise ValueError("row condition indexes must be constant integers or strings")
    return tree


def _depth(node: ast.AST) -> int:
    return 1 + max((_depth(child) for child in ast.iter_child_nodes(node)), default=0)


def _safe_number(
    value: object, out_of_budget: RowConditionFailure = RowConditionFailure.OVER_BUDGET
) -> int | float | Decimal:
    # A non-number is a type error; only a number outside the budget (or an arithmetic result) is a budget error.
    if isinstance(value, bool) or not isinstance(value, int | float | Decimal):
        raise RowConditionError(RowConditionFailure.TYPE_MISMATCH)
    # Exact types: an int or float subclass could override operators inside the closed evaluator.
    if type(value) is int and value.bit_length() <= MAX_INTEGER_BITS:
        return value
    if type(value) is float and math.isfinite(value) and abs(value) <= MAX_FLOAT_MAGNITUDE:
        return value
    if isinstance(value, Decimal) and value.is_finite() and abs(value.adjusted()) <= MAX_DECIMAL_ADJUSTED_EXPONENT:
        return value
    raise RowConditionError(out_of_budget)


def _safe_value(value: object, depth: int = 0) -> object:
    if depth > MAX_CONDITION_DEPTH:
        raise RowConditionError(RowConditionFailure.OVER_BUDGET)
    if value is None or type(value) is bool:
        return value
    if isinstance(value, int | float | Decimal):
        return _safe_number(value)
    if type(value) is str:
        if len(value) <= MAX_STRING_LENGTH:
            return value
        raise RowConditionError(RowConditionFailure.OVER_BUDGET)
    if isinstance(value, list | tuple | set | dict):
        if len(value) > MAX_CONTAINER_ITEMS:
            raise RowConditionError(RowConditionFailure.OVER_BUDGET)
        items = value.values() if isinstance(value, dict) else value
        for item in items:
            _safe_value(item, depth + 1)
        return value
    raise RowConditionError(RowConditionFailure.UNSUPPORTED_VALUE)


def evaluate_row_condition(condition: str, row: Mapping[str, object]) -> bool:
    """Evaluate one prevalidated row condition against data-only field values."""

    result = _evaluate(parse_row_condition(condition), row)
    if type(result) is not bool:
        raise RowConditionError(RowConditionFailure.TYPE_MISMATCH)
    return result


def _comparison(operation: Callable[..., object]) -> Callable[[object, object], bool]:
    def compare(left: object, right: object) -> bool:
        return bool(operation(left, right))

    return compare


def _contains(value: object, container: object) -> bool:
    if not isinstance(container, Container):
        raise TypeError(f"argument of type '{type(container).__name__}' is not iterable")
    return operator.contains(container, value)


def _not_contains(value: object, container: object) -> bool:
    return not _contains(value, container)


_COMPARISONS: Mapping[type[ast.cmpop], Callable[[object, object], bool]] = {
    ast.Eq: _comparison(operator.eq),
    ast.NotEq: _comparison(operator.ne),
    ast.Lt: _comparison(operator.lt),
    ast.LtE: _comparison(operator.le),
    ast.Gt: _comparison(operator.gt),
    ast.GtE: _comparison(operator.ge),
    ast.In: _contains,
    ast.NotIn: _not_contains,
}


def _evaluate(node: ast.AST, row: Mapping[str, object]) -> object:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body, row)
    if isinstance(node, ast.Name):
        if node.id not in row:
            raise RowConditionError(RowConditionFailure.MISSING_VALUE)
        return _safe_value(row[node.id])
    if isinstance(node, ast.Attribute):
        parent = _evaluate(node.value, row)
        if not isinstance(parent, Mapping):
            raise RowConditionError(RowConditionFailure.TYPE_MISMATCH)
        if node.attr not in parent:
            raise RowConditionError(RowConditionFailure.MISSING_VALUE)
        value = parent[node.attr]
        if callable(value):
            raise RowConditionError(RowConditionFailure.UNSUPPORTED_VALUE)
        return value
    if isinstance(node, ast.Subscript):
        container = _evaluate(node.value, row)
        if not isinstance(node.slice, ast.Constant):
            raise ValueError("row condition indexes must be constant integers or strings")
        index = node.slice.value
        if not isinstance(container, Mapping | list | tuple):
            raise RowConditionError(RowConditionFailure.TYPE_MISMATCH)
        try:
            if isinstance(container, Mapping):
                value = container[index]
            else:
                if not isinstance(index, int):
                    raise TypeError("list and tuple indexes must be integers")
                value = container[index]
        except (IndexError, KeyError, TypeError) as error:
            raise RowConditionError(RowConditionFailure.MISSING_VALUE) from error
        if callable(value):
            raise RowConditionError(RowConditionFailure.UNSUPPORTED_VALUE)
        return value
    if isinstance(node, ast.Call):
        value = _evaluate(node.args[0], row)
        if not isinstance(value, Mapping | list | tuple | set | str):
            raise RowConditionError(RowConditionFailure.TYPE_MISMATCH)
        return len(value)
    if isinstance(node, ast.Constant):
        return _safe_value(node.value)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values = [_evaluate(item, row) for item in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(values)
        if isinstance(node, ast.Set):
            try:
                return set(values)
            except TypeError as error:
                # An unhashable captured value (a list or mapping) cannot be a set member.
                raise RowConditionError(RowConditionFailure.TYPE_MISMATCH) from error
        return values
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub, ast.Not)):
        value = _evaluate(node.operand, row)
        if isinstance(node.op, ast.Not):
            if type(value) is not bool:
                raise RowConditionError(RowConditionFailure.TYPE_MISMATCH)
            return not value
        number = _safe_number(value)
        return _safe_number(+number if isinstance(node.op, ast.UAdd) else -number)
    if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
        result = _evaluate(node.values[0], row)
        if type(result) is not bool:
            raise RowConditionError(RowConditionFailure.TYPE_MISMATCH)
        for expression in node.values[1:]:
            if isinstance(node.op, ast.And) and not result:
                return False
            if isinstance(node.op, ast.Or) and result:
                return True
            result = _evaluate(expression, row)
            if type(result) is not bool:
                raise RowConditionError(RowConditionFailure.TYPE_MISMATCH)
        return result
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
        numeric_left = _safe_number(_evaluate(node.left, row))
        numeric_right = _safe_number(_evaluate(node.right, row))
        try:
            result = operations[type(node.op)](numeric_left, numeric_right)
        except ArithmeticError as error:
            raise RowConditionError(RowConditionFailure.ARITHMETIC) from error
        except TypeError as error:
            # Mixed float and Decimal operands are not combinable in Python.
            raise RowConditionError(RowConditionFailure.TYPE_MISMATCH) from error
        return _safe_number(result, RowConditionFailure.ARITHMETIC)
    if isinstance(node, ast.Compare):
        left = _evaluate(node.left, row)
        for operation_node, comparator in zip(node.ops, node.comparators, strict=True):
            right = _evaluate(comparator, row)
            operation = _COMPARISONS.get(type(operation_node))
            try:
                holds = operation is not None and operation(left, right)
            except TypeError as error:
                raise RowConditionError(RowConditionFailure.TYPE_MISMATCH) from error
            if not holds:
                return False
            left = right
        return True
    raise ValueError(f"unsupported row condition node '{type(node).__name__}'")


__all__ = ["evaluate_row_condition", "parse_row_condition"]
