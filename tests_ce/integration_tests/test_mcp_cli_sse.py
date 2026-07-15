"""Real SSE transport and API-key coverage for the reduced MCP adapter."""

import os
import socket
import subprocess
import sys
import time

import pytest

fastmcp_client = pytest.importorskip("fastmcp.client")
transports = pytest.importorskip("fastmcp.client.transports")
Client = fastmcp_client.Client
SSETransport = transports.SSETransport


def free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.bind(("127.0.0.1", 0))
        return connection.getsockname()[1]


def spawn_server(port: int, api_key: str | None = None) -> subprocess.Popen[bytes]:
    environment = dict(os.environ)
    if api_key:
        environment["DATAMIMIC_MCP_API_KEY"] = api_key
    process = subprocess.Popen(
        [
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
        ],
        env=environment,
    )
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return process
        except OSError:
            time.sleep(0.05)
    process.terminate()
    raise TimeoutError("MCP SSE server did not start")


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_cli_sse_exact_tools_with_api_key(anyio_backend: str) -> None:
    port = free_tcp_port()
    process = spawn_server(port, "secret")
    try:
        with pytest.raises(ConnectionError):
            async with Client(SSETransport(f"http://127.0.0.1:{port}/sse")) as client:
                await client.list_tools()
        headers = {"Authorization": "Bearer secret"}
        async with Client(SSETransport(f"http://127.0.0.1:{port}/sse", headers=headers)) as client:
            assert {tool.name for tool in await client.list_tools()} == {
                "datamimic_check",
                "datamimic_run",
                "datamimic_reference",
                "datamimic_scaffold",
            }
    finally:
        process.terminate()
        process.wait(timeout=5)
