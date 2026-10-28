"""Evaluate expressions embedded in source values."""

from __future__ import annotations

import ast
import re
import types
from collections.abc import Iterable, Iterator, KeysView, Mapping
from functools import lru_cache
from typing import Protocol, TypeGuard

from datamimic_ce.engine.dsl.api import ATTR_WHERE, EL_GENERATE
from datamimic_ce.engine.runtime.scripting.expression_globals import (
    NON_VALUE_TYPES,
    SCRIPT_BUILTINS,
    UNOFFERED_BUILTINS,
    row_expression_globals,
)
from datamimic_ce.errors import (
    DescriptorLocation,
    DomainError,
    IssueCode,
    UserErrorBase,
    condition_evaluation_error,
    task_config_error,
)

_SCOPE_GUIDANCE = (
    "check spelling, definition order and value shape; current-scope names can resolve bare, "
    "but existing outermost bare names win collisions; intermediate ancestor names need qualification; "
    "use this.name for the current scope, parent.name for the immediate enclosing record, "
    "or root.name for an outermost field when these aliases are available, or use a qualified scope path"
)


class ExpressionContext(Protocol):
    def evaluate_python_expression(
        self, expr: str, local_namespace: dict[str, object] | None = None, *, text_from_data: bool = False
    ) -> object: ...


class DotableDict:
    """Expose dictionary fields through dot and mapping access while evaluating expressions."""

    def __init__(self, dictionary: dict[str, object]):
        self._dictionary = dictionary

    # WHY: not a Mapping subclass; inheriting would add items()/values() methods that shadow
    # rows with fields of those names. Registered as a virtual Mapping below instead.
    def __getitem__(self, key: str) -> object:
        item = self._dictionary[key]
        if isinstance(item, dict):
            return DotableDict(item)
        if isinstance(item, list):
            return [DotableDict(value) if isinstance(value, dict) else value for value in item]
        return item

    def __getattr__(self, name: str) -> object:
        try:
            return self[name]
        except KeyError as error:
            raise AttributeError(f"Cannot find attribute '{name}'", name=name) from error

    def __iter__(self) -> Iterator[str]:
        return iter(self._dictionary)

    def __len__(self) -> int:
        return len(self._dictionary)

    def __contains__(self, key: str) -> bool:
        return key in self._dictionary

    def get(self, key: str, default: object = None) -> object:
        try:
            return self[key]
        except KeyError:
            return default

    def to_dict(self) -> dict[str, object]:
        """A copy: a script that changes it must not change the stored row, such as a memstore row (#421). Item access
        wraps each nested row, and _plain unwraps it through this method again, so every row level is rebuilt; other
        values stay shared, as in EE."""
        return {key: _plain(self[key]) for key in self._dictionary}

    def keys(self) -> KeysView[str]:
        return self._dictionary.keys()


Mapping.register(DotableDict)


def _plain(value: object) -> object:
    """Export nested rows as plain dicts so `dict(row)` never leaks a DotableDict.

    A dict that holds no row keeps its identity, and a dict subclass (defaultdict, Counter) stays what it is:
    only exact dicts and lists are rebuilt.
    """
    if isinstance(value, DotableDict):
        value = value.to_dict()
    if type(value) is dict:
        plain = {key: _plain(value[key]) for key in value}
        for key in value:
            if plain[key] is not value[key]:
                return plain
        return value
    if type(value) is list:
        return [_plain(item) for item in value]
    return value


def _written_nodes(expression: str) -> tuple[ast.AST, ...]:
    """The syntax nodes written in the expression: descriptor structure, never a value."""
    try:
        return tuple(ast.walk(ast.parse(expression.lstrip(" \t"), mode="eval")))
    except SyntaxError:
        return ()


def _names_read(nodes: tuple[ast.AST, ...], name: str) -> bool:
    return any(isinstance(node, ast.Name) and node.id == name for node in nodes)


def _lookup_failure(error: NameError | AttributeError, nodes: tuple[ast.AST, ...]) -> str:
    """Name the missing name only when the expression text holds it: a called function can raise a name built
    from data, and a diagnostic never shows a value."""
    written = {node.id for node in nodes if isinstance(node, ast.Name)}
    written |= {node.attr for node in nodes if isinstance(node, ast.Attribute)}
    if error.name not in written:
        return type(error).__name__
    if isinstance(error, NameError):
        return f"NameError: name '{error.name}' is not defined"
    return f"AttributeError: no attribute '{error.name}'"


def _replaced_engine_names(
    names: Iterable[str], global_namespace: dict[str, object], local_namespace: dict[str, object]
) -> str:
    """A library import such as `from datetime import datetime` replaces the engine's `datetime` in expressions,
    as in Python and in EE. When such an expression fails, say which of the given names are not the engine's."""
    replaced = sorted(
        name
        for name in set(names)
        if name in global_namespace and name in local_namespace and local_namespace[name] is not global_namespace[name]
    )
    return "".join(
        f"; the expression reads '{name}', which a script, variable or field binds in place of the engine's "
        f"'{name}': import it under another name or rename the field"
        for name in replaced
    )


def _compile(expression: str) -> types.CodeType:
    # eval() of a string drops leading spaces and tabs; compile() does not, so drop them here (script=" a + b").
    return compile(expression.lstrip(" \t"), "<expression>", "eval")


# As in EE: the same expression text runs once per row, so compile it once.
@lru_cache(maxsize=8192)
def _compiled(expression: str) -> types.CodeType:
    return _compile(expression)


def evaluate_python(
    expression: str,
    global_namespace: dict[str, object],
    local_namespace: dict[str, object],
    *,
    diagnostic_expression: str | None = None,
    text_from_data: bool = False,
) -> object:
    """Evaluate actual input while callers may name a synthesized expression safely. An expression read from source
    data (``text_from_data``) is a value, so its error names nothing that it holds."""
    diagnostic = "configured expression" if diagnostic_expression is None else diagnostic_expression
    shown = "" if text_from_data else expression

    def normalized_result(result: object, source: str) -> object:
        result = _plain(result)
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

    def single_namespace(names: dict[str, object]) -> dict[str, object]:
        """One dict as globals: a comprehension, generator expression or lambda sees only globals, so with
        separate locals it would not see the record (#423). Local names win, as at the top level."""
        namespace = {**global_namespace, **names}
        if "__builtins__" in names:  # a local never chose the builtins, so a field of that name must not either
            del namespace["__builtins__"]
            if "__builtins__" in global_namespace:
                namespace["__builtins__"] = global_namespace["__builtins__"]
        return namespace

    # Data text is a new value on each row: a cache would only keep every distinct text alive.
    try:
        code = _compile(expression) if text_from_data else _compiled(expression)
        return normalized_result(eval(code, single_namespace(local_namespace)), diagnostic)
    except (UserErrorBase, DomainError):
        raise
    except (NameError, AttributeError) as error:
        nodes = _written_nodes(shown)
        # Only a name the expression text holds is shown; a builtin name is no descriptor value.
        if isinstance(error, NameError) and error.name in UNOFFERED_BUILTINS and _names_read(nodes, error.name):
            raise task_config_error(
                code=IssueCode.TASK_EXPRESSION_BUILTIN_UNAVAILABLE,
                expr=diagnostic,
                builtin=error.name,
                offered=", ".join(SCRIPT_BUILTINS),
            ) from error
        # A missing name is never the replaced name, and only `replaced.missing` blames the replacement.
        receivers = (
            []
            if isinstance(error, NameError)
            else [
                node.value.id
                for node in nodes
                if isinstance(node, ast.Attribute) and node.attr == error.name and isinstance(node.value, ast.Name)
            ]
        )
        raise task_config_error(
            code=IssueCode.TASK_EXPRESSION_EVAL_FAILED,
            expr=diagnostic,
            error=(
                f"{_lookup_failure(error, nodes)}: {_SCOPE_GUIDANCE}"
                f"{_replaced_engine_names(receivers, global_namespace, local_namespace)}"
            ),
        ) from error
    except KeyError as error:
        raise task_config_error(
            code=IssueCode.TASK_EXPRESSION_EVAL_FAILED,
            expr=diagnostic,
            error="KeyError: missing mapping key",
        ) from error
    except TypeError as error:
        read = (node.id for node in _written_nodes(shown) if isinstance(node, ast.Name))
        raise task_config_error(
            code=IssueCode.TASK_EXPRESSION_EVAL_FAILED,
            expr=diagnostic,
            error=(
                f"Failed while evaluate '{diagnostic}': '{diagnostic}' have undefined item or wrong structure"
                f"{_replaced_engine_names(read, global_namespace, local_namespace)}"
            ),
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
            return normalized_result(eval(expression, single_namespace(replace_colons(local_namespace))), diagnostic)
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


def interpolate_variables(
    context: ExpressionContext, expression: str, prefix: str, suffix: str, *, text_from_data: bool = False
) -> str:
    """Replace configured variable markers with values from the current context."""
    pattern = rf"{re.escape(prefix)}([^{re.escape(prefix)}]\S*?){re.escape(suffix)}"
    if re.search(pattern, expression) is None:
        return expression
    return re.sub(
        pattern,
        lambda match: str(context.evaluate_python_expression(match.group(1), text_from_data=text_from_data)),
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


class WhereCondition:
    """The where= condition of one file-source statement. It reads one row (bare columns and ``this``) and the row
    globals, never parent., variables or setup names, so every process and every pass keep the same rows."""

    def __init__(self, where: str, stmt_name: str) -> None:
        self._where = where
        self._stmt_name = stmt_name
        self._globals = row_expression_globals()
        self._location = DescriptorLocation(EL_GENERATE, attribute=ATTR_WHERE)

    def __call__(self, row: Mapping[str, object]) -> bool:
        names = dict(row)
        for key, value in names.items():
            if isinstance(value, dict):
                names[key] = DotableDict(value)
        names.setdefault("this", DotableDict(dict(row)))
        try:
            result = evaluate_python(self._where, self._globals, names, diagnostic_expression=ATTR_WHERE)
        except UserErrorBase as error:
            if error.location is None:
                error.location = self._location
            raise
        if isinstance(result, bool):
            return result
        raise condition_evaluation_error(
            code=IssueCode.CONDITION_NOT_BOOLEAN,
            condition=ATTR_WHERE,
            element_label=f"<generate> '{self._stmt_name}'",
            value=type(result).__name__,
            location=self._location,
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
        return context.evaluate_python_expression(match.group(1), text_from_data=True) if match is not None else None
    return interpolate_variables(context, data, prefix, suffix, text_from_data=True)


__all__ = [
    "DotableDict",
    "WhereCondition",
    "evaluate_condition_value",
    "evaluate_python",
    "evaluate_source_template",
    "interpolate_variables",
]
