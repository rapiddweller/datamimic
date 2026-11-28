# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Run a project for its real output, only after Build proved it and only with the effects the caller allowed."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from datamimic_ce.authoring.domain.build_rules import catalog_diagnostic
from datamimic_ce.authoring.domain.diagnostics import (
    AuthoringRuleId,
    AuthoringSystemDiagnosticCode,
    Diagnostic,
    DiagnosticPhase,
)
from datamimic_ce.authoring.domain.project_run import (
    ExternalEffect,
    ExternalEffectKind,
    ProjectRunRequest,
    ProjectRunResult,
    UnverifiedProjectRunResult,
)
from datamimic_ce.authoring.domain.requests import BuildResult, ReadyBuild, ReadyWithGapsBuild
from datamimic_ce.authoring.ports import ExternalEffectsDetector, ProjectRunner


def _refusal_message(effects: tuple[ExternalEffect, ...]) -> str:
    """Name the files that run Python code: a hybrid project with one lib file is refused for that file alone."""
    scripts = sorted({effect.name for effect in effects if effect.kind is ExternalEffectKind.EXECUTE})
    parts: list[str] = []
    if scripts:
        # Operators only: a method call here would raise ArchKeel's unresolved-call count.
        inside = all(
            script != "inline" and script[:1] not in ("/", "\\") and ":" not in script and ".." not in script
            for script in scripts
        )
        parts.append(f"runs Python code from {', '.join(scripts)}" + (" (inside the project)" if inside else ""))
    if any(effect.kind is not ExternalEffectKind.EXECUTE for effect in effects):
        parts.append("reaches outside its directory")
    return f"The project {' and '.join(parts)}; nothing was run."


class ProjectRunWorkflow:
    def __init__(
        self, build: Callable[[], BuildResult], effects: ExternalEffectsDetector, runner: ProjectRunner
    ) -> None:
        self._build = build
        self._effects = effects
        self._runner = runner

    def execute_unverified(self, request: ProjectRunRequest, confirm_unverified: bool) -> UnverifiedProjectRunResult:
        if confirm_unverified is not True or not request.allow_side_effects:
            return UnverifiedProjectRunResult(
                outcome="not_run",
                message="Confirm the unverified run and allow side effects; nothing was run.",
            )
        execution = self._runner.run(request.params, request.timeout_seconds)
        outcome = execution.outcome
        message = "Build was not run. Execution does not verify the project or its effects."
        if outcome != "completed":
            message += " Effects may have partially persisted. Inspect the target state independently before retrying."
        if execution.record_path is None:
            message += " No run record was written below docs/runs/ of the project."
        return UnverifiedProjectRunResult(
            outcome=outcome,
            message=message,
            execution=execution,
        )

    def execute(self, request: ProjectRunRequest) -> ProjectRunResult:
        build = self._build()
        if not isinstance(build, (ReadyBuild, ReadyWithGapsBuild)):
            return ProjectRunResult(outcome="not_run", not_run_reason="build_rejected", build=build)
        outcome_name: Literal["ready", "ready_with_gaps"] = build.outcome
        action_required = build.action_required if isinstance(build, ReadyWithGapsBuild) else None
        effects = self._effects.effects()
        if effects and not request.allow_side_effects:
            return ProjectRunResult(
                outcome="not_run",
                not_run_reason="side_effects_not_allowed",
                build=build.artifact,
                build_outcome=outcome_name,
                coverage=build.coverage,
                action_required=action_required,
                required_side_effects=effects,
                diagnostics=(
                    catalog_diagnostic(
                        AuthoringRuleId.SIDE_EFFECT,
                        _refusal_message(effects),
                        phase=DiagnosticPhase.POLICY,
                        remediation="Ask the user to confirm the listed targets, then call again with "
                        "allow_side_effects true.",
                    ),
                    *tuple(item for item in build.diagnostics if item.severity == "warning"),
                ),
            )
        execution = self._runner.run(
            request.params, request.timeout_seconds, build.artifact, build_outcome=outcome_name
        )
        outcome = execution.outcome
        diagnostics: tuple[Diagnostic, ...] = tuple(item for item in build.diagnostics if item.severity == "warning")
        if outcome != "completed":
            diagnostics += (
                Diagnostic(
                    code=AuthoringSystemDiagnosticCode.CHILD_EXECUTION,
                    phase=DiagnosticPhase.EVIDENCE,
                    message="The project run timed out." if outcome == "timeout" else "The project run failed.",
                    remediation="Read log_tail, repair the project, then run Build again.",
                ),
            )
        if execution.record_path is None:
            diagnostics += (
                Diagnostic(
                    code=AuthoringSystemDiagnosticCode.ENVIRONMENT,
                    phase=DiagnosticPhase.EVIDENCE,
                    severity="warning",
                    message="The run record could not be written below docs/runs/ of the project.",
                    remediation="Make docs/ writable inside the project; this run has no record or full log on disk.",
                ),
            )
        return ProjectRunResult(
            outcome=outcome,
            exit_code=execution.exit_code,
            duration_seconds=execution.duration_seconds,
            build=build.artifact,
            build_outcome=outcome_name,
            build_file_mismatches=execution.build_file_mismatches,
            coverage=build.coverage,
            action_required=action_required,
            artifacts=execution.artifacts,
            artifact_count=execution.artifact_count,
            log_tail=execution.log_tail,
            record_path=execution.record_path,
            diagnostics=diagnostics,
        )
