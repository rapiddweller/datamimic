"""Static semantics shared by authoring feedback about script fields.

This module deliberately recognises only authoring constructs that have an
unambiguous runtime meaning. It does not evaluate scripts.
"""

import ast


def current_scope_reference(field_name: str) -> str:
    """Return the canonical explicit script reference for a current-scope field."""

    return f"this.{field_name}"


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
            and node.value.id == "this"
        )
        for node in ast.walk(expression)
    )
