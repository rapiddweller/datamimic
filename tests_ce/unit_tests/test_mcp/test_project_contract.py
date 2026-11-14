"""The project argument, the Build protocol and the result size guard of the MCP tools."""

import json
import os
from pathlib import Path

import pytest

fastmcp_client = pytest.importorskip("fastmcp.client")
Client = fastmcp_client.Client

import datamimic_ce.interfaces.mcp.server as mcp_server  # noqa: E402
from datamimic_ce.authoring.domain.requests import BUILD_PROTOCOL, BuildRequestV5  # noqa: E402
from datamimic_ce.interfaces.mcp.server import create_server  # noqa: E402
from tests_ce.authoring_project import write_project  # noqa: E402

XML = (
    '<setup rngSeed="7"><generate name="rows" count="2">'
    '<key name="id" generator="IncrementGenerator"/></generate></setup>'
)
REQUEST = {"request": {"xml": XML}}
PROJECT_TOOLS = {
    "datamimic_build": {},
    "datamimic_lint": REQUEST,
    "datamimic_dry_run": REQUEST,
    "datamimic_run": REQUEST,
    "datamimic_compile": {"request": {"document": {"root": {"kind": "setup"}}}},
    "datamimic_decompile": REQUEST,
}


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_build_protocol_matches_the_acceptance_contract() -> None:
    assert BuildRequestV5().version == BUILD_PROTOCOL == "5.0"


def test_cli_version_reports_build_protocol() -> None:
    from typer.testing import CliRunner

    from datamimic_ce.interfaces.cli import app

    result = CliRunner().invoke(app, ["authoring", "version"])
    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout)["build_protocol"] == BUILD_PROTOCOL


@pytest.mark.anyio
async def test_every_project_tool_requires_the_project_argument(anyio_backend: str) -> None:
    async with Client(create_server()) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
    for name in PROJECT_TOOLS:
        assert "project" in tools[name].inputSchema["required"], name
    for name in ("datamimic_version", "datamimic_schema", "datamimic_capabilities", "datamimic_reference"):
        assert "project" not in tools[name].inputSchema.get("properties", {}), name
    assert tools["datamimic_capabilities"].inputSchema.get("properties", {}) == {}


@pytest.mark.anyio
@pytest.mark.parametrize("tool", sorted(PROJECT_TOOLS))
@pytest.mark.parametrize("kind", ["relative", "missing", "outside"])
async def test_unusable_project_is_an_input_diagnostic_not_a_tool_error(
    anyio_backend: str, tmp_path: Path, tool: str, kind: str
) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    project = {"relative": "shop", "missing": str(allowed / "none"), "outside": str(outside)}[kind]
    async with Client(create_server(workspace_root=allowed)) as client:
        response = await client.call_tool(tool, {"project": project, **PROJECT_TOOLS[tool]})
    payload = json.loads(response[0].text)
    diagnostics = payload["diagnostics"]
    assert diagnostics[0]["code"] == "input", payload
    assert str(tmp_path) not in response[0].text


@pytest.mark.anyio
async def test_project_inside_the_workspace_root_is_accepted(anyio_backend: str, tmp_path: Path) -> None:
    project = tmp_path / "shop"
    project.mkdir()
    write_project(project, XML)
    async with Client(create_server(workspace_root=tmp_path)) as client:
        response = await client.call_tool("datamimic_build", {"project": str(project)})
    assert json.loads(response[0].text)["outcome"] == "ready"


@pytest.mark.anyio
async def test_project_dotenv_is_loaded_not_the_server_working_directory(
    anyio_backend: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("PROJECT_ONLY_VALUE", raising=False)
    (tmp_path / ".env").write_text("PROJECT_ONLY_VALUE=1\n", encoding="utf-8")
    write_project(tmp_path, XML)
    async with Client(create_server()) as client:
        await client.call_tool("datamimic_build", {"project": str(tmp_path)})
    assert os.environ.get("PROJECT_ONLY_VALUE") == "1"
    monkeypatch.delenv("PROJECT_ONLY_VALUE")


@pytest.mark.anyio
async def test_oversized_result_names_the_narrowing_argument(
    anyio_backend: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(mcp_server, "MAX_RESULT_CHARACTERS", 100)
    async with Client(create_server()) as client:
        with pytest.raises(Exception, match="result_too_large") as raised:
            await client.call_tool("datamimic_capabilities", {})
    message = str(raised.value)
    assert '"size"' in message and "datamimic_capability" in message


@pytest.mark.anyio
async def test_argument_free_tools_stay_under_the_size_limit(anyio_backend: str, tmp_path: Path) -> None:
    write_project(tmp_path, XML)
    async with Client(create_server()) as client:
        for name, arguments in (
            ("datamimic_version", {}),
            ("datamimic_schema", {"name": "build_request_v5"}),
            ("datamimic_capabilities", {}),
            ("datamimic_reference", {"request": {"topic": "overview"}}),
            ("datamimic_build", {"project": str(tmp_path)}),
        ):
            response = await client.call_tool(name, arguments)
            assert len(response[0].text) <= mcp_server.MAX_RESULT_CHARACTERS, name


@pytest.mark.anyio
async def test_document_schema_over_the_limit_names_smaller_schemas(anyio_backend: str) -> None:
    async with Client(create_server()) as client:
        with pytest.raises(Exception, match="result_too_large") as raised:
            await client.call_tool("datamimic_schema", {})
    assert "build_request_v5" in str(raised.value)
