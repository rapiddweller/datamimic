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

_ALLOWED_NODES = (
    ast.Expression,
    ast.Name,
    ast.Attribute,
    ast.Subscript,
    ast.Call,
    ast.Constant,
    ast.Load,
    ast.Compare,
    ast.GtE,
    ast.Gt,
    ast.LtE,
    ast.Lt,
    ast.Eq,
    ast.NotEq,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.BinOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.UnaryOp,
    ast.UAdd,
    ast.USub,
    ast.Not,
    ast.List,
    ast.Tuple,
    ast.Set,
    ast.In,
    ast.NotIn,
)


def parse_row_condition(condition: str) -> ast.Expression:
    """Parse and validate the complete closed row-condition grammar."""

    if len(condition) > 4096:
        raise ValueError("condition exceeds the expression length budget")
    try:
        tree = ast.parse(condition, mode="eval")
    except SyntaxError as error:
        raise ValueError("row condition must be a valid expression") from error
    nodes = tuple(ast.walk(tree))
    if len(nodes) > 96 or _depth(tree) > 12:
        raise ValueError("condition exceeds the AST budget")
    for node in nodes:
        if isinstance(node, ast.Constant):
            _safe_value(node.value)
        if isinstance(node, ast.List | ast.Tuple | ast.Set) and len(node.elts) > 64:
            raise ValueError("condition exceeds the container budget")
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
            raise ValueError(f"row condition node '{type(node).__name__}' is not supported")
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


def _safe_number(value: object) -> int | float | Decimal:
    if type(value) is int and value.bit_length() <= 256:
        return value
    if type(value) is float and math.isfinite(value) and abs(value) <= 1e100:
        return value
    if isinstance(value, Decimal) and value.is_finite() and abs(value.adjusted()) <= 128:
        return value
    raise ValueError("arithmetic requires bounded finite numeric operands")


def _safe_value(value: object, depth: int = 0) -> object:
    if depth > 12:
        raise ValueError("row value exceeds the nesting budget")
    if value is None or type(value) is bool:
        return value
    if isinstance(value, int | float | Decimal):
        return _safe_number(value)
    if type(value) is str and len(value) <= 1024:
        return value
    if isinstance(value, list | tuple | set | dict):
        if len(value) > 64:
            raise ValueError("row value exceeds the container budget")
        items = value.values() if isinstance(value, dict) else value
        for item in items:
            _safe_value(item, depth + 1)
        return value
    raise ValueError("row condition operand must be bounded data")


def evaluate_row_condition(condition: str, row: Mapping[str, object]) -> bool:
    """Evaluate one prevalidated row condition against data-only field values."""

    result = _evaluate(parse_row_condition(condition), row)
    if type(result) is not bool:
        raise ValueError("row condition must evaluate to bool")
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
            raise ValueError(f"missing field '{node.id}'")
        return _safe_value(row[node.id])
    if isinstance(node, ast.Attribute):
        parent = _evaluate(node.value, row)
        if not isinstance(parent, Mapping):
            raise ValueError("row condition attributes require nested mapping values")
        if node.attr not in parent:
            raise ValueError(f"missing field '{node.attr}'")
        value = parent[node.attr]
        if callable(value):
            raise ValueError("row condition attributes cannot resolve callable values")
        return value
    if isinstance(node, ast.Subscript):
        container = _evaluate(node.value, row)
        if not isinstance(node.slice, ast.Constant):
            raise ValueError("row condition indexes must be constant integers or strings")
        index = node.slice.value
        if not isinstance(container, Mapping | list | tuple):
            raise ValueError("row condition indexing requires a mapping, list, or tuple")
        try:
            if isinstance(container, Mapping):
                value = container[index]
            else:
                if not isinstance(index, int):
                    raise TypeError("list and tuple indexes must be integers")
                value = container[index]
        except (IndexError, KeyError, TypeError) as error:
            raise ValueError(f"row condition index {index!r} is unavailable") from error
        if callable(value):
            raise ValueError("row condition indexes cannot resolve callable values")
        return value
    if isinstance(node, ast.Call):
        value = _evaluate(node.args[0], row)
        if not isinstance(value, Mapping | list | tuple | set | str):
            raise ValueError("len() requires a bounded collection or string")
        return len(value)
    if isinstance(node, ast.Constant):
        return _safe_value(node.value)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values = [_evaluate(item, row) for item in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(values)
        if isinstance(node, ast.Set):
            return set(values)
        return values
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub, ast.Not)):
        value = _evaluate(node.operand, row)
        if isinstance(node.op, ast.Not):
            if type(value) is not bool:
                raise ValueError("not requires a boolean operand")
            return not value
        number = _safe_number(value)
        return _safe_number(+number if isinstance(node.op, ast.UAdd) else -number)
    if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
        result = _evaluate(node.values[0], row)
        if type(result) is not bool:
            raise ValueError("boolean operators require boolean operands")
        for expression in node.values[1:]:
            if isinstance(node.op, ast.And) and not result:
                return False
            if isinstance(node.op, ast.Or) and result:
                return True
            result = _evaluate(expression, row)
            if type(result) is not bool:
                raise ValueError("boolean operators require boolean operands")
        return result
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
        numeric_left = _safe_number(_evaluate(node.left, row))
        numeric_right = _safe_number(_evaluate(node.right, row))
        return _safe_number(operations[type(node.op)](numeric_left, numeric_right))
    if isinstance(node, ast.Compare):
        left = _evaluate(node.left, row)
        for operation_node, comparator in zip(node.ops, node.comparators, strict=True):
            right = _evaluate(comparator, row)
            operation = _COMPARISONS.get(type(operation_node))
            if operation is None or not operation(left, right):
                return False
            left = right
        return True
    raise ValueError(f"unsupported row condition node '{type(node).__name__}'")


__all__ = ["evaluate_row_condition", "parse_row_condition"]
