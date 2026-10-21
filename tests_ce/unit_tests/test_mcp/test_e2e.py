"""Optional MCP calls use the same typed application contracts as the CLI."""

import json
import threading

import pytest

fastmcp_client = pytest.importorskip("fastmcp.client")
Client = fastmcp_client.Client

import datamimic_ce.interfaces.mcp.server as mcp_server  # noqa: E402
from datamimic_ce.authoring.domain.requests import LintResult  # noqa: E402
from datamimic_ce.interfaces.mcp.server import create_server  # noqa: E402
from tests_ce.authoring_project import write_project  # noqa: E402


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_exact_authoring_tool_surface_and_no_resources(anyio_backend: str) -> None:
    async with Client(create_server()) as client:
        tools = await client.list_tools()
        assert {tool.name for tool in tools} == {
            "datamimic_version",
            "datamimic_schema",
            "datamimic_capabilities",
            "datamimic_capability",
            "datamimic_reference",
            "datamimic_compile",
            "datamimic_decompile",
            "datamimic_build",
            "datamimic_lint",
            "datamimic_dry_run",
            "datamimic_run",
        }
        assert await client.list_resources() == []
        assert all(tool.description for tool in tools)
        build = next(tool for tool in tools if tool.name == "datamimic_build")
        # Build takes no request: the workspace's acceptance/build.json is the only acceptance input.
        assert build.inputSchema["properties"] == {}


@pytest.mark.anyio
async def test_codec_lint_and_reference_use_canonical_contracts(anyio_backend: str) -> None:
    async with Client(create_server()) as client:
        compiled = await client.call_tool("datamimic_compile", {"request": {"document": {"root": {"kind": "setup"}}}})
        compiled_payload = json.loads(compiled[0].text)
        assert compiled_payload["outcome"] == "ready"
        xml = compiled_payload["artifact"]["compiled_xml"]
        decompiled = await client.call_tool("datamimic_decompile", {"request": {"xml": xml}})
        assert json.loads(decompiled[0].text)["document"] == compiled_payload["artifact"]["document"]
        checked = await client.call_tool("datamimic_lint", {"request": {"xml": xml}})
        assert json.loads(checked[0].text)["ok"] is True
        reference = await client.call_tool("datamimic_reference", {"request": {"topic": "overview"}})
        assert json.loads(reference[0].text)["topic"] == "overview"
        capabilities = await client.call_tool("datamimic_capabilities", {})
        assert "setup" in json.loads(capabilities[0].text)["element"]


@pytest.mark.anyio
async def test_blocking_service_work_is_offloaded_from_event_loop(anyio_backend: str, monkeypatch) -> None:
    event_loop_thread = threading.get_ident()
    service_threads: list[int] = []

    class RecordingApplication:
        def lint(self, request) -> LintResult:
            service_threads.append(threading.get_ident())
            return LintResult(ok=True)

    monkeypatch.setattr(mcp_server, "create_authoring_application", lambda **kwargs: RecordingApplication())
    async with Client(create_server()) as client:
        await client.call_tool("datamimic_lint", {"request": {"xml": "<setup/>"}})
    assert service_threads and service_threads[0] != event_loop_thread


@pytest.mark.anyio
async def test_build_matches_cli_and_preserves_caller_requirement_rejections(anyio_backend: str, tmp_path) -> None:
    from pydantic import TypeAdapter
    from typer.testing import CliRunner

    from datamimic_ce.authoring.domain.requests import BuildResult
    from datamimic_ce.interfaces.cli import app

    xml = (
        '<setup rngSeed="7"><generate name="rows" count="2">'
        '<key name="id" generator="IncrementGenerator"/></generate></setup>'
    )
    write_project(tmp_path, xml)
    async with Client(create_server(workspace_root=tmp_path)) as client:
        ready = await client.call_tool("datamimic_build", {})
        cli = CliRunner().invoke(app, ["authoring", "build", str(tmp_path)])
        assert cli.exit_code == 0, cli.stdout
        contract = TypeAdapter(BuildResult)
        assert contract.validate_json(ready[0].text) == contract.validate_json(cli.stdout)
        write_project(
            tmp_path,
            xml,
            acceptance_requirements=[
                {
                    "origin": "caller",
                    "expectation": {
                        "kind": "exact_count",
                        "subject": {"kind": "product", "product": "rows"},
                        "count": 3,
                    },
                }
            ],
        )
        rejected = await client.call_tool("datamimic_build", {})
        payload = json.loads(rejected[0].text)
        assert payload["outcome"] == "rejected"
        assert any(item["path"][:2] == ["acceptance_requirements", 0] for item in payload["diagnostics"])


@pytest.mark.anyio
async def test_bounded_run_tools_preserve_distinct_phases(anyio_backend: str, tmp_path) -> None:
    xml = (
        '<setup rngSeed="7"><generate name="rows" count="2">'
        '<key name="id" generator="IncrementGenerator"/></generate></setup>'
    )
    async with Client(create_server(workspace_root=tmp_path)) as client:
        dry = await client.call_tool("datamimic_dry_run", {"request": {"xml": xml}})
        run = await client.call_tool("datamimic_run", {"request": {"xml": xml}})
        dry_payload, run_payload = json.loads(dry[0].text), json.loads(run[0].text)
        assert dry_payload["ok"] is run_payload["ok"] is True
        assert dry_payload["phase"] == "dry_run"
        assert run_payload["phase"] == "run"
        assert dry_payload["products"] == run_payload["products"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "attributes,fields",
    [
        ('start="not-a-date" end="2026-01-01T04:00:00" interval="PT1H"', '<key name="v" constant="ok"/>'),
        ('start="2026-01-01T00:00:00" end="2026-01-01T04:00:00" interval="P1M"', '<key name="v" constant="ok"/>'),
        ('start="2026-01-01T00:00:00Z" end="2026-01-01T04:00:00" interval="PT1H"', '<key name="v" constant="ok"/>'),
        ('count="1"', '<key name="v" type="float" min="3" max="1"/>'),
        ('count="1"', '<key name="v" type="float" min="NaN" max="1"/>'),
    ],
)
async def test_invalid_dsl_values_return_build_result_over_mcp(anyio_backend, tmp_path, attributes, fields):
    from pydantic import TypeAdapter

    from datamimic_ce.authoring.domain.requests import BuildResult, RejectedBuild

    xml = f'<setup rngSeed="7"><generate name="rows" {attributes}>{fields}</generate></setup>'
    write_project(tmp_path, xml, verification={"smoke_export": True, "deterministic_replay": True})
    async with Client(create_server(workspace_root=tmp_path)) as client:
        response = await client.call_tool("datamimic_build", {})
        result = TypeAdapter(BuildResult).validate_json(response[0].text)
        assert isinstance(result, RejectedBuild), result
        assert result.diagnostics[0].path[:4] == ("document", "root", "children", 0)
        assert result.verification.smoke_export.status == "blocked"
        assert result.verification.deterministic_replay.status == "blocked"
