"""The project flow over a real stdio server: version, Build, run_project on checked-in tiny projects."""

import csv
import json
import shutil
import sys
from pathlib import Path

import pytest

fastmcp_client = pytest.importorskip("fastmcp.client")
transports = pytest.importorskip("fastmcp.client.transports")
Client = fastmcp_client.Client
PythonStdioTransport = transports.PythonStdioTransport

ROOT = Path(__file__).parents[3]
FIXTURES = ROOT / "tests_ce/unit_tests/test_authoring/project_run"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def stdio_client(cwd: Path) -> object:
    return Client(
        PythonStdioTransport(
            script_path=ROOT / "datamimic_ce/interfaces/mcp/cli.py",
            args=["--transport", "stdio"],
            python_cmd=sys.executable,
            cwd=str(cwd),
            env={"PYTHONPATH": str(ROOT)},
        )
    )


@pytest.mark.anyio
async def test_build_then_run_project_writes_25_rows(anyio_backend: str, tmp_path: Path) -> None:
    project = tmp_path / "customers"
    shutil.copytree(FIXTURES / "customers", project)
    launcher = tmp_path / "launcher"
    launcher.mkdir()
    async with stdio_client(launcher) as client:
        version = json.loads((await client.call_tool("datamimic_version", {}))[0].text)
        assert version["build_protocol"] == "5.0"
        built = json.loads((await client.call_tool("datamimic_build", {"project": str(project)}))[0].text)
        assert built["outcome"] == "ready"
        run = json.loads((await client.call_tool("datamimic_run_project", {"project": str(project)}))[0].text)
    assert run["outcome"] == "completed", run["log_tail"]
    csv_files = [item["path"] for item in run["artifacts"] if item["path"].endswith(".csv")]
    assert len(csv_files) == 1
    with (project / csv_files[0]).open(encoding="utf-8") as handle:
        assert len(list(csv.reader(handle))) == 26
    assert list(launcher.iterdir()) == []


@pytest.mark.anyio
async def test_database_project_is_not_run_without_allow_side_effects(anyio_backend: str, tmp_path: Path) -> None:
    project = tmp_path / "warehouse"
    shutil.copytree(FIXTURES / "warehouse", project)
    before = sorted(path.name for path in project.rglob("*"))
    async with stdio_client(tmp_path) as client:
        run = json.loads((await client.call_tool("datamimic_run_project", {"project": str(project)}))[0].text)
    assert run["outcome"] == "not_run"
    assert {item["kind"] for item in run["required_side_effects"]} == {"database", "target"}
    assert sorted(path.name for path in project.rglob("*")) == before


@pytest.mark.anyio
async def test_rejected_build_is_returned_by_run_project(anyio_backend: str, tmp_path: Path) -> None:
    project = tmp_path / "empty"
    project.mkdir()
    async with stdio_client(tmp_path) as client:
        run = json.loads((await client.call_tool("datamimic_run_project", {"project": str(project)}))[0].text)
    assert run["outcome"] == "not_run" and run["build"]["outcome"] == "rejected"
