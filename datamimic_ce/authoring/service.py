# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Application gateway for DATAMIMIC authoring operations.

CLI and MCP adapters call this module for descriptor checks, safe dry-runs, and
scaffolding. Low-level compiler, linter, and dry-run modules remain independently
testable implementation owners; orchestration belongs here.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from datamimic_ce.authoring.acceptance import evaluate_acceptance
from datamimic_ce.authoring.compiler import CompileError, compile_authoring_spec
from datamimic_ce.authoring.contracts import (
    AuthoringResponseFormat,
    AuthoringStage,
    CheckRequest,
    CheckResult,
    CompilePlan,
    IntentValidationIssue,
    IntentValidationIssueCode,
    RunRequest,
    RunResult,
    ScaffoldRequest,
    ScaffoldResult,
    ScaffoldVerificationEvidence,
)
from datamimic_ce.authoring.diagnostics import _diagnostic_dicts
from datamimic_ce.authoring.dryrun import dry_run, dry_run_source, dry_run_source_captured
from datamimic_ce.authoring.linter import lint_descriptor, lint_source
from datamimic_ce.authoring.normalization import normalize_authoring_spec
from datamimic_ce.authoring.spec import AuthoringSpecV1
from datamimic_ce.authoring.verification import (
    blocked_replay,
    blocked_verification,
    replay_evidence,
    replay_not_requested,
    smoke_export_evidence,
    unseeded_replay_evidence,
)


@dataclass(frozen=True)
class CompiledDocument:
    """Canonical normalize-and-compile application result."""

    xml: str
    plan: CompilePlan
    spec: AuthoringSpecV1
    normalization_notes: tuple[str, ...]


class AuthoringDocumentError(ValueError):
    """A normalize/compile failure with normalization evidence."""

    def __init__(
        self,
        issues: tuple[IntentValidationIssue, ...],
        notes: tuple[str, ...] = (),
    ) -> None:
        super().__init__("; ".join(issue.summary() for issue in issues))
        self.issues = issues
        self.notes = notes


def compile_document(spec: dict[str, Any]) -> CompiledDocument:
    """Normalize and compile through the single application-owned path."""

    normalized = normalize_authoring_spec(spec)
    if normalized.issues:
        raise AuthoringDocumentError(normalized.issues, normalized.notes)
    if normalized.spec is None:
        raise AuthoringDocumentError(
            (
                IntentValidationIssue(
                    path=("spec",),
                    code=IntentValidationIssueCode.CONSTRAINT_VIOLATION,
                    message="Normalization produced no authoring spec",
                ),
            ),
            normalized.notes,
        )
    try:
        compiled = compile_authoring_spec(normalized.spec)
    except CompileError as error:
        raise AuthoringDocumentError(
            (
                IntentValidationIssue(
                    path=("spec",),
                    code=IntentValidationIssueCode.CONSTRAINT_VIOLATION,
                    message=str(error),
                ),
            ),
            normalized.notes,
        ) from error
    return CompiledDocument(
        xml=compiled.xml,
        plan=compiled.plan,
        spec=normalized.spec,
        normalization_notes=normalized.notes,
    )


def check(request: CheckRequest) -> CheckResult:
    """Lint one inline or file-backed descriptor through the canonical linter."""
    if request.xml is not None:
        result = lint_source(request.xml, max_diagnostics=request.max_diagnostics)
    else:
        result = lint_descriptor(
            Path(str(request.path)),
            max_diagnostics=request.max_diagnostics,
        )
    return result


def run(request: RunRequest) -> RunResult:
    """Execute one safe dry-run through the canonical dry-run implementation."""
    if request.xml is not None:
        result = dry_run_source(
            request.xml,
            max_count=request.max_count,
            sample_rows=request.sample_rows,
            allow_side_effects=request.allow_side_effects,
            timeout_seconds=request.timeout_seconds,
            smoke_export=request.smoke_export,
        )
    else:
        result = dry_run(
            Path(str(request.path)),
            max_count=request.max_count,
            sample_rows=request.sample_rows,
            allow_side_effects=request.allow_side_effects,
            timeout_seconds=request.timeout_seconds,
            smoke_export=request.smoke_export,
        )
    return result


def scaffold(request: ScaffoldRequest) -> ScaffoldResult:
    """Compile, lint, run, accept and optionally verify one authoring intent."""
    try:
        compiled = compile_document(request.spec)
    except AuthoringDocumentError as error:
        return ScaffoldResult(
            ok=False,
            stage=AuthoringStage.RENDER,
            xml=None,
            error=str(error),
            issues=list(error.issues),
            summary=None,
            truncated=False,
            normalization_notes=list(error.notes),
            verification=blocked_verification(
                request.verification,
                "Intent compilation failed before verification could run",
            ),
        )
    xml = compiled.xml
    normalization_notes = list(compiled.normalization_notes)

    captured_run = dry_run_source_captured(
        xml,
        max_count=request.max_count,
        sample_rows=request.sample_rows,
        smoke_export=request.verification.smoke_export,
    )
    dry_run_result = captured_run.result
    if dry_run_result.stage is AuthoringStage.LINT:
        failed_lint = dry_run_result.lint
        return ScaffoldResult(
            ok=False,
            stage=AuthoringStage.LINT,
            xml=xml,
            error=None,
            summary=failed_lint.summary() if failed_lint is not None else None,
            diagnostics=_diagnostic_dicts(
                dry_run_result.diagnostics,
                detailed=request.response_format is AuthoringResponseFormat.DETAILED,
            ),
            truncated=bool(failed_lint.truncated) if failed_lint is not None else False,
            normalization_notes=normalization_notes,
            compile_plan=compiled.plan,
            verification=blocked_verification(
                request.verification,
                "Lint failed before verification could run",
            ),
        )

    smoke_evidence = smoke_export_evidence(
        request.verification.smoke_export,
        captured_run.smoke_export,
    )
    if not captured_run.base_run_ok:
        verification = ScaffoldVerificationEvidence(
            smoke_export=smoke_evidence,
            deterministic_replay=blocked_replay(
                request.verification,
                "The bounded run failed before replay could execute",
            ),
        )
        return ScaffoldResult(
            ok=False,
            stage=AuthoringStage.DRY_RUN,
            xml=xml,
            error=None,
            summary=None,
            diagnostics=_diagnostic_dicts(
                dry_run_result.diagnostics,
                detailed=request.response_format is AuthoringResponseFormat.DETAILED,
            ),
            products=dry_run_result.products,
            truncated=False,
            normalization_notes=normalization_notes,
            compile_plan=compiled.plan,
            verification=verification,
            verified=False,
        )

    acceptance = evaluate_acceptance(compiled.plan, compiled.spec, captured_run.captured)
    replay_run = None
    if not request.verification.deterministic_replay:
        replay_result = replay_not_requested()
    elif compiled.spec.seed is None:
        replay_result = unseeded_replay_evidence()
    else:
        replay_run = dry_run_source_captured(
            compiled.xml,
            max_count=request.max_count,
            sample_rows=request.sample_rows,
            smoke_export=False,
        )
        replay_result = replay_evidence(captured_run, replay_run)
    verification = ScaffoldVerificationEvidence(
        smoke_export=smoke_evidence,
        deterministic_replay=replay_result,
    )
    verification_passed = verification.gates_passed
    replay_diagnostics = replay_run.result.diagnostics if replay_run is not None else []
    diagnostics = [*dry_run_result.diagnostics, *replay_diagnostics]
    return ScaffoldResult(
        ok=verification_passed,
        stage=(
            AuthoringStage.ACCEPTANCE
            if verification_passed
            else AuthoringStage.VERIFICATION
        ),
        xml=xml,
        error=None,
        summary=None,
        diagnostics=_diagnostic_dicts(
            diagnostics,
            detailed=request.response_format is AuthoringResponseFormat.DETAILED,
        ),
        products=dry_run_result.products,
        truncated=False,
        normalization_notes=normalization_notes,
        compile_plan=compiled.plan,
        acceptance=acceptance,
        verification=verification,
        verified=acceptance.verified and verification_passed,
    )
