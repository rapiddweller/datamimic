# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Public authoring diagnostics retain one identity and structured repair details."""

import json
from pathlib import Path, PurePosixPath

import pytest
from fastmcp.client import Client
from typer.testing import CliRunner

from datamimic_ce.authoring.adapters.validator import CeDescriptorValidator
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH
from datamimic_ce.interfaces.cli import app
from datamimic_ce.interfaces.mcp.server import create_server
from tests_ce.authoring_project import write_project

_ROW = '<generate name="rows" count="1"/>'
_BAD_ROW = '<generate name="rows" count="1"><key name="value" script="1 / 0"/></generate>'
_ENTROPY = '<setup rngSeed="7"><execute type="python" uri="leaky.scr.py"/>' + _ROW + "</setup>"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("command", "xml", "code", "rule", "severity"),
    [
        ("lint", '<setup><generate count="1"/></setup>', "I605", "DM104", "error"),
        ("lint", f"<setup>{_ROW}</setup>", "validation", "DM303", "info"),
        ("build", f"<setup>{_BAD_ROW}</setup>", "I832", None, "error"),
        ("build", '<setup><include uri="outer.xml"/></setup>', "I832", None, "error"),
        ("dry-run", "<setup/>", "not_executed", None, "error"),
        ("dry-run", _ENTROPY, "W008", None, "warning"),
    ],
    ids=["catalog-rule", "uncatalogued-rule", "runtime-build", "included-step", "uncatalogued", "warning"],
)
async def test_cli_and_mcp_project_the_same_envelope(
    tmp_path: Path, command: str, xml: str, code: str, rule: str | None, severity: str
) -> None:
    write_project(tmp_path, xml)
    (tmp_path / "outer.xml").write_text('<setup><include uri="inner.xml"/></setup>', encoding="utf-8")
    (tmp_path / "inner.xml").write_text(f"<setup>\n{_BAD_ROW}\n</setup>", encoding="utf-8")
    (tmp_path / "leaky.scr.py").write_text("import random\nvalue = random.random()\n", encoding="utf-8")
    arguments = {"project": str(tmp_path)}
    if command != "build":
        arguments["xml"] = xml
    if command == "dry-run":
        arguments["descriptor_path"] = "datamimic.xml"
    cli_input = tmp_path if command == "build" else tmp_path / "datamimic.xml"
    cli = CliRunner().invoke(app, ["authoring", command, str(cli_input)])
    assert cli.exit_code == (1 if severity == "error" else 0), cli.stdout

    async with Client(create_server(descriptor_path=PROJECT_ENTRY_PATH)) as client:
        mcp = await client.call_tool(f"datamimic_{command.replace('-', '_')}", arguments)
    cli_items = json.loads(cli.stdout)["diagnostics"]
    mcp_items = json.loads(mcp.content[0].text)["diagnostics"]
    assert cli_items == mcp_items
    [item] = [item for item in cli_items if (item["code"], item["rule"]) == (code, rule)]
    assert item["severity"] == severity
    assert "ce_error" not in item
    assert "Caused by" not in item["message"]
    assert f"/{code}]" not in item["message"]
    if rule == "DM104":
        assert item["location"]["attribute"] == "name"
        assert sum(other["code"] == code for other in cli_items) == 1
    if "outer.xml" in xml:
        assert item["location"]["file"] == "inner.xml"
        assert item["location"]["line"] == 2
        assert item["location"]["include_chain"] == ["datamimic.xml", "outer.xml"]
    elif code == "W008":
        assert item["location"]["script_file"] == "leaky.scr.py"
        assert item["location"]["script_line"] == 2
        assert "line 2" not in item["message"]
    if item["location"] and item["location"]["file"]:
        assert item["location"]["file"] not in item["message"]


def test_live_schema_exposes_the_rule_and_catalog_code() -> None:
    result = CliRunner().invoke(app, ["authoring", "schema", "--name", "build_result"])
    assert result.exit_code == 0, result.stdout
    definitions = json.loads(result.stdout)["$defs"]
    fields = definitions["Diagnostic"]["properties"]
    assert "ce_error" not in fields
    assert fields["rule"]["anyOf"][0]["pattern"] == r"^DM[0-9]{3}$"
    assert {"I605", "W008"} <= set(definitions["IssueCode"]["enum"])


def test_include_graph_keeps_the_nested_entry_path(tmp_path: Path) -> None:
    xml = '<setup>\n<include uri="missing.xml"/>\n</setup>'
    logical_path = PurePosixPath("models/main.xml")
    (tmp_path / "models").mkdir()
    workspace = AuthoringWorkspaceContext(tmp_path, logical_path)
    validator = CeDescriptorValidator(workspace, profile_loader=workspace.load_connection_profile)
    [item] = validator.include_graph(xml).diagnostics
    assert item.code == "I201"
    assert item.location is not None
    assert item.location.file == "models/main.xml"
    assert item.location.line == 2


def test_cli_compile_keeps_a_json_syntax_position_out_of_the_message() -> None:
    result = CliRunner().invoke(app, ["authoring", "compile", "-"], input="{\ninvalid")
    assert result.exit_code == 1, result.stdout
    [item] = json.loads(result.stdout)["diagnostics"]
    assert (item["code"], item["rule"]) == ("validation", None)
    assert item["message"] == "Input is not valid JSON."
    assert (item["location"]["line"], item["location"]["column"]) == (2, 1)
