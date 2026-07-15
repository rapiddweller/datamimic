"""Architecture gates for the public authoring transports."""

import ast
from pathlib import Path

import datamimic_ce.authoring as authoring
from datamimic_ce.authoring.contracts import ScaffoldResult
from datamimic_ce.cli import app

ROOT = Path(__file__).parents[3]


def test_authoring_exports_only_the_deliberate_canonical_api() -> None:
    assert authoring.__all__ == [
        "AuthoringSpecV1",
        "ScaffoldRequest",
        "ScaffoldResult",
        "authoring_spec_json_schema",
        "scaffold",
    ]


def test_scaffold_render_errors_have_one_structured_owner() -> None:
    assert "issues" in ScaffoldResult.model_fields
    assert "error" not in ScaffoldResult.model_fields


def test_cli_has_exact_command_surface() -> None:
    assert {command.name for command in app.registered_commands} == {
        "version",
        "info",
        "capabilities",
        "reference",
        "scaffold",
        "lint",
        "dry-run",
        "init",
        "run",
    }


def test_cli_entry_module_contains_no_private_or_non_command_functions() -> None:
    tree = ast.parse((ROOT / "datamimic_ce/cli.py").read_text(encoding="utf-8"))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    assert all(not function.name.startswith("_") for function in functions)
    assert all(any(isinstance(decorator, ast.Call) for decorator in function.decorator_list) for function in functions)


def test_transports_do_not_import_authoring_implementation_modules() -> None:
    forbidden = {
        "datamimic_ce.authoring.compiler",
        "datamimic_ce.authoring.dryrun",
        "datamimic_ce.authoring.linter",
        "datamimic_ce.authoring.reference",
        "datamimic_ce.authoring.reference_projection",
    }
    for relative in ("datamimic_ce/cli.py", "datamimic_ce/cli_authoring.py", "datamimic_ce/mcp/server.py"):
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        imports = {
            node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        assert not imports & forbidden
