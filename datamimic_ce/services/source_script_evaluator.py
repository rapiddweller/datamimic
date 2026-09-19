"""Evaluate source-file templates without coupling data sources to task helpers."""

from __future__ import annotations

import re
from typing import Any

from datamimic_ce.contexts.context import Context


def interpolate_variables(context: Context, expression: str, prefix: str, suffix: str) -> str:
    """Replace configured variable markers with values from the current context."""
    pattern = rf"{re.escape(prefix)}([^{re.escape(prefix)}]\S*?){re.escape(suffix)}"
    if re.search(pattern, expression) is None:
        return expression
    return re.sub(
        pattern,
        lambda match: str(context.evaluate_python_expression(match.group(1))),
        expression,
    )


def evaluate_source_template(context: Context, data: Any, prefix: str, suffix: str) -> Any:
    """Recursively evaluate expressions embedded in source values.

    ``data`` and the return value are ``Any`` because source files contain
    arbitrary JSON-like values (dicts, lists, scalars) sourced from outside
    the generator pipeline — there is no narrower type we can enforce at this
    boundary.
    """
    if isinstance(data, dict):
        return {
            key: evaluate_source_template(context, value, prefix, suffix)
            for key, value in data.items()
        }
    if isinstance(data, list):
        result: list[Any] = []
        for value in data:
            evaluated = evaluate_source_template(context, value, prefix, suffix)
            if isinstance(value, list):
                result.extend(evaluated)
            else:
                result.append(evaluated)
        return result
    if not isinstance(data, str) or not data.strip():
        return data
    if data.startswith("{") and data.endswith("}"):
        match = re.fullmatch(r"{(.*)}", data)
        return context.evaluate_python_expression(match.group(1)) if match is not None else None
    return interpolate_variables(context, data, prefix, suffix)


__all__ = ["evaluate_source_template", "interpolate_variables"]
