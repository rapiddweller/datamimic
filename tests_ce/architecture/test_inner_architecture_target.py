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
CLIENTS_PACKAGE = "datamimic_ce.engine.io.clients"


def _is_clients_module(module: str) -> bool:
    return module == CLIENTS_PACKAGE or module.startswith(CLIENTS_PACKAGE + ".")


def _task_client_imports(task_root: Path) -> list[str]:
    offenders: list[str] = []
    for path in task_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if _is_clients_module(node.module):
                    offenders.append(f"{path}:{node.lineno} imports {node.module}")
                if node.module == "datamimic_ce.engine.io" and any(alias.name == "clients" for alias in node.names):
                    offenders.append(f"{path}:{node.lineno} imports clients")
                if node.module == "datamimic_ce.engine.io.api":
                    concrete = {alias.name for alias in node.names} & CONCRETE_IO_EXPORTS
                    if concrete:
                        offenders.append(f"{path}:{node.lineno} imports {sorted(concrete)}")
            if isinstance(node, ast.Import):
                clients = [
                    alias.name
                    for alias in node.names
                    if _is_clients_module(alias.name)
                ]
                if clients:
                    offenders.append(f"{path}:{node.lineno} imports {clients}")
    return offenders


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
    offenders = _task_client_imports(PACKAGE / "engine/runtime/tasks")
    assert not offenders, "runtime orchestration must use IO-owned operations, not clients: " + "; ".join(offenders)


def test_runtime_task_client_import_check_catches_nested_fixture(tmp_path: Path) -> None:
    task_root = tmp_path / "tasks"
    nested = task_root / "nested"
    nested.mkdir(parents=True)
    (nested / "accidental.py").write_text(
        "from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient\n",
        encoding="utf-8",
    )
    (nested / "package_import.py").write_text(
        "import datamimic_ce.engine.io.clients\n",
        encoding="utf-8",
    )
    (nested / "reexport.py").write_text(
        "from datamimic_ce.engine.io import clients\n",
        encoding="utf-8",
    )
    (nested / "similarly_named.py").write_text(
        "import datamimic_ce.engine.io.clients_extra\n",
        encoding="utf-8",
    )

    offenders = _task_client_imports(task_root)
    assert len(offenders) == 3, offenders
    assert not any("clients_extra" in offender for offender in offenders)


def _concrete_client_exports(source: str) -> set[str]:
    return {
        alias.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom) and node.module and _is_clients_module(node.module)
        for alias in node.names
    } & CONCRETE_IO_EXPORTS


def test_io_api_does_not_reexport_concrete_clients() -> None:
    api_path = PACKAGE / "engine/io/api.py"
    concrete_exports = _concrete_client_exports(api_path.read_text(encoding="utf-8"))
    assert _concrete_client_exports("from datamimic_ce.engine.io.clients import RdbmsClient") == {"RdbmsClient"}
    assert not _concrete_client_exports("from datamimic_ce.engine.io.clients_extra import RdbmsClient")

    assert not concrete_exports, f"io.api exposes concrete clients: {sorted(concrete_exports)}"
