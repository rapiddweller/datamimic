"""Evaluate expressions embedded in source values."""

from __future__ import annotations

import re
import types
from typing import Protocol, TypeGuard

from datamimic_ce.engine.runtime.scripting.expression_globals import NON_VALUE_TYPES
from datamimic_ce.errors import DomainError, IssueCode, UserErrorBase, condition_evaluation_error, task_config_error

_SCOPE_GUIDANCE = (
    "check spelling, definition order and value shape; current-scope names can resolve bare, "
    "but existing outermost bare names win collisions; intermediate ancestor names need qualification; "
    "use this.name for the current scope, parent.name for the immediate enclosing record, "
    "or root.name for an outermost field when these aliases are available, or use a qualified scope path"
)


class ExpressionContext(Protocol):
    def evaluate_python_expression(self, expr: str, local_namespace: dict[str, object] | None = None) -> object: ...


class DotableDict:
    """Expose dictionary fields through attribute access while evaluating expressions."""

    def __init__(self, dictionary: dict[str, object]):
        self._dictionary = dictionary

    def __getattr__(self, name: str) -> object:
        if name not in self._dictionary:
            raise AttributeError(f"Cannot find attribute '{name}'")
        item = self._dictionary[name]
        if isinstance(item, dict):
            return DotableDict(item)
        if isinstance(item, list):
            return [DotableDict(value) if isinstance(value, dict) else value for value in item]
        return item

    def get(self, name: str) -> object:
        return self.__getattr__(name)

    def to_dict(self) -> dict[str, object]:
        return self._dictionary

    def keys(self):
        return self._dictionary.keys()


def evaluate_python(
    expression: str,
    global_namespace: dict[str, object],
    local_namespace: dict[str, object],
    *,
    diagnostic_expression: str | None = None,
) -> object:
    """Evaluate actual input while callers may name a synthesized expression safely."""
    diagnostic = "configured expression" if diagnostic_expression is None else diagnostic_expression

    def normalized_result(result: object, source: str) -> object:
        if isinstance(result, DotableDict):
            return result.to_dict()
        if isinstance(result, list):
            return [value.to_dict() if isinstance(value, DotableDict) else value for value in result]
        if callable(result) or isinstance(result, types.ModuleType):
            raise task_config_error(
                code=IssueCode.TASK_EXPRESSION_EVAL_FAILED,
                expr=diagnostic,
                error=f"'{source}' is an callable function, not a valid type (string, integer, float,...)",
            )
        if type(result) in NON_VALUE_TYPES:
            raise task_config_error(
                code=IssueCode.TASK_EXPRESSION_EVAL_FAILED,
                expr=diagnostic,
                error=f"'{source}' is {type(result).__name__} function, not a valid type (string, integer, float,...)",
            )
        return result

    try:
        return normalized_result(eval(expression, global_namespace, local_namespace), diagnostic)
    except (UserErrorBase, DomainError):
        raise
    except (NameError, AttributeError) as error:
        raise task_config_error(
            code=IssueCode.TASK_EXPRESSION_EVAL_FAILED,
            expr=diagnostic,
            error=f"{type(error).__name__}: {_SCOPE_GUIDANCE}",
        ) from error
    except KeyError as error:
        raise task_config_error(
            code=IssueCode.TASK_EXPRESSION_EVAL_FAILED,
            expr=diagnostic,
            error="KeyError: missing mapping key",
        ) from error
    except TypeError as error:
        raise task_config_error(
            code=IssueCode.TASK_EXPRESSION_EVAL_FAILED,
            expr=diagnostic,
            error=f"Failed while evaluate '{diagnostic}': '{diagnostic}' have undefined item or wrong structure",
        ) from error
    except SyntaxError as error:
        if ":" not in expression:
            raise task_config_error(
                code=IssueCode.TASK_EXPRESSION_EVAL_FAILED,
                expr=diagnostic,
                error=(
                    f"Evaluation error for expression '{diagnostic}': "
                    "The expression may contain undefined elements, formatting errors, "
                    "or unsupported parameter names. Ensure that boolean values and all parameter names "
                    "(e.g., 'True' vs 'true') adhere to the required formats."
                ),
            ) from error

        colon_replacement = "__"
        expression = expression.replace(r"\:", "__")

        def process_after_dot(match):
            return "." + re.sub(":", "__", match.group(1))

        expression = re.sub(r"\.(.*)", process_after_dot, expression)

        def replace_colons(values):
            updated = {}
            for key, value in values.items():
                if isinstance(value, dict):
                    value = replace_colons(value)
                if isinstance(value, DotableDict):
                    value = DotableDict(replace_colons(value.to_dict()))
                updated[key.replace(":", colon_replacement)] = value
            return updated

        try:
            return normalized_result(eval(expression, global_namespace, replace_colons(local_namespace)), diagnostic)
        except (UserErrorBase, DomainError):
            raise
        except Exception as retry_error:
            raise task_config_error(
                code=IssueCode.TASK_EXPRESSION_EVAL_FAILED,
                expr=diagnostic,
                error=(
                    f"Evaluation error for expression '{diagnostic}': "
                    "The expression may contain undefined items, improper structure, "
                    "or case-sensitive issues (e.g., using 'true' instead of 'True'). "
                    "Please double-check that all parameters and type notations are correct and supported."
                ),
            ) from retry_error
    except Exception as error:
        raise task_config_error(
            code=IssueCode.TASK_EXPRESSION_EVAL_FAILED,
            expr=diagnostic,
            error=type(error).__name__,
        ) from error


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


def evaluate_condition_value(context: ExpressionContext, element_name: str | None, value: str | None) -> bool:
    """Evaluate a DSL condition and reject non-boolean results."""
    condition = context.evaluate_python_expression(value) if value else True
    if isinstance(condition, bool):
        return condition
    raise condition_evaluation_error(
        code=IssueCode.CONDITION_NOT_BOOLEAN,
        condition="configured condition",
        element_label=f"element '{element_name}'",
        value=type(condition).__name__,
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
        return {key: evaluate_source_template(context, value, prefix, suffix) for key, value in data.items()}
    if isinstance(data, list):
        return _evaluate_list(context, data, prefix, suffix)
    if not isinstance(data, str) or not data.strip():
        return data
    if data.startswith("{") and data.endswith("}"):
        match = re.fullmatch(r"{(.*)}", data)
        return context.evaluate_python_expression(match.group(1)) if match is not None else None
    return interpolate_variables(context, data, prefix, suffix)


__all__ = [
    "DotableDict",
    "evaluate_condition_value",
    "evaluate_python",
    "evaluate_source_template",
    "interpolate_variables",
]
