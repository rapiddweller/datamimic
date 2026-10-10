"""Architecture gates for the public authoring transports."""

import ast
import json
from pathlib import Path

from pydantic import JsonValue

import datamimic_ce.authoring as authoring
from datamimic_ce.authoring.contracts import ProductResult, RunResult, ScaffoldResult
from datamimic_ce.interfaces.cli import app

ROOT = Path(__file__).parents[3]


def test_authoring_payload_permissions_keep_complete_sample_shapes() -> None:
    assert ProductResult.model_fields["sample"].annotation == list[dict[str, JsonValue]]
    assert RunResult.model_fields["products"].annotation == list[ProductResult]
    assert ScaffoldResult.model_fields["products"].annotation == list[ProductResult]

    contract = json.loads((ROOT / "architecture-contract.json").read_text(encoding="utf-8"))
    rule = next(rule for rule in contract["rules"] if rule["id"] == "AUTHORING-API-TYPES")
    assert rule["allowed_positions"] == [
        {
            "qualified_name": "datamimic_ce.authoring.api.run",
            "position": "return",
            "field_path": "products.sample",
            "annotation": "list[dict[str, JsonValue]]",
        },
        {
            "qualified_name": "datamimic_ce.authoring.api.scaffold",
            "position": "return",
            "field_path": "issues.repair.corrected_fragment",
            "annotation": "dict[str, JsonValue]",
        },
        {
            "qualified_name": "datamimic_ce.authoring.api.scaffold",
            "position": "return",
            "field_path": "products.sample",
            "annotation": "list[dict[str, JsonValue]]",
        },
        {
            "qualified_name": "datamimic_ce.authoring.api.scaffold",
            "position": "return",
            "field_path": "acceptance.results.observed_counts",
            "annotation": "dict[str, int] | None",
        },
    ]


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
    tree = ast.parse((ROOT / "datamimic_ce/interfaces/cli/_app.py").read_text(encoding="utf-8"))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    assert all(not function.name.startswith("_") for function in functions)
    assert all(any(isinstance(decorator, ast.Call) for decorator in function.decorator_list) for function in functions)


def test_transports_do_not_import_authoring_implementation_modules() -> None:
    forbidden = {
        "datamimic_ce.authoring.application.compiler",
        "datamimic_ce.authoring.adapters.dryrun",
        "datamimic_ce.authoring.adapters.linter",
        "datamimic_ce.authoring.adapters.reference",
        "datamimic_ce.authoring.projection.reference_projection",
    }
    for relative in (
        "datamimic_ce/interfaces/cli/__init__.py",
        "datamimic_ce/interfaces/cli/__main__.py",
        "datamimic_ce/interfaces/cli/_app.py",
        "datamimic_ce/interfaces/cli/authoring.py",
        "datamimic_ce/interfaces/mcp/__init__.py",
        "datamimic_ce/interfaces/mcp/cli.py",
        "datamimic_ce/interfaces/mcp/server.py",
    ):
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        imports = {
            node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        assert not imports & forbidden
