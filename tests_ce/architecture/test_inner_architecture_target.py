"""Acceptance checks for the approved physical CE core layout."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "datamimic_ce"

TARGET_FILES = (
    "authoring/api.py",
    "authoring/contracts.py",
    "authoring/spec.py",
    "errors/base.py",
    "errors/factory.py",
    "errors/formatters.py",
    "engine/dsl/api.py",
    "engine/dsl/contracts.py",
    "engine/io/api.py",
    "engine/io/contracts.py",
    "engine/runtime/api.py",
    "engine/runtime/contracts.py",
    "engine/runtime/logging.py",
)

TARGET_DIRECTORIES = (
    "authoring/domain",
    "authoring/application",
    "authoring/adapters",
    "authoring/projection",
    "errors/catalog",
    "domains/domain_core",
    "domains/shared/models",
    "domains/shared/services",
    "domains/shared/generators",
    "domains/shared/literal_generators",
    "domains/shared/converters",
    "domains/finance",
    "domains/healthcare",
    "domains/insurance",
    "domains/ecommerce",
    "domains/public_sector",
    "engine/dsl/constants",
    "engine/dsl/enums",
    "engine/dsl/model",
    "engine/dsl/parsers",
    "engine/dsl/statements",
    "engine/io/clients",
    "engine/io/connection_config",
    "engine/io/data_sources",
    "engine/io/exporters",
    "engine/runtime/contexts",
    "engine/runtime/storage",
    "engine/runtime/lifecycle",
    "engine/runtime/scripting",
    "engine/runtime/tasks/generate/workers",
    "engine/runtime/tasks/generate/services/policies",
    "interfaces/cli",
)

CONCRETE_IO_EXPORTS = {"DatabaseClient", "MongoDBClient", "RdbmsClient"}


def _has_python_code(directory: Path) -> bool:
    for module in directory.rglob("*.py"):
        body = ast.parse(module.read_text(encoding="utf-8"), filename=str(module)).body
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(
            body[0].value.value, str
        ):
            body = body[1:]
        if any(not isinstance(statement, ast.Pass) for statement in body):
            return True
    return False


def test_empty_package_check_allows_a_real_initializer(tmp_path: Path) -> None:
    package = tmp_path / "package"
    package.mkdir()
    initializer = package / "__init__.py"
    initializer.write_text('"""Placeholder only."""\npass\n', encoding="utf-8")

    assert not _has_python_code(package)

    initializer.write_text('"""Package facade."""\nfrom .api import run\n', encoding="utf-8")
    assert _has_python_code(package)


def test_core_packages_follow_the_physical_target() -> None:
    missing_files = [path for path in TARGET_FILES if not (PACKAGE / path).is_file()]
    missing_directories = [path for path in TARGET_DIRECTORIES if not (PACKAGE / path).is_dir()]
    empty_directories = [
        path
        for path in TARGET_DIRECTORIES
        if (PACKAGE / path).is_dir() and not _has_python_code(PACKAGE / path)
    ]
    actual_engine_roots = {
        path.name
        for path in (PACKAGE / "engine").iterdir()
        if path.is_dir() and (path / "__init__.py").is_file()
    }

    issues = []
    if missing_files:
        issues.append(f"missing target modules: {missing_files}")
    if missing_directories:
        issues.append(f"missing target packages: {missing_directories}")
    if empty_directories:
        issues.append(f"empty target packages: {empty_directories}")
    if (PACKAGE / "domains/common").exists() or (PACKAGE / "domains/common.py").exists():
        issues.append("domains.common must be removed, with no compatibility shim")
    if actual_engine_roots != {"dsl", "io", "runtime"}:
        issues.append(f"unexpected engine packages: {sorted(actual_engine_roots)}")

    assert not issues, "; ".join(issues)


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
