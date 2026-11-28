"""Optional MCP calls use the same typed application contracts as the CLI."""

import json
import threading
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

fastmcp_client = pytest.importorskip("fastmcp.client")
Client = fastmcp_client.Client

from fastmcp.exceptions import ToolError  # noqa: E402

import datamimic_ce.interfaces.mcp.server as mcp_server  # noqa: E402
from datamimic_ce.authoring.domain.requests import LintResult  # noqa: E402
from datamimic_ce.interfaces.mcp.server import create_server  # noqa: E402
from tests_ce.authoring_project import write_project  # noqa: E402

DESCRIPTOR = Path(__file__).resolve().parents[2] / "scenarios" / "s01_flat_seeded" / "datamimic.xml"


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
            "datamimic_run_project",
            "datamimic_init",
        }
        assert await client.list_resources() == []
        assert all(tool.description for tool in tools)
        build = next(tool for tool in tools if tool.name == "datamimic_build")
        # Build takes only the project: its acceptance/build.json is the only acceptance input.
        assert set(build.input_schema["properties"]) == {"project"}
        assert build.input_schema["required"] == ["project"]
        version = json.loads((await client.call_tool("datamimic_version", {})).content[0].text)
        assert version["build_protocol"] == "5.0"
        capabilities = await client.call_tool("datamimic_capabilities", {})
        assert "setup" in json.loads(capabilities.content[0].text)["element"]


@pytest.mark.anyio
async def test_flat_and_legacy_arguments_use_the_same_authoring_contracts(anyio_backend: str, tmp_path) -> None:
    project = {"project": str(tmp_path)}
    xml = {"xml": DESCRIPTOR.read_text(encoding="utf-8")}
    async with Client(create_server()) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}

        async def compare(tool: str, project_args: dict, fields: dict) -> dict:
            name = f"datamimic_{tool}"
            schema = tools[name].input_schema
            assert schema["properties"]["request"]["deprecated"] is True
            assert schema["oneOf"][0]["title"] == "Preferred: flat arguments"
            flat = {**project_args, **fields}
            legacy = {**project_args, "request": fields}
            mixed = {**flat, "request": fields}
            validator = Draft202012Validator(schema)
            validator.validate(flat)
            validator.validate(legacy)
            assert not validator.is_valid(mixed)
            flat_result = await client.call_tool(name, flat)
            legacy_result = await client.call_tool(name, legacy)
            payload = json.loads(flat_result.content[0].text)
            assert payload == json.loads(legacy_result.content[0].text)
            with pytest.raises(ToolError, match=r"Do not mix flat arguments with request\. Use \{"):
                await client.call_tool(name, mixed)
            return payload

        decompiled = await compare("decompile", project, xml)
        compiled = await compare("compile", project, {"document": decompiled["document"]})
        assert compiled["outcome"] == "ready"
        assert compiled["artifact"]["document"] == decompiled["document"]
        assert (await compare("lint", project, xml))["ok"] is True
        run_fields = {**xml, "max_count": 10, "sample_rows": 2}
        dry = await compare("dry_run", project, run_fields)
        run = await compare("run", project, run_fields)
        assert dry["ok"] is run["ok"] is True
        assert dry["phase"] == "dry_run"
        assert run["phase"] == "run"
        assert dry["products"] == run["products"]
        reference = await compare("reference", {}, {"topic": "assembly", "name": "starter"})
        assert reference["topic"] == "assembly"
        default = await client.call_tool("datamimic_reference", {})
        legacy_default = await client.call_tool("datamimic_reference", {"request": {}})
        assert default.content == legacy_default.content
        assert json.loads(default.content[0].text)["topic"] == "overview"


@pytest.mark.anyio
async def test_reference_unknown_name_is_a_typed_miss_and_known_name_a_hit(anyio_backend: str) -> None:
    async with Client(create_server()) as client:
        miss = json.loads(
            (await client.call_tool("datamimic_reference", {"topic": "rules", "name": "DM0"})).content[0].text
        )
        hit = json.loads(
            (await client.call_tool("datamimic_reference", {"topic": "rules", "name": "DM401"})).content[0].text
        )
    assert (miss["ok"], miss["error"], miss["content"]) == (False, "reference_not_found", "No matching rule.")
    assert "DM401" in miss["available_names"]
    assert hit["ok"] is True


@pytest.mark.anyio
@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"xml": "<setup/>"},
        {"project": ".", "xml": ""},
        {"project": ".", "xml": 1},
        {"project": ".", "request": None},
        {"project": ".", "request": {}},
        {"request": {"project": ".", "xml": "<setup/>"}},
        {"project": ".", "unknown": "<setup/>"},
    ],
)
async def test_invalid_arguments_show_the_preferred_example(anyio_backend: str, arguments) -> None:
    async with Client(create_server()) as client:
        with pytest.raises(
            ToolError, match=r'Invalid arguments\. Use \{"project": "/absolute/project", "xml": "<setup/>"\}'
        ):
            await client.call_tool("datamimic_lint", arguments)


@pytest.mark.anyio
async def test_blocking_service_work_is_offloaded_from_event_loop(anyio_backend: str, monkeypatch, tmp_path) -> None:
    event_loop_thread = threading.get_ident()
    service_threads: list[int] = []

    class RecordingApplication:
        def lint(self, request) -> LintResult:
            service_threads.append(threading.get_ident())
            return LintResult(ok=True)

    monkeypatch.setattr(mcp_server, "create_authoring_application", lambda **kwargs: RecordingApplication())
    async with Client(create_server()) as client:
        await client.call_tool("datamimic_lint", {"project": str(tmp_path), "request": {"xml": "<setup/>"}})
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
    async with Client(create_server()) as client:
        ready = await client.call_tool("datamimic_build", {"project": str(tmp_path)})
        cli = CliRunner().invoke(app, ["authoring", "build", str(tmp_path)])
        assert cli.exit_code == 0, cli.stdout
        contract = TypeAdapter(BuildResult)
        assert contract.validate_json(ready.content[0].text) == contract.validate_json(cli.stdout)
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
        rejected = await client.call_tool("datamimic_build", {"project": str(tmp_path)})
        payload = json.loads(rejected.content[0].text)
        assert payload["outcome"] == "rejected"
        assert any(item["path"][:2] == ["acceptance_requirements", 0] for item in payload["diagnostics"])


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
    async with Client(create_server()) as client:
        response = await client.call_tool("datamimic_build", {"project": str(tmp_path)})
        result = TypeAdapter(BuildResult).validate_json(response.content[0].text)
        assert isinstance(result, RejectedBuild), result
        assert result.diagnostics[0].path[:4] == ("document", "root", "children", 0)
        assert result.verification.smoke_export.status == "blocked"
        assert result.verification.deterministic_replay.status == "blocked"
