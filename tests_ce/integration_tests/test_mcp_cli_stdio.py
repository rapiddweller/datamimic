"""Real stdio transport coverage for the reduced MCP adapter."""

import json
import sys
from pathlib import Path

import pytest

fastmcp_client = pytest.importorskip("fastmcp.client")
transports = pytest.importorskip("fastmcp.client.transports")
Client = fastmcp_client.Client
PythonStdioTransport = transports.PythonStdioTransport
ROOT = Path(__file__).parents[2]


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_cli_stdio_authoring_roundtrip(anyio_backend: str) -> None:
    transport = PythonStdioTransport(
        script_path=ROOT / "datamimic_ce/interfaces/mcp/cli.py",
        args=["--transport", "stdio"],
        python_cmd=sys.executable,
        cwd=str(ROOT),
        env={"PYTHONPATH": str(ROOT)},
    )
    async with Client(transport) as client:
        assert {tool.name for tool in await client.list_tools()} == {
            "datamimic_version",
            "datamimic_schema",
            "datamimic_capabilities",
            "datamimic_capability",
            "datamimic_compile",
            "datamimic_decompile",
            "datamimic_build",
            "datamimic_lint",
            "datamimic_dry_run",
            "datamimic_run",
            "datamimic_reference",
        }
        result = await client.call_tool(
            "datamimic_reference",
            {"request": {"topic": "overview"}},
        )
        assert json.loads(result[0].text)["topic"] == "overview"


@pytest.mark.anyio
async def test_cli_stdio_explicit_workspace_reads_project_instead_of_launcher(tmp_path: Path) -> None:
    project = tmp_path / "project with spaces"
    launcher = tmp_path / "launcher"
    project.mkdir()
    launcher.mkdir()
    (project / "rows.csv").write_text("id\nPROJECT\n", encoding="utf-8")
    (launcher / "rows.csv").write_text("id\nLAUNCHER\n", encoding="utf-8")
    transport = PythonStdioTransport(
        script_path=ROOT / "datamimic_ce/interfaces/mcp/cli.py",
        args=["--transport", "stdio", "--workspace-root", str(project)],
        python_cmd=sys.executable,
        cwd=str(launcher),
        env={"PYTHONPATH": str(ROOT)},
    )
    async with Client(transport) as client:
        result = await client.call_tool(
            "datamimic_dry_run",
            {
                "request": {
                    "xml": '<setup rngSeed="7"><generate name="rows" source="rows.csv" distribution="ordered"/></setup>'
                }
            },
        )
        payload = json.loads(result[0].text)
        assert payload["ok"], payload
        assert payload["products"][0]["rows"] == [{"id": "PROJECT"}]
