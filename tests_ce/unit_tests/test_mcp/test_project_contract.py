"""The project argument, the Build protocol and the result size guard of the MCP tools."""

import json
import os
from pathlib import Path

import pytest

fastmcp_client = pytest.importorskip("fastmcp.client")
Client = fastmcp_client.Client

import datamimic_ce.interfaces.mcp.server as mcp_server  # noqa: E402
from datamimic_ce.authoring.domain.requests import BUILD_PROTOCOL, BuildRequestV5, LintResult  # noqa: E402
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
    project = {"relative": ".", "missing": str(allowed / "none"), "outside": str(outside)}[kind]
    # Without a root restriction only the absolute-path rule can refuse the existing relative path ".".
    restriction = allowed if kind != "relative" else None
    async with Client(create_server(workspace_root=restriction)) as client:
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
async def test_each_call_gets_the_dotenv_of_its_own_project(
    anyio_backend: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[dict[str, str]] = []

    class RecordingApplication:
        def lint(self, request) -> LintResult:
            return LintResult(ok=True)

    def record(**kwargs) -> RecordingApplication:
        seen.append(dict(kwargs["environment"]))
        return RecordingApplication()

    monkeypatch.setattr(mcp_server, "create_authoring_application", record)
    monkeypatch.delenv("PROJECT_ONLY_VALUE", raising=False)
    first, second = tmp_path / "first", tmp_path / "second"
    for project, value in ((first, "one"), (second, "two")):
        project.mkdir()
        (project / ".env").write_text(f"PROJECT_ONLY_VALUE={value}\n", encoding="utf-8")
    async with Client(create_server()) as client:
        for project in (first, second, first):
            await client.call_tool("datamimic_lint", {"project": str(project), "request": {"xml": "<setup/>"}})
    assert [item["PROJECT_ONLY_VALUE"] for item in seen] == ["one", "two", "one"]
    assert "PROJECT_ONLY_VALUE" not in os.environ


def test_child_environment_adds_project_values_without_touching_this_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from datamimic_ce.authoring.adapters.bounded_executor import _child_environment

    monkeypatch.delenv("PROJECT_ONLY_VALUE", raising=False)
    assert _child_environment({}, None) is None
    child = _child_environment({"PROJECT_ONLY_VALUE": "1"}, 5)
    assert child is not None and child["PROJECT_ONLY_VALUE"] == "1" and child["PYTHONHASHSEED"] == "5"
    assert "PROJECT_ONLY_VALUE" not in os.environ


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


WIDE_XML = (
    '<setup rngSeed="7"><generate name="rows" count="50">'
    + "".join(f'<key name="k{index}" type="string" pattern="[a-z]{{60}}"/>' for index in range(30))
    + "</generate></setup>"
)


@pytest.mark.anyio
@pytest.mark.parametrize("tool", ["datamimic_dry_run", "datamimic_run"])
async def test_oversized_bounded_run_is_refused_with_its_hint(anyio_backend: str, tmp_path: Path, tool: str) -> None:
    async with Client(create_server()) as client:
        with pytest.raises(Exception, match="result_too_large") as raised:
            await client.call_tool(
                tool, {"project": str(tmp_path), "request": {"xml": WIDE_XML, "sample_rows": 50, "max_count": 50}}
            )
    assert "sample_rows" in str(raised.value)


@pytest.mark.anyio
async def test_every_tool_is_guarded(anyio_backend: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mcp_server, "MAX_RESULT_CHARACTERS", 2)
    project = str(tmp_path)
    calls = {
        "datamimic_version": {},
        "datamimic_schema": {},
        "datamimic_capabilities": {},
        "datamimic_capability": {"domain": "element", "name": "setup"},
        "datamimic_reference": {"request": {"topic": "overview"}},
        "datamimic_run_project": {"project": project},
        "datamimic_init": {"project": project},
        **{name: {"project": project, **arguments} for name, arguments in PROJECT_TOOLS.items()},
    }
    async with Client(create_server()) as client:
        names = {tool.name for tool in await client.list_tools()}
        assert names == set(calls)
        for name, arguments in calls.items():
            with pytest.raises(Exception, match="result_too_large"):
                await client.call_tool(name, arguments)
