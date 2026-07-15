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
        script_path=ROOT / "datamimic_ce/mcp/cli.py",
        args=["--transport", "stdio"],
        python_cmd=sys.executable,
        cwd=str(ROOT),
        env={"PYTHONPATH": str(ROOT)},
    )
    async with Client(transport) as client:
        assert {tool.name for tool in await client.list_tools()} == {
            "datamimic_check",
            "datamimic_run",
            "datamimic_reference",
            "datamimic_scaffold",
        }
        result = await client.call_tool(
            "datamimic_reference",
            {"request": {"topic": "element", "name": "generate"}},
        )
        assert "pageSize" in json.loads(result[0].text)["content"]
