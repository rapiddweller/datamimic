"""Typed Authoring CLI boundaries; runtime commands keep their existing owner."""

import json
import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring.adapters.workspace import MAX_RESOURCE_BYTES
from datamimic_ce.authoring.domain.requests import PROJECT_ACCEPTANCE_PATH, PROJECT_ENTRY_PATH, ReadyBuild, RunResult
from datamimic_ce.interfaces.cli import app
from tests_ce.authoring_project import write_project

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
    result = runner.invoke(app, ["authoring", "schema", "--name", "build_request_v5"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert {"document", "descriptor_path", "spec"}.isdisjoint(payload["properties"])
    assert payload["properties"]["version"]["const"] == "5.0"


def test_one_capability_has_a_structured_not_found_result() -> None:
    result = runner.invoke(app, ["authoring", "capability", "--domain", "element", "--name", "missing-element"])
    assert result.exit_code == 1, result.output
    assert json.loads(result.output)["error"] == "capability_not_found"


def test_reference_defaults_to_the_typed_overview() -> None:
    result = runner.invoke(app, ["authoring", "reference"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["topic"] == "overview"


def test_minimal_project_build_does_not_copy_unrelated_files(tmp_path: Path) -> None:
    write_project(
        tmp_path,
        '<setup rngSeed="7"><generate name="rows" count="2">'
        '<key name="id" generator="IncrementGenerator"/></generate></setup>',
    )
    # A snapshot of the whole directory would refuse this file as over the per-file limit.
    with (tmp_path / "unrelated.bin").open("wb") as unrelated:
        unrelated.truncate(MAX_RESOURCE_BYTES + 1)
    result = runner.invoke(app, ["authoring", "build", str(tmp_path)])
    assert result.exit_code == 0, result.stdout
    ready = ReadyBuild.model_validate_json(result.stdout)
    assert {item.path for item in ready.artifact.files} == {PROJECT_ENTRY_PATH, PROJECT_ACCEPTANCE_PATH}


def test_count_free_source_json_preserves_required_nullable_capture(tmp_path: Path) -> None:
    (tmp_path / "db").mkdir()
    database = tmp_path / "db" / "database.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE items (id INTEGER)")
        connection.executemany("INSERT INTO items VALUES (?)", [(1,), (2,), (3,)])
    descriptor = tmp_path / "model.xml"
    descriptor.write_text(
        '<setup><database id="db" dbms="sqlite" database="database"/>'
        '<generate name="rows" source="db" selector="SELECT id FROM items" distribution="ordered"/></setup>',
        encoding="utf-8",
    )
    before = database.read_bytes()

    result = runner.invoke(app, ["authoring", "dry-run", str(descriptor), "--max-count", "2"])

    assert result.exit_code == 0, result.output
    response = RunResult.model_validate_json(result.stdout)
    assert response.ok
    (product,) = response.products
    assert product.rows == ({"id": 1}, {"id": 2})
    assert product.capture is not None
    assert product.capture.requested is None
    assert database.read_bytes() == before
