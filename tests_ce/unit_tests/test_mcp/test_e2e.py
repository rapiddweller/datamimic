"""End-to-end contract tests for the reduced MCP authoring adapter."""

import json
import threading

import pytest

fastmcp_client = pytest.importorskip("fastmcp.client")
Client = fastmcp_client.Client

from datamimic_ce.mcp.server import create_server  # noqa: E402
import datamimic_ce.mcp.server as mcp_server  # noqa: E402
from datamimic_ce.authoring.diagnostics import LintResult  # noqa: E402


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
        assert all(tool.description for tool in tools)


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

        field_reference = await client.call_tool(
            "datamimic_reference",
            {"request": {"topic": "authoring", "category": "field"}},
        )
        field_payload = json.loads(field_reference[0].text)
        assert field_payload["ok"] is True
        field_content = json.loads(field_payload["content"])
        assert {variant["category"] for variant in field_content["variants"]} == {"field"}

        reference = await client.call_tool(
            "datamimic_reference",
            {"request": {"topic": "element", "name": "generate"}},
        )
        reference_payload = json.loads(reference[0].text)
        assert reference_payload["ok"] is True
        assert "pageSize" in reference_payload["content"]

        checked = await client.call_tool(
            "datamimic_check",
            {"request": {"xml": "<setup/>"}},
        )
        check_payload = json.loads(checked[0].text)
        assert check_payload["ok"] is True


@pytest.mark.anyio
async def test_scaffold_evaluates_caller_owned_acceptance_requirements(anyio_backend: str) -> None:
    async with Client(create_server()) as client:
        result = await client.call_tool(
            "datamimic_scaffold",
            {
                "request": {
                    "spec": {
                        "version": "1",
                        "seed": 7,
                        "products": [
                            {
                                "kind": "generated",
                                "name": "records",
                                "count": 1,
                                "fields": [{"kind": "increment", "name": "id"}],
                            }
                        ],
                    },
                    "acceptance_requirements": [
                        {"kind": "exact_count", "product": "records", "count": 2}
                    ],
                }
            },
        )

    payload = json.loads(result[0].text)
    caller_result = next(item for item in payload["acceptance"]["results"] if item["source"] == "caller")
    assert caller_result["kind"] == "exact_count"
    assert caller_result["status"] == "fail"
    assert payload["verified"] is False


@pytest.mark.anyio
async def test_blocking_service_work_is_offloaded_from_the_event_loop(
    anyio_backend: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    event_loop_thread = threading.get_ident()
    service_threads: list[int] = []

    def blocking_check(_request: object) -> LintResult:
        service_threads.append(threading.get_ident())
        return LintResult(ok=True)

    monkeypatch.setattr(mcp_server.service, "check", blocking_check)
    async with Client(create_server()) as client:
        await client.call_tool("datamimic_check", {"request": {"xml": "<setup/>"}})

    assert service_threads and service_threads[0] != event_loop_thread
