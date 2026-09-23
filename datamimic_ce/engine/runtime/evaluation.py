"""Evaluate expressions embedded in source values."""

from __future__ import annotations

import re
from typing import Protocol, TypeGuard


class ExpressionContext(Protocol):
    def evaluate_python_expression(self, expr: str, local_namespace: dict[str, object] | None = None) -> object: ...


def evaluate_python(expression: str, global_namespace: dict[str, object], local_namespace: dict[str, object]) -> object:
    """Evaluate one DSL expression in the supplied globals and locals."""
    return eval(expression, global_namespace, local_namespace)


def interpolate_variables(context: ExpressionContext, expression: str, prefix: str, suffix: str) -> str:
    """Replace configured variable markers with values from the current context."""
    pattern = rf"{re.escape(prefix)}([^{re.escape(prefix)}]\S*?){re.escape(suffix)}"
    if re.search(pattern, expression) is None:
        return expression
    return re.sub(
        pattern,
        lambda match: str(context.evaluate_python_expression(match.group(1))),
        expression,
    )


def _dictionary(value: object) -> TypeGuard[dict[object, object]]:
    return isinstance(value, dict)


def _evaluate_list(context: ExpressionContext, data: list[object], prefix: str, suffix: str) -> list[object]:
    result: list[object] = []
    for value in data:
        if isinstance(value, list):
            result.extend(_evaluate_list(context, value, prefix, suffix))
        else:
            result.append(evaluate_source_template(context, value, prefix, suffix))
    return result


def evaluate_source_template(context: ExpressionContext, data: object, prefix: str, suffix: str) -> object:
    """Recursively evaluate expressions embedded in source values."""
    if _dictionary(data):
        return {
            key: evaluate_source_template(context, value, prefix, suffix)
            for key, value in data.items()
        }
    if isinstance(data, list):
        return _evaluate_list(context, data, prefix, suffix)
    if not isinstance(data, str) or not data.strip():
        return data
    if data.startswith("{") and data.endswith("}"):
        match = re.fullmatch(r"{(.*)}", data)
        return context.evaluate_python_expression(match.group(1)) if match is not None else None
    return interpolate_variables(context, data, prefix, suffix)


__all__ = ["evaluate_python", "evaluate_source_template", "interpolate_variables"]
