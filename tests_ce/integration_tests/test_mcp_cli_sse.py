"""Integration tests for the real MCP CLI over SSE.

WHY: Complements stdio tests by exercising the CLI in network mode, including
API key gating. Prints selected output so humans can verify behavior.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from typing import Iterable

import anyio
import pytest

fastmcp_client = pytest.importorskip(
    "fastmcp.client", reason="fastmcp extra required; install datamimic_ce[mcp]"
)
transports = pytest.importorskip(
    "fastmcp.client.transports", reason="fastmcp extra required; install datamimic_ce[mcp]"
)

Client = fastmcp_client.Client
SSETransport = transports.SSETransport

from datamimic_ce.mcp.models import GenerateArgs


def _free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_port_open(host: str, port: int, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise TimeoutError(f"Port {host}:{port} did not open in time")


def _spawn_cli_sse(port: int, env: dict[str, str] | None = None) -> subprocess.Popen:
    cmd = [
        sys.executable,
        "-m",
        "datamimic_ce.mcp.cli",
        "--transport",
        "sse",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--log-level",
        "warning",
    ]
    proc = subprocess.Popen(cmd, env={**os.environ, **(env or {})})
    _wait_port_open("127.0.0.1", port)
    return proc


def _kill(proc: subprocess.Popen) -> None:
    try:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    except Exception:
        pass


def _print_tools(tools: Iterable) -> None:  # pragma: no cover - print helper
    names = sorted([t.name for t in tools])
    print("SSE MCP tools:", names)


@pytest.fixture
def anyio_backend() -> str:  # pragma: no cover - fixture glue
    return "asyncio"


@pytest.mark.anyio
async def test_cli_sse_generate_roundtrip(anyio_backend) -> None:
    port = _free_tcp_port()
    proc = _spawn_cli_sse(port)
    try:
        async with Client(SSETransport(f"http://127.0.0.1:{port}/sse")) as client:
            tools = await client.list_tools()
            _print_tools(tools)

            # Also call the catalog tool and show basic stats for human verification
            catalog_raw = await client.call_tool("list_domains", {})
            catalog = json.loads(catalog_raw[0].text)
            print("Domains count:", len(catalog))
            if catalog:
                print("First domain entry:", json.dumps(catalog[0], sort_keys=True)[:240])

            args = GenerateArgs(domain="person", locale="en_US", seed=42)
            res = await client.call_tool("generate", {"args": args.model_dump(mode="python")})
            data = json.loads(res[0].text)
            assert data.get("items"), "Expected generated items from SSE CLI"
            print("Generated sample (seed=42):", json.dumps(data["items"][0], sort_keys=True)[:240])
            # Verify schema resource fetch via SSE transport
            res_schema = await client.read_resource("resource://datamimic/schemas/person/v1/request.json")
            assert res_schema and res_schema[0].text
            print("Schema snippet:", res_schema[0].text[:120])
    finally:
        _kill(proc)


@pytest.mark.anyio
async def test_cli_sse_requires_api_key_forbidden_without_header(anyio_backend) -> None:
    port = _free_tcp_port()
    proc = _spawn_cli_sse(port, env={"DATAMIMIC_MCP_API_KEY": "secret"})
    try:
        # Attempt without header should fail with HTTP 401
        with pytest.raises(Exception):
            async with Client(SSETransport(f"http://127.0.0.1:{port}/sse")) as client:
                await client.list_tools()

        # With Authorization header it should succeed
        headers = {"Authorization": "Bearer secret"}
        async with Client(SSETransport(f"http://127.0.0.1:{port}/sse", headers=headers)) as client:
            tools = await client.list_tools()
            _print_tools(tools)
            args = GenerateArgs(domain="person", seed=99)
            res = await client.call_tool("generate", {"args": args.model_dump(mode="python")})
            data = json.loads(res[0].text)
            assert data.get("items"), "Expected generated items with API key"
            print("Generated sample (seed=99, gated):", json.dumps(data["items"][0], sort_keys=True)[:240])
    finally:
        _kill(proc)
