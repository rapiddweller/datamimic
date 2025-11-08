"""End-to-end tests exercising the FastMCP server."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable

import anyio
import pytest

fastmcp_client = pytest.importorskip(
    "fastmcp.client", reason="fastmcp extra required; install datamimic_ce[mcp]"
)
uvicorn = pytest.importorskip("uvicorn", reason="uvicorn required for SSE transport tests")

Client = fastmcp_client.Client

from datamimic_ce.domains.determinism import canonical_json, hash_bytes
from datamimic_ce.mcp.models import GenerateArgs
from datamimic_ce.mcp.server import (
    HTTP_MIDDLEWARE_ATTR,
    build_sse_app,
    create_server,
)


@pytest.fixture
def anyio_backend() -> str:  # pragma: no cover - fixture glue
    return "asyncio"


async def _call_generate(client: Client, args: GenerateArgs) -> dict:
    payload = args.model_dump(mode="python")
    result = await client.call_tool("generate", {"args": payload})
    assert result, "FastMCP generate tool returned no content"
    text_payload = result[0].text
    assert text_payload, "FastMCP generate tool returned empty text"
    return dict(json.loads(text_payload))


@pytest.mark.anyio
async def test_generate_is_deterministic(anyio_backend) -> None:
    server = create_server()
    async with Client(server) as client:
        args = GenerateArgs(domain="person", locale="en_US", seed=42)
        first = await _call_generate(client, args)
        second = await _call_generate(client, args)
        assert canonical_json(first) == canonical_json(second)
        assert hash_bytes(canonical_json(first)) == hash_bytes(canonical_json(second))


@pytest.mark.anyio
async def test_schema_resource_available(anyio_backend) -> None:
    server = create_server()
    async with Client(server) as client:
        listing = await client.list_tools()
        assert {tool.name for tool in listing} == {"list_domains", "generate"}
        resources = await client.read_resource("resource://datamimic/schemas/person/v1/request.json")
        assert resources and "\"$schema\"" in resources[0].text


@pytest.mark.anyio
async def test_sse_transport_roundtrip(anyio_backend, free_tcp_port_factory) -> None:
    server = create_server()
    middleware = getattr(server, HTTP_MIDDLEWARE_ATTR, None)
    sse_app = build_sse_app(server, middleware)

    port = free_tcp_port_factory()
    config = uvicorn.Config(
        sse_app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        loop="asyncio",
        lifespan="on",
    )
    uvicorn_server = uvicorn.Server(config)

    thread = threading.Thread(target=uvicorn_server.run, daemon=True)
    thread.start()

    await _wait_for(lambda: uvicorn_server.started)

    try:
        async with Client(f"http://127.0.0.1:{port}/sse") as client:
            args = GenerateArgs(domain="person", seed=99)
            payload = await _call_generate(client, args)
            assert payload["items"], "Expected generated items from SSE transport"
    finally:
        uvicorn_server.should_exit = True
        uvicorn_server.force_exit = True
        await anyio.to_thread.run_sync(thread.join, 5)


async def _wait_for(condition: Callable[[], bool], timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return
        await anyio.sleep(0.05)
    raise TimeoutError("Timed out waiting for condition")
