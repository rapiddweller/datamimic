"""Real stdio transport and project run coverage."""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.adapters.external_effects import CeExternalEffectsDetector
from datamimic_ce.authoring.adapters.project_runner import CeProjectRunner
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.application.project_run import ProjectRunWorkflow
from datamimic_ce.authoring.domain.project_run import ProjectRunRecord, ProjectRunRequest, ProjectRunResult
from datamimic_ce.authoring.domain.requests import PROJECT_ACCEPTANCE_PATH, PROJECT_ENTRY_PATH
from datamimic_ce.interfaces.cli import app

fastmcp_client = pytest.importorskip("fastmcp.client")
transports = pytest.importorskip("fastmcp.client.transports")
Client = fastmcp_client.Client
PythonStdioTransport = transports.PythonStdioTransport
ROOT = Path(__file__).parents[2]
CSV_PROJECT = ROOT / "tests_ce/unit_tests/test_authoring/project_run/customers"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_cli_stdio_authoring_roundtrip(anyio_backend: str) -> None:
    transport = PythonStdioTransport(
        script_path=ROOT / "datamimic_ce/interfaces/mcp/cli.py",
        args=["--transport", "stdio"],
        python_cmd=sys.executable,
        cwd=str(ROOT),
        env={"PYTHONPATH": str(ROOT)},
    )
    async with Client(transport) as client:
        assert {tool.name for tool in await client.list_tools()} == {
            "datamimic_version",
            "datamimic_schema",
            "datamimic_capabilities",
            "datamimic_capability",
            "datamimic_compile",
            "datamimic_decompile",
            "datamimic_build",
            "datamimic_lint",
            "datamimic_dry_run",
            "datamimic_run",
            "datamimic_run_project",
            "datamimic_run_project_unverified",
            "datamimic_init",
            "datamimic_reference",
        }
        result = await client.call_tool(
            "datamimic_reference",
            {"request": {"topic": "overview"}},
        )
        assert json.loads(result.content[0].text)["topic"] == "overview"


@pytest.mark.anyio
async def test_cli_stdio_explicit_workspace_reads_project_instead_of_launcher(tmp_path: Path) -> None:
    project = tmp_path / "project with spaces"
    launcher = tmp_path / "launcher"
    project.mkdir()
    launcher.mkdir()
    (project / "rows.csv").write_text("id\nPROJECT\n", encoding="utf-8")
    (launcher / "rows.csv").write_text("id\nLAUNCHER\n", encoding="utf-8")
    transport = PythonStdioTransport(
        script_path=ROOT / "datamimic_ce/interfaces/mcp/cli.py",
        args=["--transport", "stdio", "--workspace-root", str(project)],
        python_cmd=sys.executable,
        cwd=str(launcher),
        env={"PYTHONPATH": str(ROOT)},
    )
    async with Client(transport) as client:
        result = await client.call_tool(
            "datamimic_dry_run",
            {
                "project": str(project),
                "request": {
                    "xml": '<setup rngSeed="7"><generate name="rows" source="rows.csv" distribution="ordered"/></setup>'
                },
            },
        )
        payload = json.loads(result.content[0].text)
        assert payload["ok"], payload
        assert payload["products"][0]["rows"] == [{"id": "PROJECT"}]


@pytest.mark.anyio
async def test_run_project_cli_and_mcp_return_the_same_proof_and_csv_bytes(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(CSV_PROJECT, project)
    cli = CliRunner().invoke(app, ["authoring", "run-project", str(project)])
    assert cli.exit_code == 0, cli.output
    cli_payload = json.loads(cli.output)

    transport = PythonStdioTransport(
        script_path=ROOT / "datamimic_ce/interfaces/mcp/cli.py",
        args=["--transport", "stdio"],
        python_cmd=sys.executable,
        cwd=str(ROOT),
        env={"PYTHONPATH": str(ROOT)},
    )
    async with Client(transport) as client:
        reply = await client.call_tool("datamimic_run_project", {"project": str(project)})
        mcp_payload = json.loads(reply.content[0].text)

    assert cli_payload["build"] == mcp_payload["build"]
    digests = []
    for payload in (cli_payload, mcp_payload):
        run = ProjectRunResult.model_validate(payload)
        assert run.outcome == "completed" and run.build_outcome == "ready"
        assert run.build is not None
        assert run.record_path is not None
        record = ProjectRunRecord.model_validate_json((project / run.record_path / "run.json").read_bytes())
        assert record.proof == run.build and record.outputs == run.artifacts
        assert record.build_outcome == run.build_outcome
        assert record.build_file_mismatches == run.build_file_mismatches == ()
        (csv_file,) = run.artifacts
        assert csv_file.sha256 == hashlib.sha256((project / csv_file.path).read_bytes()).hexdigest()
        digests.append(csv_file.sha256)
    assert digests[0] == digests[1]


@pytest.mark.parametrize("changed_file", [PROJECT_ENTRY_PATH, PROJECT_ACCEPTANCE_PATH])
def test_run_project_reports_a_changed_or_missing_proof_file(tmp_path: Path, changed_file: PurePosixPath) -> None:
    project = tmp_path / "project"
    shutil.copytree(CSV_PROJECT, project)
    workspace = AuthoringWorkspaceContext(project, PROJECT_ENTRY_PATH)
    build = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()
    assert build.outcome == "ready"

    path = project / changed_file
    if changed_file == PROJECT_ENTRY_PATH:
        path.write_bytes(path.read_bytes().replace(b'rngSeed="7"', b'rngSeed="8"'))
    else:
        path.unlink()

    workflow = ProjectRunWorkflow(lambda: build, CeExternalEffectsDetector(workspace), CeProjectRunner(workspace))
    run = workflow.execute(ProjectRunRequest())

    assert run.outcome == "completed", run.log_tail
    assert run.build_outcome == "ready" and run.build == build.artifact
    assert run.record_path is not None
    record = ProjectRunRecord.model_validate_json((project / run.record_path / "run.json").read_bytes())
    assert record.build_file_mismatches == run.build_file_mismatches == (changed_file.as_posix(),)


@pytest.mark.parametrize("target_change", ["none", "contents", "outside"])
def test_run_project_checks_linked_acceptance_like_build(tmp_path: Path, target_change: str) -> None:
    project = tmp_path / "project"
    shutil.copytree(CSV_PROJECT, project)
    acceptance = project / PROJECT_ACCEPTANCE_PATH
    original = project / "docs" / "original.json"
    original.parent.mkdir()
    acceptance.rename(original)
    try:
        acceptance.symlink_to("../docs/original.json")
    except OSError as error:
        if sys.platform == "win32" and error.winerror == 1314:
            pytest.skip("Windows denied creating this file symlink")
        raise

    workspace = AuthoringWorkspaceContext(project, PROJECT_ENTRY_PATH)
    build = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()
    assert build.outcome == "ready", build.diagnostics
    if target_change == "contents":
        original.write_bytes(original.read_bytes() + b"\n")
    elif target_change == "outside":
        # Even byte-identical content must not satisfy the proof through an external link.
        shutil.copyfile(original, tmp_path / "outside.json")
        acceptance.unlink()
        acceptance.symlink_to("../../outside.json")

    workflow = ProjectRunWorkflow(lambda: build, CeExternalEffectsDetector(workspace), CeProjectRunner(workspace))
    run = workflow.execute(ProjectRunRequest())

    assert run.outcome == "completed", run.log_tail
    assert run.build_file_mismatches == (() if target_change == "none" else (str(PROJECT_ACCEPTANCE_PATH),))


def test_run_project_reports_a_proof_file_changed_by_the_child(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = tmp_path / "project"
    shutil.copytree(CSV_PROJECT, project)
    workspace = AuthoringWorkspaceContext(project, PROJECT_ENTRY_PATH)
    build = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()
    assert build.outcome == "ready", build.diagnostics

    # Run the real CLI and amend the proof file in the same child, before its exit.
    # Build's bounded policy does not allow a DSL <execute> that writes files.
    child = """
import runpy
import sys
from pathlib import Path
sys.argv = sys.argv[1:]
try:
    runpy.run_module(sys.argv[0], run_name="__main__", alter_sys=True)
finally:
    with Path("acceptance/build.json").open("ab") as acceptance:
        acceptance.write(b"\\n")
"""
    popen = subprocess.Popen

    def launch(command, **kwargs):
        assert all(
            hashlib.sha256(workspace.read_project_file(item.path)).hexdigest() == item.sha256
            for item in build.artifact.files
        )
        return popen([*command[:2], "-c", child, *command[3:]], **kwargs)

    monkeypatch.setattr(subprocess, "Popen", launch)
    workflow = ProjectRunWorkflow(lambda: build, CeExternalEffectsDetector(workspace), CeProjectRunner(workspace))
    run = workflow.execute(ProjectRunRequest())

    assert run.outcome == "completed", run.log_tail
    assert run.record_path is not None
    record = ProjectRunRecord.model_validate_json((project / run.record_path / "run.json").read_bytes())
    assert record.build_file_mismatches == run.build_file_mismatches == (str(PROJECT_ACCEPTANCE_PATH),)
