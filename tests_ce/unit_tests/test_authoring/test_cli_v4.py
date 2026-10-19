"""Typed Authoring CLI boundaries; runtime commands keep their existing owner."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.interfaces.cli import app

runner = CliRunner()


def test_authoring_has_its_own_command_tree_and_retires_root_scaffold() -> None:
    assert {group.name for group in app.registered_groups} >= {"authoring", "demo"}
    assert {command.name for command in app.registered_commands} == {"version", "info", "init", "run"}


def test_compile_stdin_returns_reviewable_xml_without_build_assurance() -> None:
    result = runner.invoke(app, ["authoring", "compile", "-"], input='{"root":{"kind":"setup"}}')
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["outcome"] == "ready"
    assert payload["artifact"]["compiled_xml"] == "<setup/>"
    assert "assurance" not in payload


def test_decompile_file_uses_the_same_typed_document(tmp_path: Path) -> None:
    source = tmp_path / "input.xml"
    source.write_text('<setup rngSeed="7"/>')
    result = runner.invoke(app, ["authoring", "decompile", str(source)])
    assert result.exit_code == 0, result.output
    document = json.loads(result.output)["document"]
    assert document["root"]["properties"]["rng_seed"] == 7
    assert source.read_text() == '<setup rngSeed="7"/>'


@pytest.mark.parametrize("source", ["", "{broken", "[]", '{"root":{"kind":"setup","extra":1}}'])
def test_invalid_compile_stdin_returns_one_rejected_json_document(source: str) -> None:
    result = runner.invoke(app, ["authoring", "compile", "-"], input=source)
    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["outcome"] == "rejected"
    assert payload["diagnostics"]


def test_missing_input_diagnostic_does_not_expose_host_path(tmp_path: Path) -> None:
    missing = tmp_path / "private-path.xml"
    result = runner.invoke(app, ["authoring", "decompile", str(missing)])
    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["outcome"] == "rejected"
    assert str(tmp_path) not in result.output


def test_schema_selects_the_running_build_contract() -> None:
    result = runner.invoke(app, ["authoring", "schema", "--name", "build_request_v4"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert "document" in payload["properties"]
    assert "spec" not in payload["properties"]
    assert payload["properties"]["version"]["const"] == "4.0"


def test_one_capability_has_a_structured_not_found_result() -> None:
    result = runner.invoke(app, ["authoring", "capability", "--domain", "element", "--name", "missing-element"])
    assert result.exit_code == 1, result.output
    assert json.loads(result.output)["error"] == "capability_not_found"


def test_reference_defaults_to_the_typed_overview() -> None:
    result = runner.invoke(app, ["authoring", "reference"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["topic"] == "overview"


def test_minimal_stdin_build_from_repository_does_not_copy_unrelated_files(monkeypatch) -> None:
    monkeypatch.chdir(Path(__file__).resolve().parents[3])
    request = {
        "document": {
            "root": {
                "kind": "setup",
                "properties": {"rng_seed": 7},
                "children": [
                    {
                        "kind": "generate",
                        "properties": {"name": "rows", "count": 2},
                        "children": [
                            {"kind": "key", "properties": {"name": "id", "generator": "IncrementGenerator"}},
                        ],
                    },
                ],
            }
        }
    }
    result = runner.invoke(app, ["authoring", "build", "-"], input=json.dumps(request))
    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout)["outcome"] == "ready"
