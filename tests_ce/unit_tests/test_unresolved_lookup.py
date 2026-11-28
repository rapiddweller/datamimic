# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""is_unresolved_lookup reads the traceback of evaluate_python's wrapped error. Each test pins one fact it relies on,
so a change to the evaluator's structure fails here, not in a descriptor that silently stops waiting for a row."""

import pytest

from datamimic_ce.engine.runtime.scripting import evaluation
from datamimic_ce.engine.runtime.scripting.evaluation import DotableDict, evaluate_python, is_unresolved_lookup
from datamimic_ce.errors import TaskConfigError


def _wrapped(expression: str, **names: object) -> TaskConfigError:
    with pytest.raises(TaskConfigError) as raised:
        evaluate_python(expression, {}, names)
    return raised.value


def _raises(kind: str) -> object:
    if kind == "attribute":
        return DotableDict({}).missing_attribute
    if kind == "name":
        return missing_name  # type: ignore[name-defined]  # noqa: F821
    if kind == "key":
        return {}["missing_key"]
    return 1 + "a"  # type: ignore[operator]


class _Constructed:
    def __init__(self, kind: str, *_unused: object):
        _raises(kind)


@pytest.mark.parametrize(
    ("expression", "names"),
    [
        ("missing_name", {}),
        ("row.missing", {"row": DotableDict({})}),
        ("row['missing']", {"row": DotableDict({})}),
        ("int(row.missing)", {"row": DotableDict({})}),
        ("row.ns:missing", {"row": DotableDict({})}),  # the colon-rewrite fallback
        ("row.ns:missing + 1", {"row": DotableDict({"other": 1})}),
    ],
    ids=["name", "row_attribute", "row_key", "inside_a_builtin_call", "colon_rewrite", "colon_rewrite_expression"],
)
def test_a_lookup_the_expression_cannot_resolve_is_unresolved(expression: str, names: dict[str, object]) -> None:
    assert is_unresolved_lookup(_wrapped(expression, **names))


@pytest.mark.parametrize("kind", ["attribute", "name", "key", "type"])
def test_a_failure_inside_a_called_function_is_not_unresolved(kind: str) -> None:
    assert not is_unresolved_lookup(_wrapped(f"build('{kind}')", build=_raises))


@pytest.mark.parametrize("kind", ["attribute", "name", "key", "type"])
def test_a_failure_inside_a_constructor_is_not_unresolved(kind: str) -> None:
    assert not is_unresolved_lookup(_wrapped(f"Constructed('{kind}')", Constructed=_Constructed))


@pytest.mark.parametrize("kind", ["attribute", "name", "key"])
def test_a_failure_inside_a_constructor_is_not_unresolved_on_the_colon_fallback(kind: str) -> None:
    names = {"Constructed": _Constructed, "row": DotableDict({"ns:value": 1})}
    assert not is_unresolved_lookup(_wrapped(f"Constructed('{kind}', row.ns:value)", **names))


def test_an_error_without_an_expression_cause_is_not_unresolved() -> None:
    assert not is_unresolved_lookup(TaskConfigError("plain"))
    assert not is_unresolved_lookup(_wrapped("1 + 'a'"))


def test_every_expression_is_compiled_under_the_expression_file_name() -> None:
    assert evaluation._compile("1").co_filename == evaluation._EXPRESSION_FILE
    assert evaluation._compiled("1").co_filename == evaluation._EXPRESSION_FILE
