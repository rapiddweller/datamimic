"""Static semantics shared by authoring feedback about script fields.

This module deliberately recognises only authoring constructs that have an
unambiguous runtime meaning. It does not evaluate scripts.
"""

import ast
from dataclasses import dataclass
from enum import StrEnum

from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1, iter_dm_json_nodes
from datamimic_ce.engine.dsl.api import EL_EXECUTE, ExportOperation, parse_consumer
from datamimic_ce.errors import GUIDANCE_LOOKUP_POINTER


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
                    "call a module function with a builtin's name qualified, such as re.compile. "
                    f"{GUIDANCE_LOOKUP_POINTER}"
                )
            case LibraryRefusalReason.IMPORT_INSIDE_BODY_UNDER_SEED:
                return "Move the import to module level, where seeded runs rebind it to the run's stream."


def names_statement_operation(target: str | None) -> bool:
    """Whether a ``target`` attribute names a source-free ``clear`` or ``drop`` (``db.clear``, ``mongo.drop()``)."""
    for part in parse_consumer(target):
        parsed = ExportOperation.from_target(part)
        if parsed is not None and parsed[1].is_statement_operation:
            return True
    return False


# Calls whose result does not depend on the order in which they read a set argument. sorted, min and max lose this
# with key=: ties keep the set order.
_ORDER_FREE_CALLS = frozenset({"sorted", "len", "min", "max", "sum", "any", "all", "bool", "set", "frozenset"})
_KEYED_CALLS = frozenset({"sorted", "min", "max"})
# Conversions that keep the set order; an order-free call around them stays order-free: len(list(set(x))).
_ORDER_KEEPING_CALLS = frozenset({"list", "tuple"})
_SET_PREDICATES = frozenset({"issubset", "issuperset", "isdisjoint"})
_DICT_VIEWS = frozenset({"keys", "items"})
_SET_OPERATORS = (ast.BitOr, ast.BitAnd, ast.Sub, ast.BitXor)
# Script attributes that hold one Python expression.
SCRIPT_PROPERTIES = ("script", "condition")


def _called_name(node: ast.AST | None) -> str | None:
    return node.func.id if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) else None


def _is_dict_view(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in _DICT_VIEWS
        and not node.args
    )


def _is_set(node: ast.AST) -> bool:
    if isinstance(node, ast.Set | ast.SetComp):
        return True
    if isinstance(node, ast.Call):
        return _called_name(node) in ("set", "frozenset")
    # d.keys() - e.keys() is a set too.
    return (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, _SET_OPERATORS)
        and any(_is_set(side) or _is_dict_view(side) for side in (node.left, node.right))
    )


def _has_fixed_order(node: ast.AST) -> bool:
    """A literal set of numbers iterates in the same order under every hash seed: a number hashes to its value."""
    elements: list[ast.expr] | None = None
    if isinstance(node, ast.Set):
        elements = node.elts
    elif (
        isinstance(node, ast.Call) and len(node.args) == 1 and isinstance(node.args[0], ast.List | ast.Tuple | ast.Set)
    ):
        elements = node.args[0].elts
    return elements is not None and all(
        isinstance(element, ast.Constant) and isinstance(element.value, int | float) for element in elements
    )


def _reads_order_free(node: ast.AST, parents: dict[int, ast.AST]) -> bool:
    parent = parents.get(id(node))
    while isinstance(parent, ast.Call) and _called_name(parent) in _ORDER_KEEPING_CALLS:
        node, parent = parent, parents.get(id(parent))
    if isinstance(parent, ast.Compare | ast.UnaryOp) or (isinstance(parent, ast.BinOp) and _is_set(parent)):
        return True
    if isinstance(parent, ast.IfExp) and parent.test is node:
        return True
    # {...}.issubset(x) and x.issubset({...}) give a bool.
    if isinstance(parent, ast.Attribute) and parent.attr in _SET_PREDICATES:
        return True
    if isinstance(parent, ast.Call) and isinstance(parent.func, ast.Attribute) and parent.func.attr in _SET_PREDICATES:
        return True
    name = _called_name(parent)
    return (
        isinstance(parent, ast.Call)
        and name in _ORDER_FREE_CALLS
        and node in parent.args
        and not (name in _KEYED_CALLS and any(keyword.arg == "key" for keyword in parent.keywords))
    )


def iterates_a_set(script: str) -> bool:
    """Whether a script reads a set in an order-dependent way (#425). The order of a set of strings follows the
    process hash seed, which rngSeed does not fix. Membership tests, comparisons, set predicates and order-free calls
    such as sorted(...) or len(...) are safe; a set that is iterated, converted or returned is not. This is a lint
    hint, not a proof: a set held in a name or returned by a helper is not seen. Build replays every
    seeded model under other hash seeds, which lowers the chance that such a miss stays hidden; it cannot remove it."""
    try:
        tree = ast.parse(script, mode="eval")
    except SyntaxError:
        return False
    parents = {id(child): node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    return any(
        _is_set(node) and not _has_fixed_order(node) and not _reads_order_free(node, parents) for node in ast.walk(tree)
    )


class ReplayCause(StrEnum):
    """What a seeded model contains that a replay is known to catch; the cause a failed replay names."""

    PYTHON_LIBRARY = "python_library"
    SET_ORDER = "set_order"
    OTHER = "other"

    def failure_message(self) -> str:
        """Static text for a replay that differed. It names a possible cause, because a model can have several, and
        never source text or values."""
        match self:
            case ReplayCause.PYTHON_LIBRARY:
                return (
                    "A seeded model that loads Python must replay identically, and this one did not. A possible "
                    "cause: a value drawn outside the seeded names, such as a module-level draw in the library."
                )
            case ReplayCause.SET_ORDER:
                return (
                    "A seeded model whose script iterates a set must replay identically, and this one did not. A "
                    "possible cause: the order of a set of strings changes with the process hash seed, which rngSeed "
                    "does not fix. Use sorted(...), a list or a tuple."
                )
            case ReplayCause.OTHER:
                return (
                    "A seeded model must replay identically, and this one did not. A possible cause: a set of strings "
                    "held in a name or returned by a helper, read in an order-dependent way. Its "
                    "order changes with the process hash seed, which rngSeed does not fix. Use sorted(...), a list or "
                    "a tuple."
                )


def replay_causes(entry: DmJsonDocumentV1, steps: tuple[DmJsonDocumentV1, ...] = ()) -> tuple[ReplayCause, ...]:
    """The causes a failed replay of a seeded model names, in a fixed order; OTHER when the model shows none, and
    empty for an unseeded model, which Build does not replay. The entry's seed governs every included step."""
    if entry.root.properties.get("rng_seed") is None:
        return ()
    nodes = [node for document in (entry, *steps) for node, _ in iter_dm_json_nodes(document)]
    causes = []
    if any(node.kind == EL_EXECUTE for node in nodes):
        causes.append(ReplayCause.PYTHON_LIBRARY)
    if any(
        isinstance(script := node.properties.get(name), str) and iterates_a_set(script)
        for node in nodes
        for name in SCRIPT_PROPERTIES
    ):
        causes.append(ReplayCause.SET_ORDER)
    return tuple(causes) or (ReplayCause.OTHER,)


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
