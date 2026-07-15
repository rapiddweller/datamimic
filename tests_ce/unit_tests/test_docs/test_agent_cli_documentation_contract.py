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


def test_documentation_index_has_no_removed_authoring_archive() -> None:
    documentation_index = (_REPOSITORY_ROOT / "docs" / "README.md").read_text(
        encoding="utf-8"
    )

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

    weighted = _invoke_json(
        ["reference", "authoring", "--category", "field", "--kind", "weighted"]
    )
    assert isinstance(weighted, dict)
    assert weighted["query"] == {"category": "field", "kind": "weighted"}

    memstore_source = _invoke_json(
        ["reference", "authoring", "--category", "source", "--kind", "memstore"]
    )
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
