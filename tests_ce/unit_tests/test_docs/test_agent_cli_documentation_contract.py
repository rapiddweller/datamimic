# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.

"""Fast executable guards for the agent-facing README command contract."""

import json
import re
from pathlib import Path

from typer.testing import CliRunner

from datamimic_ce.cli import app

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")


def _invoke_json(arguments: list[str], *, stdin: str | None = None) -> object:
    result = CliRunner().invoke(app, arguments, input=stdin)
    assert result.exit_code == 0, result.stdout
    return json.loads(result.stdout)


def test_agent_facing_readme_relative_links_resolve() -> None:
    readmes = (_REPOSITORY_ROOT / "README.md",)
    missing: list[str] = []
    for readme in readmes:
        for target in _MARKDOWN_LINK.findall(readme.read_text(encoding="utf-8")):
            path, _, _ = target.partition("#")
            if path and "://" not in path and not path.startswith("#"):
                resolved = readme.parent / path
                if not resolved.exists():
                    missing.append(f"{readme.relative_to(_REPOSITORY_ROOT)} -> {target}")

    assert missing == []


def test_agents_md_points_to_scaffold_for_the_full_intent_schema() -> None:
    agents_md = (_REPOSITORY_ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "datamimic reference scaffold" in agents_md


def _scaffold_json(spec: dict) -> dict:
    result = CliRunner().invoke(app, ["scaffold", "-", "--format", "json"], input=json.dumps(spec))
    payload = json.loads(result.stdout)
    assert isinstance(payload, dict)
    return payload


def test_agents_md_embedded_worked_example_scaffolds_verified() -> None:
    """The minimal model.dm.json embedded in AGENTS.md is a live contract, not prose."""
    agents_md = (_REPOSITORY_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```json\n(.*?)```", agents_md, re.DOTALL)
    assert blocks, "AGENTS.md lost its embedded worked example"
    spec = json.loads(blocks[0])

    scaffold = _scaffold_json(spec)
    assert scaffold["ok"] is True
    assert scaffold["verified"] is True


def test_agents_md_structural_recipes_scaffold_verified() -> None:
    """The three structural recipes documented in AGENTS.md stay executable.

    Nested parent-child FK via script parent.<field> + foreign_key role; memstore
    pipeline with the identifier/foreign_key role pair; time_series with window
    and series_count. If the engine changes any of these contracts, this gate
    fails before the documentation silently rots.
    """
    nested_fk = {
        "version": "1",
        "seed": 7,
        "products": [
            {
                "kind": "generated",
                "name": "customers",
                "count": 2,
                "fields": [{"kind": "increment", "name": "id"}],
                "children": [
                    {
                        "name": "orders",
                        "count": 2,
                        "fields": [
                            {
                                "kind": "script",
                                "name": "customer_id",
                                "script": "parent.id",
                                "roles": [
                                    {"kind": "foreign_key", "parent_product": "customers", "parent_field": "id"}
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
        "expectations": [
            {"kind": "per_parent_count", "parent_product": "customers", "child_product": "orders", "count": 2}
        ],
    }
    memstore_pipeline = {
        "version": "1",
        "seed": 7,
        "products": [
            {
                "kind": "generated",
                "name": "users",
                "count": 2,
                "fields": [{"kind": "increment", "name": "id", "roles": [{"kind": "identifier"}]}],
                "targets": [{"kind": "memstore", "id": "store"}],
            },
            {
                "kind": "source",
                "name": "user_audit",
                "source": {"kind": "memstore", "id": "store", "product": "users"},
                "fields": [
                    {
                        "kind": "script",
                        "name": "id",
                        "script": "this.id",
                        "roles": [{"kind": "foreign_key", "parent_product": "users", "parent_field": "id"}],
                    }
                ],
            },
        ],
    }
    time_series = {
        "version": "1",
        "seed": 7,
        "products": [
            {
                "kind": "time_series",
                "name": "readings",
                "series_count": 2,
                "window": {"start": "2026-01-01T00:00:00", "end": "2026-01-01T03:00:00", "interval": "PT1H"},
                "fields": [{"kind": "values", "name": "sensor", "values": ["temp", "humidity"]}],
            }
        ],
        "expectations": [{"kind": "exact_count", "product": "readings", "count": 6}],
    }

    recipes = (("nested_fk", nested_fk), ("memstore_pipeline", memstore_pipeline), ("time_series", time_series))
    for name, spec in recipes:
        scaffold = _scaffold_json(spec)
        assert scaffold["ok"] is True, f"{name}: {scaffold.get('issues')}{scaffold.get('diagnostics')}"
        assert scaffold["verified"] is True, f"{name}: {scaffold.get('acceptance')}"


def test_agents_md_random_fk_recipe_warning_holds() -> None:
    """AGENTS.md warns a randomly generated FK passes schema validation but fails
    per-parent-count acceptance. Gate the warning itself."""
    random_fk = {
        "version": "1",
        "seed": 7,
        "products": [
            {
                "kind": "generated",
                "name": "customers",
                "count": 4,
                "fields": [{"kind": "increment", "name": "id"}],
                "children": [
                    {
                        "name": "orders",
                        "count": 2,
                        "fields": [
                            {
                                "kind": "int_range",
                                "name": "customer_id",
                                "minimum": 1,
                                "maximum": 4,
                                "roles": [
                                    {"kind": "foreign_key", "parent_product": "customers", "parent_field": "id"}
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
        "expectations": [
            {"kind": "per_parent_count", "parent_product": "customers", "child_product": "orders", "count": 2}
        ],
    }

    scaffold = _scaffold_json(random_fk)
    assert scaffold["ok"] is True, "the documented trap is a semantic failure, not a schema rejection"
    assert scaffold["verified"] is False, (
        "AGENTS.md claims a random FK fails per-parent-count acceptance; "
        "if this now verifies, update the recipe section"
    )


def test_documentation_index_has_no_removed_authoring_archive() -> None:
    documentation_index = (_REPOSITORY_ROOT / "docs" / "README.md").read_text(encoding="utf-8")

    assert "Authoring evaluation archive" not in documentation_index
    assert "benchmarks/dsl-authoring" not in documentation_index
    assert "measures how reliably agents author" not in documentation_index


def test_agent_cli_discovery_and_scaffold_contract() -> None:
    capabilities = _invoke_json(["capabilities"])
    assert isinstance(capabilities, dict)
    assert capabilities["elements"]

    authoring = _invoke_json(["reference", "authoring"])
    assert isinstance(authoring, dict)
    assert authoring["queries"]

    weighted = _invoke_json(["reference", "authoring", "--category", "field", "--kind", "weighted"])
    assert isinstance(weighted, dict)
    assert weighted["query"] == {"category": "field", "kind": "weighted"}

    memstore_source = _invoke_json(["reference", "authoring", "--category", "source", "--kind", "memstore"])
    assert isinstance(memstore_source, dict)
    assert memstore_source["query"] == {
        "category": "source",
        "kind": "memstore",
    }
    assert memstore_source["model"] == "MemstoreSource"
    assert "product" in memstore_source["allowed_fields"]
    assert "fragment" not in memstore_source
    assert memstore_source["json_schema"]["title"] == "MemstoreSource"

    spec = {
        "version": "1",
        "seed": 42,
        "products": [
            {
                "kind": "generated",
                "name": "records",
                "count": 1,
                "fields": [{"kind": "increment", "name": "record_id"}],
            }
        ],
    }
    scaffold = _invoke_json(
        ["scaffold", "-", "--format", "json"],
        stdin=json.dumps(spec),
    )
    assert isinstance(scaffold, dict)
    assert scaffold["ok"] is True
    assert scaffold["verified"] is True
