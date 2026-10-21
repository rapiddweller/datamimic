"""Keep portable Authoring contracts independent of Runtime key ownership."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTHORING = ROOT / "datamimic_ce" / "authoring"
RUNTIME_KEY_OWNER = "datamimic_ce.engine.runtime.pseudonymization"


def test_portable_authoring_modules_do_not_import_runtime_key_owner() -> None:
    files = [
        *sorted((AUTHORING / "application").rglob("*.py")),
        *sorted((AUTHORING / "domain").rglob("*.py")),
        AUTHORING / "ports.py",
    ]
    violations: dict[Path, set[str]] = {}
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        imports.update(
            node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module is not None
        )
        forbidden = {name for name in imports if name == RUNTIME_KEY_OWNER or name.startswith(f"{RUNTIME_KEY_OWNER}.")}
        if forbidden:
            violations[path] = forbidden

    assert not violations
