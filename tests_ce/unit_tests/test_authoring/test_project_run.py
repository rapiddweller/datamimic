"""Running a project for its real output: Build first, effects refused unless allowed."""

import csv
import json
import shutil
from pathlib import Path

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
    ProjectRunRequest,
)
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, BuildResult, RejectedBuild

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

    def run(self, params: tuple[ProjectParam, ...], timeout_seconds: int) -> ProjectRunExecution:
        self.calls.append(params)
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


def ready_build(tmp_path: Path):
    return create_authoring_application(project(tmp_path, "customers"), descriptor_path=PROJECT_ENTRY_PATH).build()


def test_rejected_build_stops_before_any_run(tmp_path: Path) -> None:
    runner = FakeRunner(execution())
    rejected = RejectedBuild.from_input_error("broken")
    result = workflow(rejected, (), runner).execute(ProjectRunRequest())
    assert result.outcome == "not_run" and result.build == rejected
    assert runner.calls == []
    assert result.not_run_reason == "build_rejected"


def test_a_build_with_open_coverage_gaps_still_runs(tmp_path: Path) -> None:
    root = project(tmp_path, "customers")
    entry = root / PROJECT_ENTRY_PATH
    entry.write_text(entry.read_text(encoding="utf-8").replace(' rngSeed="7"', ""), encoding="utf-8")
    build = create_authoring_application(root, descriptor_path=PROJECT_ENTRY_PATH).build()
    runner = FakeRunner(execution())

    result = workflow(build, (), runner).execute(ProjectRunRequest())

    assert build.outcome == "ready_with_gaps", build
    assert result.outcome == "completed"
    assert len(runner.calls) == 1
    assert result.build_outcome == "ready_with_gaps"
    assert result.coverage is not None and not result.coverage.seeded
    assert result.action_required == build.action_required
    assert "seeded" in (result.action_required or "")


def test_run_preserves_build_warning_diagnostics(tmp_path: Path) -> None:
    root = project(tmp_path, "customers")
    entry = root / PROJECT_ENTRY_PATH
    entry.write_text(entry.read_text(encoding="utf-8").replace(' rngSeed="7"', ""), encoding="utf-8")
    build = create_authoring_application(root, descriptor_path=PROJECT_ENTRY_PATH).build()
    assert any(item.severity == "warning" for item in build.diagnostics)

    result = workflow(build, (), FakeRunner(execution())).execute(ProjectRunRequest())

    warnings = tuple(item for item in build.diagnostics if item.severity == "warning")
    assert all(item in result.diagnostics for item in warnings)


def test_a_clean_ready_run_carries_the_outcome_and_no_action(tmp_path: Path) -> None:
    result = workflow(ready_build(tmp_path), (), FakeRunner(execution())).execute(ProjectRunRequest())

    assert result.outcome == "completed"
    assert result.build_outcome == "ready"
    assert result.coverage is not None and not result.coverage.has_gaps
    assert result.action_required is None


def test_effects_without_the_flag_are_listed_and_nothing_runs(tmp_path: Path) -> None:
    runner = FakeRunner(execution())
    result = workflow(ready_build(tmp_path), (EFFECT,), runner).execute(ProjectRunRequest())
    assert result.outcome == "not_run" and result.required_side_effects == (EFFECT,)
    assert result.not_run_reason == "side_effects_not_allowed"
    assert result.diagnostics[0].code.value == "side_effect"
    assert runner.calls == []


def test_allowed_effects_run_and_params_reach_the_runner(tmp_path: Path) -> None:
    runner = FakeRunner(execution())
    request = ProjectRunRequest(allow_side_effects=True, params=(ProjectParam(name="STAGE", value="test"),))
    result = workflow(ready_build(tmp_path), (EFFECT,), runner).execute(request)
    assert result.outcome == "completed" and result.exit_code == 0
    assert runner.calls == [(ProjectParam(name="STAGE", value="test"),)]


@pytest.mark.parametrize("run,outcome", [(execution(3), "failed"), (execution(None, timed_out=True), "timeout")])
def test_failed_and_timed_out_runs_carry_a_diagnostic(tmp_path: Path, run: ProjectRunExecution, outcome: str) -> None:
    result = workflow(ready_build(tmp_path), (), FakeRunner(run)).execute(ProjectRunRequest())
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

    monkeypatch.setattr(project_runner.subprocess, "Popen", slow)
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
