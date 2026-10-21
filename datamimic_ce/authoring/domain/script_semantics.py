"""Static semantics shared by authoring feedback about script fields.

This module deliberately recognises only authoring constructs that have an
unambiguous runtime meaning. It does not evaluate scripts.
"""

import ast
from dataclasses import dataclass
from enum import StrEnum

from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1, iter_dm_json_nodes
from datamimic_ce.engine.dsl.api import EL_EXECUTE


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


# Python libraries loaded by <execute> into a bounded run (#332). The check refuses what a library of
# functions, classes and constants does not need: imports outside the data modules, file or dynamic-code
# builtins, and under rngSeed imports inside a body, which the seeded rebinding cannot reach (#359). It is no
# sandbox: the bounded child process and its private workspace stay the isolation boundary, and deterministic
# replay proves what static rules cannot.

# Modules a library may import: the data modules expressions already know, plus DATAMIMIC domain types.
ADMITTED_IMPORT_ROOTS = frozenset(
    {
        "__future__",
        "abc",
        "base64",
        "calendar",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "enum",
        "faker",
        "functools",
        "hashlib",
        "itertools",
        "json",
        "logging",
        "math",
        "numpy",
        "pandas",
        "random",
        "re",
        "statistics",
        "string",
        "typing",
        "uuid",
    }
)
ADMITTED_PACKAGES = ("datamimic_ce.domains",)
# Referenced at all, not only called: an alias such as `write = open` or `__builtins__["open"]` reaches them too.
# Also a name the library imports itself (`from re import compile`): `del` or a failed import falls back to the
# builtin, so only the qualified form (`re.compile`) is admitted.
REFUSED_NAMES = frozenset(
    {"open", "exec", "eval", "compile", "__import__", "__builtins__", "globals", "locals", "vars"}
    # Attribute access by computed name; no corpus library uses it, and aliases defeat any narrower rule.
    | {"getattr", "setattr", "delattr"}
)
# Introspection that leads back to the builtins, the running code or the file loader, and the builtins
# themselves reached as attributes of the builtins module (print.__self__.open). compile stays: re.compile.
REFUSED_ATTRIBUTES = frozenset(
    {"__builtins__", "__globals__", "__code__", "__subclasses__", "__loader__", "__spec__", "__getattribute__"}
    | {"__self__", "__import__", "open", "exec", "eval"}
)



class LibraryRefusalReason(StrEnum):
    IMPORT_NOT_ADMITTED = "import_not_admitted"
    FILE_OR_DYNAMIC_CODE_BUILTIN = "file_or_dynamic_code_builtin"
    IMPORT_INSIDE_BODY_UNDER_SEED = "import_inside_body_under_seed"


@dataclass(frozen=True)
class LibraryRefusal:
    reason: LibraryRefusalReason
    line: int

    def message(self) -> str:
        """Static text: names the rule and the line, never source text or values."""
        match self.reason:
            case LibraryRefusalReason.IMPORT_NOT_ADMITTED:
                rule = "imports a module outside the bounded library modules"
            case LibraryRefusalReason.FILE_OR_DYNAMIC_CODE_BUILTIN:
                rule = "uses a file or dynamic-code builtin (open, exec, eval, compile, __import__, getattr, ...)"
            case LibraryRefusalReason.IMPORT_INSIDE_BODY_UNDER_SEED:
                rule = "imports inside a function or class body, which <setup rngSeed> cannot seed"
        return f"Python library line {self.line} {rule}"

    def remediation(self) -> str:
        match self.reason:
            case LibraryRefusalReason.IMPORT_NOT_ADMITTED:
                return "Import only data modules such as random, datetime, math or datamimic_ce.domains."
            case LibraryRefusalReason.FILE_OR_DYNAMIC_CODE_BUILTIN:
                return (
                    "Pass data in from the model instead of reading files or building code at runtime; "
                    "call a module function with a builtin's name qualified, such as re.compile."
                )
            case LibraryRefusalReason.IMPORT_INSIDE_BODY_UNDER_SEED:
                return "Move the import to module level, where seeded runs rebind it to the run's stream."


def requires_deterministic_replay(entry: DmJsonDocumentV1, steps: tuple[DmJsonDocumentV1, ...] = ()) -> bool:
    """A seeded model that loads Python anywhere in its include graph must replay: only a second run catches
    draws the seeded names miss. The entry's seed governs every included step."""
    return entry.root.properties.get("rng_seed") is not None and any(
        node.kind == EL_EXECUTE for document in (entry, *steps) for node, _ in iter_dm_json_nodes(document)
    )


def admits_python_library(language: str | None, *, target: str | None, script: str | None) -> bool:
    """Only Python from a file or inline text, without a client target or code computed by an expression."""
    return language == "python" and target is None and script is None


def _imported_modules(node: ast.Import | ast.ImportFrom) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    # A relative import has no module root to admit.
    return (node.module or "",) if node.level == 0 else ("",)


def _admitted(module: str) -> bool:
    return module.split(".")[0] in ADMITTED_IMPORT_ROOTS or any(
        module == package or module.startswith(package + ".") for package in ADMITTED_PACKAGES
    )


def python_library_refusal(source: str, *, seeded: bool) -> LibraryRefusal | None:
    """The earliest rule ``source`` breaks, or None. Unparseable source is left to the runtime's diagnostic."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    nested_imports = {
        id(inner)
        for body in ast.walk(tree)
        if isinstance(body, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        for inner in ast.walk(body)
        if isinstance(inner, (ast.Import, ast.ImportFrom))
    }
    refusals: list[LibraryRefusal] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if not all(_admitted(module) for module in _imported_modules(node)):
                refusals.append(LibraryRefusal(LibraryRefusalReason.IMPORT_NOT_ADMITTED, node.lineno))
            elif seeded and id(node) in nested_imports:
                refusals.append(LibraryRefusal(LibraryRefusalReason.IMPORT_INSIDE_BODY_UNDER_SEED, node.lineno))
        elif (
            (isinstance(node, ast.Name) and node.id in REFUSED_NAMES)
            or (isinstance(node, ast.Attribute) and node.attr in REFUSED_ATTRIBUTES)
            # module.__dict__["__builtins__"] and getattr(module, "__dict__")["__builtins__"]
            or (isinstance(node, ast.Constant) and node.value == "__builtins__")
        ):
            refusals.append(LibraryRefusal(LibraryRefusalReason.FILE_OR_DYNAMIC_CODE_BUILTIN, node.lineno))
    return min(refusals, key=lambda refusal: refusal.line) if refusals else None
