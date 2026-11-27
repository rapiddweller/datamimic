"""Running a project for its real output: Build first, effects refused unless allowed."""

import csv
import json
import os
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Literal

import pytest
from pydantic import ValidationError

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.adapters.external_effects import CeExternalEffectsDetector
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.application.project_run import ProjectRunWorkflow
from datamimic_ce.authoring.domain.project_run import (
    ExternalEffect,
    ExternalEffectKind,
    ProjectParam,
    ProjectRunExecution,
    ProjectRunRecord,
    ProjectRunRequest,
    UnverifiedProjectRunResult,
)
from datamimic_ce.authoring.domain.requests import (
    PROJECT_ENTRY_PATH,
    BuildArtifact,
    BuildResult,
    ReadyBuild,
    ReadyWithGapsBuild,
    RejectedBuild,
)
from tests_ce.authoring_coverage_fixtures import coverage as _coverage
from tests_ce.authoring_coverage_fixtures import ready_fields as _ready_fields

FIXTURES = Path(__file__).parent / "project_run"
EFFECT = ExternalEffect(kind=ExternalEffectKind.DATABASE, name="db", descriptor="datamimic.xml")


def project(tmp_path: Path, name: str) -> Path:
    target = tmp_path / name
    shutil.copytree(FIXTURES / name, target)
    return target


class FakeRunner:
    def __init__(self, execution: ProjectRunExecution) -> None:
        self.execution = execution
        self.calls: list[tuple[ProjectParam, ...]] = []

    def run(
        self,
        params: tuple[ProjectParam, ...],
        timeout_seconds: int,
        proof: BuildArtifact | None = None,
        *,
        build_outcome: Literal["ready", "ready_with_gaps"] | None = None,
    ) -> ProjectRunExecution:
        self.calls.append(params)
        if proof is not None:
            return self.execution.model_copy(update={"build_file_mismatches": ()})
        return self.execution


class FakeEffects:
    def __init__(self, effects: tuple[ExternalEffect, ...]) -> None:
        self._effects = effects

    def effects(self) -> tuple[ExternalEffect, ...]:
        return self._effects


def execution(exit_code: int | None = 0, timed_out: bool = False) -> ProjectRunExecution:
    return ProjectRunExecution(
        exit_code=exit_code,
        timed_out=timed_out,
        duration_seconds=0.5,
        artifacts=(),
        artifact_count=0,
        log_tail=("done",),
    )


def workflow(build: BuildResult, effects: tuple[ExternalEffect, ...], runner: FakeRunner) -> ProjectRunWorkflow:
    return ProjectRunWorkflow(lambda: build, FakeEffects(effects), runner)


def ready_build() -> ReadyBuild:
    """A validated Build result for workflow tests; real Build-to-run proofs are tested separately."""
    return ReadyBuild(**_ready_fields(_coverage()))


def gaps_build() -> ReadyWithGapsBuild:
    coverage = _coverage(seeded=False)
    return ReadyWithGapsBuild(
        **_ready_fields(coverage),
        action_required=coverage.action_required() or "",
        diagnostics=coverage.warnings(),
    )


def test_rejected_build_stops_before_any_run(tmp_path: Path) -> None:
    runner = FakeRunner(execution())
    rejected = RejectedBuild.from_input_error("broken")
    result = workflow(rejected, (), runner).execute(ProjectRunRequest())
    assert result.outcome == "not_run" and result.build == rejected
    assert runner.calls == []
    assert result.not_run_reason == "build_rejected"


@pytest.mark.parametrize(
    "run,expected",
    [(execution(), "completed"), (execution(3), "failed"), (execution(None, timed_out=True), "timeout")],
)
def test_unverified_run_reports_execution_without_build(run: ProjectRunExecution, expected: str) -> None:
    runner = FakeRunner(run)

    def forbidden_build() -> BuildResult:
        raise AssertionError("the unverified run must not invoke Build")

    subject = ProjectRunWorkflow(forbidden_build, FakeEffects(()), runner)
    result = subject.execute_unverified(ProjectRunRequest(allow_side_effects=True), True)
    assert result.outcome == expected
    assert result.verification == "not_verified"
    assert result.execution == run


def test_unverified_result_rejects_inconsistent_execution() -> None:
    with pytest.raises(ValidationError):
        UnverifiedProjectRunResult(outcome="completed", message="not verified", execution=execution(1))
    with pytest.raises(ValidationError):
        UnverifiedProjectRunResult(outcome="not_run", message="not verified", execution=execution())


def test_a_build_with_open_coverage_gaps_still_runs() -> None:
    build = gaps_build()
    runner = FakeRunner(execution())

    result = workflow(build, (), runner).execute(ProjectRunRequest())

    assert build.outcome == "ready_with_gaps", build
    assert result.outcome == "completed"
    assert len(runner.calls) == 1
    assert result.build_outcome == "ready_with_gaps"
    assert result.build == build.artifact
    assert result.coverage is not None and not result.coverage.seeded
    assert result.action_required == build.action_required
    assert "seeded" in (result.action_required or "")


def test_run_preserves_build_warning_diagnostics() -> None:
    build = gaps_build()
    assert any(item.severity == "warning" for item in build.diagnostics)

    result = workflow(build, (), FakeRunner(execution())).execute(ProjectRunRequest())

    warnings = tuple(item for item in build.diagnostics if item.severity == "warning")
    assert all(item in result.diagnostics for item in warnings)


def test_a_clean_ready_run_carries_the_outcome_and_no_action() -> None:
    result = workflow(ready_build(), (), FakeRunner(execution())).execute(ProjectRunRequest())

    assert result.outcome == "completed"
    assert result.build_outcome == "ready"
    assert result.coverage is not None and not result.coverage.has_gaps
    assert result.action_required is None


def test_effects_without_the_flag_are_listed_and_nothing_runs() -> None:
    runner = FakeRunner(execution())
    result = workflow(ready_build(), (EFFECT,), runner).execute(ProjectRunRequest())
    assert result.outcome == "not_run" and result.required_side_effects == (EFFECT,)
    assert result.not_run_reason == "side_effects_not_allowed"
    assert isinstance(result.build, BuildArtifact) and result.build_file_mismatches is None
    assert result.diagnostics[0].code.value == "side_effect"
    assert runner.calls == []


@pytest.mark.parametrize(
    "effects,message",
    [
        (
            (ExternalEffect(kind=ExternalEffectKind.EXECUTE, name="lib/solver.scr.py", descriptor="datamimic.xml"),),
            "The project runs Python code from lib/solver.scr.py; nothing was run.",
        ),
        (
            (
                ExternalEffect(kind=ExternalEffectKind.EXECUTE, name="lib/b.scr.py", descriptor="datamimic.xml"),
                ExternalEffect(kind=ExternalEffectKind.EXECUTE, name="lib/a.scr.py", descriptor="datamimic.xml"),
                EFFECT,
            ),
            "The project runs Python code from lib/a.scr.py, lib/b.scr.py and reaches outside its directory; "
            "nothing was run.",
        ),
        ((EFFECT,), "The project reaches outside its directory; nothing was run."),
    ],
)
def test_the_refusal_names_the_python_files_it_would_run(effects: tuple[ExternalEffect, ...], message: str) -> None:
    result = workflow(ready_build(), effects, FakeRunner(execution())).execute(ProjectRunRequest())
    assert result.diagnostics[0].message == message


def test_a_hybrid_project_is_refused_with_its_lib_file_named(tmp_path: Path) -> None:
    root = tmp_path / "hybrid"
    shutil.copytree(Path(__file__).parents[2] / "scenarios" / "s20_library_names", root)
    result = create_authoring_application(root, descriptor_path=PROJECT_ENTRY_PATH).run_project(ProjectRunRequest())
    assert result.not_run_reason == "side_effects_not_allowed"
    assert result.diagnostics[0].message == "The project runs Python code from lib/helpers.scr.py; nothing was run."
    assert [effect.name for effect in result.required_side_effects] == ["lib/helpers.scr.py"]


def test_allowed_effects_run_and_params_reach_the_runner() -> None:
    runner = FakeRunner(execution())
    request = ProjectRunRequest(allow_side_effects=True, params=(ProjectParam(name="STAGE", value="test"),))
    result = workflow(ready_build(), (EFFECT,), runner).execute(request)
    assert result.outcome == "completed" and result.exit_code == 0
    assert runner.calls == [(ProjectParam(name="STAGE", value="test"),)]


@pytest.mark.parametrize("run,outcome", [(execution(3), "failed"), (execution(None, timed_out=True), "timeout")])
def test_failed_and_timed_out_runs_carry_a_diagnostic(run: ProjectRunExecution, outcome: str) -> None:
    result = workflow(ready_build(), (), FakeRunner(run)).execute(ProjectRunRequest())
    assert result.outcome == outcome
    assert result.diagnostics[0].code.value == "child_execution"
    assert result.log_tail == ("done",)


@pytest.mark.parametrize(
    "arguments",
    [
        {"timeout_seconds": 0},
        {"timeout_seconds": 841},
        {"params": [{"name": "bad name", "value": "x"}]},
        {"params": [{"name": "1x", "value": "y"}]},
    ],
)
def test_request_refuses_bad_options(arguments: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ProjectRunRequest.model_validate(arguments)


def test_detector_finds_no_effect_in_a_file_project(tmp_path: Path) -> None:
    root = project(tmp_path, "customers")
    assert CeExternalEffectsDetector(AuthoringWorkspaceContext(root, PROJECT_ENTRY_PATH)).effects() == ()


def test_detector_finds_database_and_its_target(tmp_path: Path) -> None:
    root = project(tmp_path, "warehouse")
    effects = CeExternalEffectsDetector(AuthoringWorkspaceContext(root, PROJECT_ENTRY_PATH)).effects()
    assert {(effect.kind, effect.name) for effect in effects} == {
        (ExternalEffectKind.DATABASE, "db"),
        (ExternalEffectKind.TARGET, "db"),
    }


def test_detector_reads_included_steps_and_ignores_memstore_and_console(tmp_path: Path) -> None:
    root = tmp_path / "steps"
    root.mkdir()
    (root / "datamimic.xml").write_text(
        '<setup><memstore id="m"/><include uri="step.xml"/>'
        '<generate name="a" count="1" target="m,ConsoleExporter,JSON"><key name="id" constant="1"/></generate></setup>',
        encoding="utf-8",
    )
    (root / "step.xml").write_text(
        '<setup><execute type="python">x = 1</execute></setup>',
        encoding="utf-8",
    )
    effects = CeExternalEffectsDetector(AuthoringWorkspaceContext(root, PROJECT_ENTRY_PATH)).effects()
    assert [(effect.kind, effect.descriptor) for effect in effects] == [(ExternalEffectKind.EXECUTE, "step.xml")]


def test_unreadable_include_graph_is_unresolved(tmp_path: Path) -> None:
    root = tmp_path / "broken"
    root.mkdir()
    (root / "datamimic.xml").write_text('<setup><include uri="missing.xml"/></setup>', encoding="utf-8")
    effects = CeExternalEffectsDetector(AuthoringWorkspaceContext(root, PROJECT_ENTRY_PATH)).effects()
    assert [effect.kind for effect in effects] == [ExternalEffectKind.UNRESOLVED]


def test_real_run_writes_the_csv_and_lists_it(tmp_path: Path) -> None:
    root = project(tmp_path, "customers")
    application = create_authoring_application(root, descriptor_path=PROJECT_ENTRY_PATH)
    result = application.run_project(ProjectRunRequest(timeout_seconds=300))
    assert result.outcome == "completed", result.log_tail
    csv_files = [artifact.path for artifact in result.artifacts if artifact.path.endswith(".csv")]
    assert len(csv_files) == 1
    with (root / csv_files[0]).open(encoding="utf-8") as handle:
        assert len(list(csv.reader(handle))) == 26
    assert "datamimic.xml" not in [artifact.path for artifact in result.artifacts]
    assert result.artifact_count == len(result.artifacts)


def test_real_run_of_database_project_is_refused_and_writes_nothing(tmp_path: Path) -> None:
    root = project(tmp_path, "warehouse")
    before = sorted(path.name for path in root.rglob("*"))
    result = create_authoring_application(root, descriptor_path=PROJECT_ENTRY_PATH).run_project(ProjectRunRequest())
    assert result.outcome == "not_run" and result.required_side_effects
    assert sorted(path.name for path in root.rglob("*")) == before


def test_cli_run_project_matches_the_application(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from datamimic_ce.interfaces.cli import app

    root = project(tmp_path, "warehouse")
    refused = CliRunner().invoke(app, ["authoring", "run-project", str(root)])
    assert refused.exit_code == 1
    assert json.loads(refused.stdout)["outcome"] == "not_run"
    bad = CliRunner().invoke(app, ["authoring", "run-project", str(root), "--param", "novalue"])
    assert bad.exit_code == 1
    assert json.loads(bad.stdout)["diagnostics"][0]["code"] == "input"


def effects_of(tmp_path: Path, xml: str) -> list[tuple[ExternalEffectKind, str]]:
    root = tmp_path / "probe"
    root.mkdir()
    (root / "datamimic.xml").write_text(xml, encoding="utf-8")
    found = CeExternalEffectsDetector(AuthoringWorkspaceContext(root, PROJECT_ENTRY_PATH)).effects()
    return [(effect.kind, effect.name) for effect in found]


def test_detector_refuses_mongodb(tmp_path: Path) -> None:
    xml = (
        '<setup><mongodb id="mongo" host="localhost" port="27017" database="t"/>'
        '<generate name="a" count="1" target="mongo"><key name="id" constant="1"/></generate></setup>'
    )
    assert (ExternalEffectKind.MONGODB, "mongo") in effects_of(tmp_path, xml)


@pytest.mark.parametrize("target", ["KafkaExporter", "S3Exporter", "MinioExporter", "csv", "unknown_client"])
def test_detector_refuses_queue_storage_and_unknown_targets(tmp_path: Path, target: str) -> None:
    xml = f'<setup><generate name="a" count="1" target="{target}"><key name="id" constant="1"/></generate></setup>'
    assert (ExternalEffectKind.TARGET, target) in effects_of(tmp_path, xml)


def test_detector_refuses_a_dynamic_target(tmp_path: Path) -> None:
    xml = '<setup><generate name="a" count="1" target="${x}"><key name="id" constant="1"/></generate></setup>'
    assert effects_of(tmp_path, xml), "a placeholder target must never count as local"


def test_unreadable_target_is_reported_with_fixed_text(tmp_path: Path) -> None:
    from datamimic_ce.authoring.adapters.dryrun import UNREADABLE_TARGET, classify_targets

    classified = classify_targets({"CSV(unclosed"}, frozenset())
    assert classified.unreadable and classified.external == ()
    xml = '<setup><generate name="a" count="1" target="CSV(unclosed"><key name="id" constant="1"/></generate></setup>'
    found = effects_of(tmp_path, xml)
    assert found and all("unclosed" not in name for _, name in found)
    assert (ExternalEffectKind.UNRESOLVED, UNREADABLE_TARGET) in found or found[0][0] is ExternalEffectKind.UNRESOLVED


def test_one_classification_serves_the_dry_run_and_the_run_check() -> None:
    from datamimic_ce.authoring.adapters.dryrun import classify_targets

    classified = classify_targets({"CSV", "JSON(chunk_size=10)", "ConsoleExporter", "mem", "db"}, {"mem"})
    assert [name for name, _ in classified.files] == ["CSV", "JSON"]
    assert classified.diagnostics == ("ConsoleExporter",)
    assert classified.external == ("db",)


def test_runner_stops_a_run_that_exceeds_the_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess
    import sys

    from datamimic_ce.authoring.adapters import project_runner

    root = project(tmp_path, "customers")
    real_popen = subprocess.Popen
    started: list[int] = []

    def slow(command, **kwargs):
        process = real_popen(
            [sys.executable, "-c", "import time; print('start', flush=True); time.sleep(60)"], **kwargs
        )
        started.append(process.pid)
        return process

    monkeypatch.setattr(
        project_runner,
        "subprocess",
        SimpleNamespace(
            Popen=slow,
            DEVNULL=subprocess.DEVNULL,
            STDOUT=subprocess.STDOUT,
            TimeoutExpired=subprocess.TimeoutExpired,
        ),
    )
    run = project_runner.CeProjectRunner(AuthoringWorkspaceContext(root, PROJECT_ENTRY_PATH)).run((), 1)
    assert run.timed_out and run.exit_code is None
    assert run.log_tail == ("start",)
    assert run.duration_seconds < 30


def test_project_file_named_like_a_module_does_not_shadow_the_package(tmp_path: Path) -> None:
    root = project(tmp_path, "customers")
    shadow = root / "datamimic_ce"
    shadow.mkdir()
    (shadow / "__init__.py").write_text('raise RuntimeError("wrong launcher package")\n', encoding="utf-8")
    result = create_authoring_application(root, descriptor_path=PROJECT_ENTRY_PATH).run_project(
        ProjectRunRequest(timeout_seconds=300)
    )
    assert result.outcome == "completed", result.log_tail


def test_result_rejects_contradictory_not_run_state() -> None:
    from datamimic_ce.authoring.domain.project_run import ProjectRunResult

    with pytest.raises(ValidationError):
        ProjectRunResult(outcome="not_run", not_run_reason="input", exit_code=0)


@pytest.mark.skipif(sys.platform == "win32", reason="process groups are POSIX-only")
@pytest.mark.parametrize("error", [ProcessLookupError, PermissionError])
def test_runner_tolerates_process_group_disappearing_during_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: type[OSError]
) -> None:
    import os
    import subprocess
    import sys

    from datamimic_ce.authoring.adapters import project_runner

    root = project(tmp_path, "customers")
    real_popen = subprocess.Popen
    original_killpg = os.killpg

    def slow(command, **kwargs):
        return real_popen([sys.executable, "-c", "import time; time.sleep(60)"], **kwargs)

    def killpg(pid: int, sig: int) -> None:
        original_killpg(pid, sig)
        raise error("leader exited")

    monkeypatch.setattr(project_runner.subprocess, "Popen", slow)
    monkeypatch.setattr(project_runner.os, "killpg", killpg)
    result = project_runner.CeProjectRunner(AuthoringWorkspaceContext(root, PROJECT_ENTRY_PATH)).run((), 1)
    assert result.timed_out


@pytest.mark.skipif(sys.platform == "win32", reason="os.killpg is POSIX-only")
def test_runner_does_not_kill_group_after_normal_exit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import os
    import subprocess
    import sys

    from datamimic_ce.authoring.adapters import project_runner

    root = project(tmp_path, "customers")
    real_popen = subprocess.Popen
    original_killpg = os.killpg
    calls: list[int] = []

    def finished(command, **kwargs):
        return real_popen([sys.executable, "-c", "pass"], **kwargs)

    def killpg(pid: int, sig: int) -> None:
        calls.append(pid)
        original_killpg(pid, sig)

    monkeypatch.setattr(project_runner.subprocess, "Popen", finished)
    monkeypatch.setattr(project_runner.os, "killpg", killpg)
    result = project_runner.CeProjectRunner(AuthoringWorkspaceContext(root, PROJECT_ENTRY_PATH)).run((), 5)
    assert result.exit_code == 0
    assert calls == []


def test_cli_text_prints_build_diagnostics_when_project_is_rejected(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from datamimic_ce.interfaces.cli import app

    root = project(tmp_path, "customers")
    (root / PROJECT_ENTRY_PATH).write_text("<setup><invalid/></setup>", encoding="utf-8")
    result = CliRunner().invoke(app, ["authoring", "run-project", str(root), "--format", "text"])
    assert result.exit_code == 1
    assert "parser validation" in result.output.lower()


def test_project_run_result_validates_workflow_shapes_and_exit_fields() -> None:
    from datamimic_ce.authoring.domain.project_run import ProjectRunResult

    build_schema = ProjectRunResult.model_json_schema()["properties"]["build"]["anyOf"]
    assert {arm.get("$ref", arm.get("type")) for arm in build_schema} == {
        "#/$defs/BuildArtifact",
        "#/$defs/RejectedBuild",
        "null",
    }

    ready = ready_build()
    gaps = gaps_build()
    valid_results = (
        ProjectRunResult.from_input_error("bad params"),
        workflow(RejectedBuild.from_input_error("bad project"), (), FakeRunner(execution())).execute(
            ProjectRunRequest()
        ),
        workflow(ready, (EFFECT,), FakeRunner(execution())).execute(ProjectRunRequest()),
        workflow(ready, (), FakeRunner(execution())).execute(ProjectRunRequest()),
        workflow(ready, (), FakeRunner(execution(9))).execute(ProjectRunRequest()),
        workflow(ready, (), FakeRunner(execution(None, timed_out=True))).execute(ProjectRunRequest()),
        workflow(gaps, (), FakeRunner(execution())).execute(ProjectRunRequest()),
    )
    for result in valid_results:
        ProjectRunResult.model_validate(result.model_dump(mode="json"))

    completed = valid_results[3].model_dump(mode="json")
    input_error = valid_results[0].model_dump(mode="json")
    rejected = valid_results[1].model_dump(mode="json")
    gaps = valid_results[6].model_dump(mode="json")
    contradictory = (
        {**completed, "exit_code": 9},
        {**completed, "outcome": "timeout", "exit_code": 0},
        {**completed, "outcome": "failed", "exit_code": None},
        {**completed, "duration_seconds": None},
        {**completed, "build": None},
        {**completed, "build_file_mismatches": None},
        {**completed, "build": rejected["build"]},
        {**input_error, "exit_code": 0},
        {**input_error, "duration_seconds": 0.1},
        {**input_error, "artifacts": [{"path": "out.csv", "bytes": 1}], "artifact_count": 1},
        {**input_error, "action_required": "Fix open coverage gaps."},
        {**rejected, "action_required": "Fix open coverage gaps."},
        {**gaps, "action_required": None},
    )
    for payload in contradictory:
        with pytest.raises(ValidationError):
            ProjectRunResult.model_validate(payload)


def test_cli_text_shows_gaps_build_outcome_and_action_required(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from datamimic_ce.interfaces.cli import app

    root = project(tmp_path, "customers")
    entry = root / PROJECT_ENTRY_PATH
    entry.write_text(entry.read_text(encoding="utf-8").replace(' rngSeed="7"', ""), encoding="utf-8")
    result = CliRunner().invoke(app, ["authoring", "run-project", str(root), "--format", "text", "--timeout", "300"])
    assert result.exit_code == 0, result.output
    assert "Build outcome: ready_with_gaps" in result.output
    assert "Build files: digests match" in result.output
    assert "Action required:" in result.output


def _record(root: Path, record_path: str | None) -> ProjectRunRecord:
    assert record_path is not None
    return ProjectRunRecord.model_validate_json((root / record_path / "run.json").read_text(encoding="utf-8"))


def test_a_real_run_keeps_the_full_log_and_an_audit_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import hashlib

    from datamimic_ce.authoring.adapters import project_runner

    monkeypatch.setattr(project_runner, "LOG_TAIL_LINES", 3)  # the tail is short; the file must hold the whole log
    root = project(tmp_path, "customers")
    application = create_authoring_application(root, descriptor_path=PROJECT_ENTRY_PATH)
    proof = application.build().artifact

    result = application.run_project(
        ProjectRunRequest(timeout_seconds=300, params=(ProjectParam(name="TOKEN", value="s3cret"),))
    )

    assert result.outcome == "completed", result.log_tail
    record = _record(root, result.record_path)
    assert result.record_path == f"docs/runs/{result.record_path.split('/')[-1]}"
    assert result.record_path.endswith(f"_{record.task_id}")
    log = (root / result.record_path / "run.log").read_text(encoding="utf-8").splitlines()
    assert len(log) > len(result.log_tail) == 3 and tuple(log[-3:]) == result.log_tail
    assert any(f"Task ID: {record.task_id}" in line for line in log)
    assert record.proof == proof and record.outcome == "completed" and record.exit_code == 0
    assert result.build == proof
    assert record.build_outcome == result.build_outcome == "ready"
    assert record.build_file_mismatches == result.build_file_mismatches == ()
    assert record.param_names == ("TOKEN",) and "s3cret" not in (root / result.record_path / "run.json").read_text()
    csv_file = next(artifact for artifact in record.outputs if artifact.path.endswith(".csv"))
    assert csv_file.path.startswith(f"output/{record.task_id}/")  # the output folder carries the task id of the record
    assert csv_file.sha256 == hashlib.sha256((root / csv_file.path).read_bytes()).hexdigest()
    assert not [item for item in result.artifacts if item.path.startswith("docs/")]


def test_a_second_run_writes_a_second_record_and_build_ignores_both(tmp_path: Path) -> None:
    root = project(tmp_path, "customers")
    application = create_authoring_application(root, descriptor_path=PROJECT_ENTRY_PATH)

    first = application.run_project(ProjectRunRequest(timeout_seconds=300))
    second = application.run_project(ProjectRunRequest(timeout_seconds=300))

    diagnostics = f"first={first.model_dump_json(indent=2)}\nsecond={second.model_dump_json(indent=2)}"
    assert first.record_path and second.record_path and first.record_path != second.record_path, diagnostics
    assert len(list((root / "docs" / "runs").iterdir())) == 2
    rebuilt = application.build()
    assert rebuilt.outcome == "ready", [str(item.code) for item in rebuilt.diagnostics]  # docs/ is no unread data


@pytest.mark.parametrize(
    "script,expected_outcome,expected_exit",
    [
        ("import sys; print('boom'); sys.exit(3)", "failed", 3),
        ("import time; print('start', flush=True); time.sleep(60)", "timeout", None),
    ],
)
def test_a_failed_or_timed_out_run_still_gets_a_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, script: str, expected_outcome: str, expected_exit: int | None
) -> None:
    import subprocess
    import sys

    from datamimic_ce.authoring.adapters import project_runner

    root = project(tmp_path, "customers")
    real_popen = subprocess.Popen

    def run_script(command, **kwargs):
        return real_popen([sys.executable, "-c", script], **kwargs)

    monkeypatch.setattr(
        project_runner,
        "subprocess",
        SimpleNamespace(
            Popen=run_script,
            DEVNULL=subprocess.DEVNULL,
            STDOUT=subprocess.STDOUT,
            TimeoutExpired=subprocess.TimeoutExpired,
        ),
    )

    run = project_runner.CeProjectRunner(AuthoringWorkspaceContext(root, PROJECT_ENTRY_PATH)).run((), 1)

    record = _record(root, run.record_path)
    assert record.exit_code == run.exit_code == expected_exit and record.proof is None
    assert record.build_outcome is None and record.build_file_mismatches is None
    assert record.outcome == expected_outcome
    assert run.timed_out is (expected_outcome == "timeout")
    assert (root / run.record_path / "run.log").read_text(encoding="utf-8").splitlines()[0] in {"boom", "start"}


@pytest.mark.parametrize("blocker", ["file", "link_out"])
def test_an_unwritable_record_folder_does_not_fail_the_run_and_says_so(
    tmp_path: Path, blocker: str, request: pytest.FixtureRequest
) -> None:
    root = project(tmp_path, "customers")
    outside = tmp_path / "outside"
    outside.mkdir()
    if blocker == "file":
        (root / "docs").write_text("not a folder", encoding="utf-8")
    else:
        request.getfixturevalue("require_symlinks")
        (root / "docs").symlink_to(outside, target_is_directory=True)

    result = create_authoring_application(root, descriptor_path=PROJECT_ENTRY_PATH).run_project(
        ProjectRunRequest(timeout_seconds=300)
    )

    assert result.outcome == "completed" and result.record_path is None
    assert [str(item.code) for item in result.diagnostics if item.severity == "warning"] == ["environment"]
    assert list(outside.iterdir()) == []  # nothing escaped the project


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes")
def test_the_full_log_is_private_to_the_user(tmp_path: Path) -> None:
    import stat

    root = project(tmp_path, "customers")
    result = create_authoring_application(root, descriptor_path=PROJECT_ENTRY_PATH).run_project(
        ProjectRunRequest(timeout_seconds=300)
    )

    assert result.record_path is not None
    assert stat.S_IMODE(os.stat(root / result.record_path / "run.log").st_mode) == 0o600


@pytest.mark.parametrize(("record_path", "says_so"), [(None, True), ("docs/runs/x", False)])
def test_an_unverified_run_says_when_no_record_was_written(record_path: str | None, says_so: bool) -> None:
    run = execution().model_copy(update={"record_path": record_path})
    result = ProjectRunWorkflow(
        lambda: RejectedBuild.from_input_error("x"), FakeEffects(()), FakeRunner(run)
    ).execute_unverified(ProjectRunRequest(allow_side_effects=True), True)

    assert ("No run record was written" in result.message) is says_so


@pytest.mark.parametrize(
    ("target", "shown"), [("mongo", "mongo -> accounts"), ("mongo.upsert", "mongo.upsert -> accounts")]
)
def test_a_mongodb_target_effect_names_the_collection(tmp_path: Path, target: str, shown: str) -> None:
    """A MongoDB write creates its collection by name. A typo in targetEntity must be visible before the run."""
    xml = (
        '<setup><mongodb id="mongo" host="localhost" port="27017" database="t"/>'
        f'<generate name="a" count="1" target="{target}" targetEntity="accounts">'
        '<key name="id" constant="1"/></generate></setup>'
    )
    assert (ExternalEffectKind.TARGET, shown) in effects_of(tmp_path, xml)
