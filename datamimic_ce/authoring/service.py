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

from pydantic import ValidationError

from datamimic_ce.authoring.acceptance import evaluate_acceptance
from datamimic_ce.authoring.compiler import CompileError, compile_authoring_spec
from datamimic_ce.authoring.contracts import (
    AuthoringStage,
    CapabilitiesRequest,
    CapabilitiesResult,
    CheckRequest,
    CompilePlan,
    IntentValidationIssue,
    IntentValidationIssueCode,
    ReferenceRequest,
    ReferenceResult,
    RunRequest,
    RunResult,
    ScaffoldRequest,
    ScaffoldResult,
    ScaffoldVerificationEvidence,
)
from datamimic_ce.authoring.derived_facts import derive_facts
from datamimic_ce.authoring.diagnostics import LintResult
from datamimic_ce.authoring.dryrun import (
    dry_run,
    dry_run_source,
    dry_run_source_captured,
)
from datamimic_ce.authoring.intent_linter import lint_intent
from datamimic_ce.authoring.intent_validation import project_validation_issues
from datamimic_ce.authoring.linter import lint_descriptor, lint_source
from datamimic_ce.authoring.spec import AuthoringSpecV1
from datamimic_ce.authoring.verification import (
    blocked_replay,
    blocked_verification,
    max_count_remediations,
    replay_evidence,
    replay_not_requested,
    smoke_export_evidence,
    unseeded_replay_evidence,
)


@dataclass(frozen=True)
class CompiledDocument:
    """Canonical validate-and-compile application result."""

    xml: str
    plan: CompilePlan
    spec: AuthoringSpecV1


class AuthoringDocumentError(ValueError):
    """A canonical intent validation or compilation failure."""

    def __init__(
        self,
        issues: tuple[IntentValidationIssue, ...],
    ) -> None:
        super().__init__("; ".join(issue.summary() for issue in issues))
        self.issues = issues


def compile_document(spec: dict[str, Any]) -> CompiledDocument:
    """Validate AuthoringSpecV1 and compile it through the canonical path."""

    try:
        authoring_spec = AuthoringSpecV1.model_validate(spec)
    except ValidationError as error:
        raise AuthoringDocumentError(project_validation_issues(error, spec)) from error
    try:
        compiled = compile_authoring_spec(authoring_spec)
    except CompileError as error:
        raise AuthoringDocumentError(
            (
                IntentValidationIssue(
                    path=("spec",),
                    code=IntentValidationIssueCode.CONSTRAINT_VIOLATION,
                    message=str(error),
                ),
            ),
        ) from error
    return CompiledDocument(
        xml=compiled.xml,
        plan=compiled.plan,
        spec=authoring_spec,
    )


def capabilities(request: CapabilitiesRequest | None = None) -> CapabilitiesResult:
    from datamimic_ce.authoring.reference import (
        capabilities_index,
        capabilities_manifest,
        capabilities_sections,
    )

    if request is None:
        request = CapabilitiesRequest()
    if request.mode == "compact":
        return CapabilitiesResult(capabilities_index())
    if request.mode == "full":
        return CapabilitiesResult(capabilities_manifest())
    return CapabilitiesResult(capabilities_sections(request.sections))


def reference(request: ReferenceRequest) -> ReferenceResult:
    from datamimic_ce.authoring.reference import reference as project_reference

    try:
        content = project_reference(request.topic, request.name, category=request.category, query=request.query)
    except ValueError as error:
        return ReferenceResult(
            ok=False,
            topic=request.topic,
            name=request.name,
            query=request.query,
            error=str(error),
        )
    return ReferenceResult(
        ok=True,
        topic=request.topic,
        name=request.name,
        query=request.query,
        content=content,
    )


def check(request: CheckRequest) -> LintResult:
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
            issues=list(error.issues),
            summary=None,
            truncated=False,
            verification=blocked_verification(
                request.verification,
                "Intent compilation failed before verification could run",
            ),
        )
    xml = compiled.xml
    derived_facts = derive_facts(compiled.plan)
    intent_diagnostics = lint_intent(compiled.spec)

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
            summary=failed_lint.summary() if failed_lint is not None else None,
            diagnostics=[*intent_diagnostics, *dry_run_result.diagnostics],
            truncated=bool(failed_lint.truncated) if failed_lint is not None else False,
            compile_plan=compiled.plan,
            derived_facts=derived_facts,
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
            summary=None,
            diagnostics=[*intent_diagnostics, *dry_run_result.diagnostics],
            products=dry_run_result.products,
            truncated=False,
            compile_plan=compiled.plan,
            derived_facts=derived_facts,
            verification=verification,
            verified=False,
        )

    acceptance = evaluate_acceptance(compiled.plan, compiled.spec, captured_run.captured)
    remediations = max_count_remediations(
        compiled.plan,
        captured_run.captured,
    )
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
    diagnostics = [*intent_diagnostics, *dry_run_result.diagnostics, *replay_diagnostics]
    return ScaffoldResult(
        ok=verification_passed,
        stage=(AuthoringStage.ACCEPTANCE if verification_passed else AuthoringStage.VERIFICATION),
        xml=xml,
        summary=None,
        diagnostics=diagnostics,
        products=dry_run_result.products,
        truncated=False,
        compile_plan=compiled.plan,
        derived_facts=derived_facts,
        acceptance=acceptance,
        remediations=remediations,
        verification=verification,
        verified=acceptance.verified and verification_passed,
    )
