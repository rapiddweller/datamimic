"""Static semantics shared by authoring feedback about script fields.

This module deliberately recognises only authoring constructs that have an
unambiguous runtime meaning. It does not evaluate scripts.
"""

import ast
from enum import StrEnum


class ScriptScope(StrEnum):
    """Named record scopes recognised by the authoring script contract."""

    CURRENT = "this"
    PARENT = "parent"


def scope_reference(scope: ScriptScope, field_name: str) -> str:
    """Return the canonical explicit reference to a field in ``scope``."""

    return f"{scope}.{field_name}"


def current_scope_reference(field_name: str) -> str:
    """Return the canonical explicit script reference for a current-scope field."""

    return scope_reference(ScriptScope.CURRENT, field_name)


def is_exact_scope_field_reference(script: str, scope: ScriptScope, field_name: str) -> bool:
    """Return whether a script is exactly one explicit reference to ``scope.field``.

    Foreign keys that carry a related record's actual key require an exact
    reference; arithmetic and other transforms can produce a different key.
    """

    try:
        expression = ast.parse(script, mode="eval")
    except SyntaxError:
        return False
    return (
        isinstance(expression.body, ast.Attribute)
        and expression.body.attr == field_name
        and isinstance(expression.body.value, ast.Name)
        and expression.body.value.id == scope
    )


def references_current_scope_field(script: str, field_name: str) -> bool:
    """Return whether a script reads ``field_name`` from its current record scope.

    DATAMIMIC accepts both the explicit ``this.field`` spelling and the bare
    ``field`` spelling in the current scope. Syntax validity remains the
    compiler/runtime's responsibility; unparsable expressions simply provide no
    static evidence of a source read.
    """

    try:
        expression = ast.parse(script, mode="eval")
    except SyntaxError:
        return False
    return any(
        (isinstance(node, ast.Name) and node.id == field_name)
        or (
            isinstance(node, ast.Attribute)
            and node.attr == field_name
            and isinstance(node.value, ast.Name)
            and node.value.id == ScriptScope.CURRENT
        )
        for node in ast.walk(expression)
    )
