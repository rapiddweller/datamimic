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
        assert {tool.name for tool in listing} == {
            "list_domains",
            "generate",
            "datamimic_check",
            "datamimic_run",
            "datamimic_reference",
            "datamimic_scaffold",
        }
        resources = await client.read_resource("resource://datamimic/schemas/person/v1/request.json")
        assert resources and "\"$schema\"" in resources[0].text
        cheatsheet = await client.read_resource("resource://datamimic/dsl/cheatsheet")
        assert cheatsheet and "<setup" in cheatsheet[0].text
        recipe = await client.read_resource("resource://datamimic/dsl/recipes/csv-to-json-pipeline")
        assert recipe and "<iterate" in recipe[0].text


@pytest.mark.anyio
async def test_dsl_check_run_reference_loop(anyio_backend) -> None:
    """The agent loop: reference -> check (broken -> fix hints) -> check (clean) -> run."""
    server = create_server()
    broken = "<setup><generate name='u' pagesize='5' target='ConsoleExporter'/></setup>"
    fixed = (
        '<setup rngSeed="1"><memstore id="mem"/>'
        '<generate name="u" count="3" pageSize="100" target="mem">'
        '<key name="id" generator="IncrementGenerator"/></generate></setup>'
    )
    async with Client(server) as client:
        ref = await client.call_tool("datamimic_reference", {"args": {"topic": "element", "name": "generate"}})
        assert "pageSize" in json.loads(ref[0].text)["content"]

        check = json.loads((await client.call_tool("datamimic_check", {"args": {"xml": broken}}))[0].text)
        assert check["ok"] is False
        rules = {diag["rule"] for diag in check["diagnostics"]}
        assert "DM103" in rules  # pagesize -> did you mean pageSize
        assert all(diag["fix_hint"] for diag in check["diagnostics"])

        check2 = json.loads((await client.call_tool("datamimic_check", {"args": {"xml": fixed}}))[0].text)
        assert check2["ok"] is True

        run = json.loads((await client.call_tool("datamimic_run", {"args": {"xml": fixed}}))[0].text)
        assert run["ok"] is True and run["stage"] == "run"
        product = run["products"][0]
        assert product["count"] == 3 and product["sample"][0]["id"] == 1


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
