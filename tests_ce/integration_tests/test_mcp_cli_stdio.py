"""Integration test: spawn the real MCP CLI in stdio mode and call tools.

WHY: Ensures our tests exercise the actual CLI process and FastMCP wiring
without mocks. Uses stdio transport so no network is required.
"""

from __future__ import annotations

import json
import sys

import anyio
import pytest

fastmcp_client = pytest.importorskip(
    "fastmcp.client", reason="fastmcp extra required; install datamimic_ce[mcp]"
)
transports = pytest.importorskip(
    "fastmcp.client.transports", reason="fastmcp extra required; install datamimic_ce[mcp]"
)

Client = fastmcp_client.Client
PythonStdioTransport = transports.PythonStdioTransport

from datamimic_ce.mcp.models import GenerateArgs
from datamimic_ce.domains.determinism import canonical_json, hash_bytes


@pytest.fixture
def anyio_backend() -> str:  # pragma: no cover - fixture glue
    return "asyncio"


@pytest.mark.anyio
async def test_cli_stdio_generate_roundtrip() -> None:
    # Spawn the real CLI as a subprocess with stdio transport
    transport = PythonStdioTransport(
        script_path="datamimic_ce/mcp/cli.py",
        args=["--transport", "stdio"],
        python_cmd=sys.executable,
    )

    async with Client(transport) as client:
        # Discover tools
        tools = await client.list_tools()
        tool_names = {t.name for t in tools}
        assert {"list_domains", "generate"}.issubset(tool_names)
        # Show tool list for human verification in -s runs
        print("MCP tools:", sorted(tool_names))
        # Also show domain catalog size and first entry
        catalog_raw = await client.call_tool("list_domains", {})
        catalog = json.loads(catalog_raw[0].text)
        print("Domains count:", len(catalog))
        if catalog:
            print("First domain entry:", json.dumps(catalog[0], sort_keys=True)[:240])

        # Call generate with deterministic args and assert result shape
        args = GenerateArgs(domain="person", locale="en_US", seed=7)
        payload = args.model_dump(mode="python")
        result = await client.call_tool("generate", {"args": payload})
        assert result, "No content from generate tool"
        text = result[0].text
        assert text and text.strip(), "Empty text payload from generate tool"
        data = json.loads(text)
        assert isinstance(data.get("items"), list) and data["items"], "Expected non-empty generated items"
        # Show a snippet of the generated item for human verification in -s runs
        sample = data["items"][0]
        print("Generated sample (seed=7):", json.dumps(sample, sort_keys=True)[:240])
        # Determinism is covered in unit/e2e tests; stdio path validated for roundtrip.
        # Also verify schema resource fetch via stdio transport
        res = await client.read_resource("resource://datamimic/schemas/person/v1/request.json")
        assert res and res[0].text
        print("Schema snippet:", res[0].text[:120])
