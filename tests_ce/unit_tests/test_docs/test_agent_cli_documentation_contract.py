"""Current authoring instructions remain executable through the public CLI."""

import json
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.interfaces.cli import app

ROOT = Path(__file__).resolve().parents[3]


def _json_blocks(path: Path) -> list[dict]:
    return [json.loads(block) for block in re.findall(r"```json\n(.*?)```", path.read_text(), re.DOTALL)]


def _build(request: dict, workspace: Path) -> dict:
    result = CliRunner().invoke(
        app, ["authoring", "build", "-", "--workspace-root", str(workspace)], input=json.dumps(request)
    )
    payload = json.loads(result.stdout)
    assert result.exit_code == (0 if payload["outcome"] == "ready" else 1), result.stdout
    return payload


def test_agent_facing_readme_relative_links_resolve() -> None:
    readme = ROOT / "README.md"
    missing = []
    for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", readme.read_text()):
        path = target.partition("#")[0]
        if path and "://" not in path and not path.startswith("#") and not (readme.parent / path).exists():
            missing.append(target)
    assert missing == []


def test_agents_md_points_to_the_running_document_and_build_schemas() -> None:
    content = (ROOT / "AGENTS.md").read_text()
    assert "datamimic authoring schema" in content
    assert "schema --name build_request_v4" in content
    assert "artifact.compiled_xml" in content


def test_agents_md_embedded_transaction_builds_ready(tmp_path: Path) -> None:
    request = _json_blocks(ROOT / "AGENTS.md")[0]
    result = _build(request, tmp_path)
    assert result["outcome"] == "ready", result
    assert result["evidence"][0]["count"] == 3


@pytest.mark.parametrize("index", range(3), ids=["nested_fk", "memstore_readback", "time_series"])
def test_documented_structural_transactions_build_ready(index: int, tmp_path: Path) -> None:
    requests = _json_blocks(ROOT / "docs/examples/authoring.md")
    assert len(requests) == 3
    result = _build(requests[index], tmp_path)
    assert result["outcome"] == "ready", result


def test_documented_random_fk_warning_holds(tmp_path: Path) -> None:
    request = _json_blocks(ROOT / "docs/examples/authoring.md")[0]
    parents = request["document"]["root"]["children"][0]
    parents["properties"]["count"] = 4
    request["expectations"][0]["count"] = 4
    child_fk = parents["children"][1]["children"][0]
    child_fk["properties"] = {"name": "parent_id", "type": "int", "min": 1, "max": 4}
    result = _build(request, tmp_path)
    assert result["outcome"] == "rejected", "Random FK membership must not establish per-parent correctness."
    assert result["phase"] == "expectation", result
    assert result["diagnostics"][0]["path"] == ["product_roles", 1]


def test_documentation_index_does_not_teach_historical_benchmark_commands() -> None:
    index = (ROOT / "docs/README.md").read_text()
    assert "benchmarks/dsl-authoring" not in index


def test_agent_cli_discovery_uses_the_same_public_contract() -> None:
    runner = CliRunner()
    capabilities = runner.invoke(app, ["authoring", "capabilities"])
    assert capabilities.exit_code == 0, capabilities.stdout
    assert "generate" in json.loads(capabilities.stdout)["element"]
    schema = runner.invoke(app, ["authoring", "schema", "--name", "build_request_v4"])
    assert schema.exit_code == 0, schema.stdout
    assert "document" in json.loads(schema.stdout)["properties"]
    element = runner.invoke(app, ["authoring", "capability", "--domain", "element", "--name", "generate"])
    assert element.exit_code == 0, element.stdout
    assert json.loads(element.stdout)["capability"]["name"] == "generate"
