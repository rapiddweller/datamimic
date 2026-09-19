"""Text I/O encoding gate.

AST-walks the CE production tree and fails on any text-mode file or
subprocess I/O that relies on the platform default encoding (cp1252 on
Windows, UTF-8 on Linux/macOS). Such calls make every supported source
and target format (CSV, JSON, XML, TXT, FCW, properties, scripts, ...)
read or write different bytes per platform.

Forbidden without an explicit, non-``None`` ``encoding=`` argument:

* ``open(path)`` / ``open(path, "r"|"w"|"a"|...)``
* ``path.open(...)`` in text mode
* ``path.read_text()`` / ``path.write_text(data)``
* ``subprocess.run/Popen/...(..., text=True)``, also when imported via
  ``from subprocess import run``

Binary mode (``"rb"``, ``"wb"``, ...) is exempt: it bypasses Python's
platform text encoding, and format-specific parsers (e.g. the XML prolog)
handle encoding where applicable. Encoding values come from the existing
SPOTs: the exporter's ``self.encoding`` or ``SetupContext.default_encoding``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PROD_ROOT = Path(__file__).resolve().parents[2] / "datamimic_ce"

TEXT_IO_METHODS = {"read_text", "write_text"}
SUBPROCESS_FUNCS = {"run", "Popen", "check_output", "call", "check_call"}


def _mode(node: ast.Call, positional_index: int) -> str | None:
    """Literal mode string of an open() call, or None if not a literal."""
    for kw in node.keywords:
        if kw.arg == "mode":
            return kw.value.value if isinstance(kw.value, ast.Constant) else None
    if len(node.args) > positional_index:
        arg = node.args[positional_index]
        return arg.value if isinstance(arg, ast.Constant) and isinstance(arg.value, str) else None
    return "r"


def _has_explicit_encoding(node: ast.Call) -> bool:
    """``encoding=None`` falls back to the platform default, so it does not count."""
    return any(
        kw.arg == "encoding" and not (isinstance(kw.value, ast.Constant) and kw.value.value is None)
        for kw in node.keywords
    )


def _subprocess_names(tree: ast.AST) -> set[str]:
    """Names bound by ``from subprocess import run, Popen as P``."""
    return {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "subprocess"
        for alias in node.names
        if alias.name in SUBPROCESS_FUNCS
    }


def _is_subprocess_call(func: ast.expr, imported: set[str]) -> bool:
    if isinstance(func, ast.Name):
        return func.id in imported
    return (
        isinstance(func, ast.Attribute)
        and func.attr in SUBPROCESS_FUNCS
        and isinstance(func.value, ast.Name)
        and func.value.id == "subprocess"
    )


def _collect_callsites(tree: ast.AST) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    imported_subprocess = _subprocess_names(tree)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or _has_explicit_encoding(node):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "open":
            mode = _mode(node, 1)
            if mode is None or "b" not in mode:
                hits.append((node.lineno, "open(...)"))
        elif (
            isinstance(func, ast.Attribute)
            and func.attr == "open"
            and not (isinstance(func.value, ast.Name) and func.value.id == "os")
        ):
            mode = _mode(node, 0)
            if mode is None or "b" not in mode:
                hits.append((node.lineno, ".open(...)"))
        elif isinstance(func, ast.Attribute) and func.attr in TEXT_IO_METHODS:
            hits.append((node.lineno, f".{func.attr}(...)"))
        elif _is_subprocess_call(func, imported_subprocess) and any(
            kw.arg in {"text", "universal_newlines"} for kw in node.keywords
        ):
            hits.append((node.lineno, "subprocess call with text=True"))
    return hits


def _production_modules() -> list[Path]:
    skip_segments = {"demos", "__pycache__"}
    return sorted(p for p in PROD_ROOT.rglob("*.py") if not any(seg in p.parts for seg in skip_segments))


@pytest.mark.parametrize("module_path", _production_modules(), ids=lambda p: str(p.relative_to(PROD_ROOT.parent)))
def test_text_io_declares_encoding(module_path: Path) -> None:
    rel = str(module_path.relative_to(PROD_ROOT.parent))
    hits = _collect_callsites(ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path)))
    if not hits:
        return
    formatted = "\n".join(f"  {rel}:{lineno}  {expr}" for lineno, expr in hits)
    pytest.fail(
        f"Platform-default encoding in {rel}:\n{formatted}\n\n"
        f"Pass encoding= explicitly: the exporter's self.encoding, ctx.root.default_encoding, "
        f'or "utf-8" where no context exists. Binary mode ("rb"/"wb") is exempt.'
    )
