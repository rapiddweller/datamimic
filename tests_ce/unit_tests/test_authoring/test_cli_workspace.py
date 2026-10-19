"""File inputs keep their logical descriptor location within an explicit workspace."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.interfaces.cli import app


@pytest.mark.parametrize("command", ["dry-run", "run"])
@pytest.mark.parametrize("explicit_root", [False, True])
def test_nested_descriptor_reads_its_own_relative_source(tmp_path: Path, command: str, explicit_root: bool):
    nested = tmp_path / "nested"
    nested.mkdir()
    (tmp_path / "rows.csv").write_text("id\nROOT\n", encoding="utf-8")
    (nested / "rows.csv").write_text("id\nNESTED\n", encoding="utf-8")
    descriptor = nested / "model.xml"
    descriptor.write_text(
        '<setup rngSeed="7"><generate name="rows" source="rows.csv" distribution="ordered">'
        '<key name="id" script="this.id"/></generate></setup>',
        encoding="utf-8",
    )
    arguments = ["authoring", command, str(descriptor)]
    if explicit_root:
        arguments += ["--workspace-root", str(tmp_path)]
    response = CliRunner().invoke(app, arguments)
    assert response.exit_code == 0, response.stdout
    assert json.loads(response.stdout)["products"][0]["rows"] == [{"id": "NESTED"}]


@pytest.mark.parametrize("command", ["decompile", "lint", "dry-run", "run"])
def test_explicit_workspace_rejects_outside_descriptor(tmp_path: Path, command: str):
    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "outside.xml"
    outside.write_text(
        '<setup rngSeed="7"><generate name="rows" count="1"><key name="id" constant="1"/></generate></setup>',
        encoding="utf-8",
    )
    response = CliRunner().invoke(app, ["authoring", command, str(outside), "--workspace-root", str(root)])
    assert response.exit_code == 1, response.stdout
    result = json.loads(response.stdout)
    assert result.get("outcome") == "rejected" or result.get("ok") is False
    assert result["diagnostics"]
    assert str(tmp_path) not in response.stdout


def test_explicit_decompile_path_keeps_deliberate_logical_mapping(tmp_path: Path):
    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "outside.xml"
    outside.write_text(
        '<setup rngSeed="7"><generate name="rows" count="1"><key name="id" constant="1"/></generate></setup>',
        encoding="utf-8",
    )
    response = CliRunner().invoke(
        app,
        [
            "authoring",
            "decompile",
            str(outside),
            "--workspace-root",
            str(root),
            "--descriptor-path",
            "nested/model.xml",
        ],
    )
    assert response.exit_code == 0, response.stdout
    assert json.loads(response.stdout)["outcome"] == "ready"
