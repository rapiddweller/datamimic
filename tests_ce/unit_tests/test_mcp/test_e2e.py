"""End-to-end contract tests for the reduced MCP authoring adapter."""

import json

import pytest

fastmcp_client = pytest.importorskip("fastmcp.client")
Client = fastmcp_client.Client

from datamimic_ce.mcp.server import create_server  # noqa: E402


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_exact_authoring_tool_surface_and_no_resources(anyio_backend: str) -> None:
    async with Client(create_server()) as client:
        tools = await client.list_tools()
        assert {tool.name for tool in tools} == {
            "datamimic_check",
            "datamimic_run",
            "datamimic_reference",
            "datamimic_scaffold",
        }
        assert await client.list_resources() == []


@pytest.mark.anyio
async def test_reference_and_check_delegate_canonical_contracts(anyio_backend: str) -> None:
    async with Client(create_server()) as client:
        authoring_reference = await client.call_tool(
            "datamimic_reference",
            {"request": {"topic": "authoring"}},
        )
        authoring_payload = json.loads(authoring_reference[0].text)
        assert authoring_payload["ok"] is True
        authoring_content = json.loads(authoring_payload["content"])
        assert {
            "category": "expectation",
            "kind": "range",
            "required_fields": ["product", "field", "minimum", "maximum"],
            "allowed_fields": ["kind", "product", "field", "minimum", "maximum"],
        } in authoring_content["variants"]

        reference = await client.call_tool(
            "datamimic_reference",
            {"request": {"topic": "element", "name": "generate"}},
        )
        reference_payload = json.loads(reference[0].text)
        assert reference_payload["ok"] is True
        assert "pageSize" in reference_payload["content"]

        checked = await client.call_tool(
            "datamimic_check",
            {"request": {"xml": "<setup/>", "response_format": "detailed"}},
        )
        check_payload = json.loads(checked[0].text)
        assert check_payload["ok"] is True
