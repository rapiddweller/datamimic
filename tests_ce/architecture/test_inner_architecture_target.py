"""Acceptance checks for the approved physical CE core layout."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from tests_ce.architecture.test_recursive_target_definition import (
    MANIFEST,
    _current_files,
    _files_at,
    _physical_target_issues,
    _target_files,
    _target_implementation_issues,
)

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "datamimic_ce"

CONCRETE_IO_EXPORTS = {"DatabaseClient", "MongoDBClient", "RdbmsClient"}


def test_current_filesystem_matches_the_frozen_target_map() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = _files_at(manifest["source_commit"])
    excluded = {path for path in source if any(path.startswith(item["prefix"]) for item in manifest["exclusions"])}
    targets = _target_files(source - excluded, manifest)
    current = {
        path
        for path in _current_files()
        if not any(path.startswith(item["prefix"]) for item in manifest["exclusions"])
    }

    assert not _physical_target_issues(current, targets)
    assert not _target_implementation_issues(targets, PACKAGE, manifest["source_commit"])


def test_runtime_tasks_do_not_depend_on_concrete_io_clients_through_facades() -> None:
    runtime = PACKAGE / "engine/runtime"
    task_roots = [runtime / "tasks"]
    offenders: list[str] = []

    for task_root in task_roots:
        if not task_root.is_dir():
            continue
        for path in task_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if ".engine.io.clients" in node.module:
                        offenders.append(f"{path.relative_to(ROOT)}:{node.lineno} imports {node.module}")
                    if node.module.endswith("engine.io.api"):
                        names = {alias.name for alias in node.names}
                        concrete = names & CONCRETE_IO_EXPORTS
                        if concrete:
                            offenders.append(f"{path.relative_to(ROOT)}:{node.lineno} imports {sorted(concrete)}")
                if isinstance(node, ast.Import):
                    client_modules = [
                        alias.name
                        for alias in node.names
                        if ".engine.io.clients." in alias.name
                    ]
                    if client_modules:
                        offenders.append(f"{path.relative_to(ROOT)}:{node.lineno} imports {client_modules}")

    assert not offenders, "runtime orchestration must use IO-owned operations, not clients: " + "; ".join(offenders)


def test_io_api_does_not_reexport_concrete_clients() -> None:
    api_path = PACKAGE / "engine/io/api.py"
    tree = ast.parse(api_path.read_text(encoding="utf-8"), filename=str(api_path))
    exports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module and ".engine.io.clients." in node.module
        for alias in node.names
    }

    concrete_exports = exports & CONCRETE_IO_EXPORTS
    assert not concrete_exports, f"io.api exposes concrete clients: {sorted(concrete_exports)}"
