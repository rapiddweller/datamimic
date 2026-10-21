"""Current authoring instructions remain executable through the public CLI."""

import json
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.interfaces.cli import app

ROOT = Path(__file__).resolve().parents[3]


def _projects(path: Path) -> list[tuple[str, dict]]:
    """Each documented project: an ``xml`` entry block followed by its ``json`` acceptance block."""
    text = path.read_text()
    entries = re.findall(r"```xml\n(.*?)```", text, re.DOTALL)
    acceptances = [json.loads(block) for block in re.findall(r"```json\n(.*?)```", text, re.DOTALL)]
    assert len(entries) == len(acceptances)
    return list(zip(entries, acceptances, strict=True))


def _build(project: tuple[str, dict], workspace: Path) -> dict:
    entry, acceptance = project
    (workspace / "datamimic.xml").write_text(entry, encoding="utf-8")
    (workspace / "acceptance").mkdir()
    (workspace / "acceptance" / "build.json").write_text(json.dumps(acceptance), encoding="utf-8")
    result = CliRunner().invoke(app, ["authoring", "build", str(workspace)])
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
    assert "schema --name build_request_v5" in content
    assert "acceptance/build.json" in content


def test_agents_md_embedded_project_builds_ready(tmp_path: Path) -> None:
    result = _build(_projects(ROOT / "AGENTS.md")[0], tmp_path)
    assert result["outcome"] == "ready", result
    assert result["evidence"][0]["count"] == 3


@pytest.mark.parametrize("index", range(3), ids=["nested_fk", "memstore_readback", "time_series"])
def test_documented_structural_projects_build_ready(index: int, tmp_path: Path) -> None:
    projects = _projects(ROOT / "docs/examples/authoring.md")
    assert len(projects) == 3
    result = _build(projects[index], tmp_path)
    assert result["outcome"] == "ready", result


def test_documented_random_fk_warning_holds(tmp_path: Path) -> None:
    entry, acceptance = _projects(ROOT / "docs/examples/authoring.md")[0]
    entry = entry.replace('name="parents" count="2"', 'name="parents" count="4"').replace(
        '<key name="parent_id" script="parent.id"/>', '<key name="parent_id" type="int" min="1" max="4"/>'
    )
    acceptance["expectations"][0]["count"] = 4
    result = _build((entry, acceptance), tmp_path)
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
    schema = runner.invoke(app, ["authoring", "schema", "--name", "build_request_v5"])
    assert schema.exit_code == 0, schema.stdout
    assert "expectations" in json.loads(schema.stdout)["properties"]
    element = runner.invoke(app, ["authoring", "capability", "--domain", "element", "--name", "generate"])
    assert element.exit_code == 0, element.stdout
    assert json.loads(element.stdout)["capability"]["name"] == "generate"
