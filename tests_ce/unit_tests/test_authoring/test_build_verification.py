"""CE verification guarantees survive the scaffold-to-Build migration."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.adapters.validator import CeDescriptorValidator
from datamimic_ce.authoring.domain.build_rules import catalog_diagnostic
from datamimic_ce.authoring.domain.capture import (
    CapturedProduct,
    CapturedProducts,
    CaptureStatus,
    ProductCaptureEvidence,
    SmokeExportCapture,
)
from datamimic_ce.authoring.domain.coverage import CoverageGapKind
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId, DiagnosticPhase
from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1
from datamimic_ce.authoring.domain.proof import ReplayMismatchKind, VerificationGateStatus
from datamimic_ce.authoring.domain.requests import (
    BoundedExecutionEvidence,
    BoundedExecutionStatus,
    LintResult,
    ReadyBuild,
    ReadyWithGapsBuild,
    RejectedBuild,
)
from datamimic_ce.interfaces.cli import app
from tests_ce.authoring_project import build_document, build_project


def _captured(*, rows=({"id": 1}, {"id": 2}), ok=True, base_run_ok=True, smoke=None) -> BoundedExecutionEvidence:
    provenance = ProductCaptureEvidence(
        status=CaptureStatus.COMPLETE,
        requested=len(rows),
        observed=len(rows),
        limit=10,
        reason="Complete controlled executor-port capture",
    )
    return BoundedExecutionEvidence(
        status=(
            BoundedExecutionStatus.FAILED
            if not base_run_ok
            else BoundedExecutionStatus.PASSED
            if ok
            else BoundedExecutionStatus.SMOKE_FAILED
        ),
        captured=CapturedProducts((CapturedProduct("items", tuple(rows), provenance),), 10),
        smoke_export=smoke or SmokeExportCapture.not_requested(),
    )


@pytest.fixture
def controlled_executions(monkeypatch):
    calls = []

    def execute(executor, request):
        calls.append(request)
        return _captured()

    monkeypatch.setattr(CeBoundedExecutor, "execute", execute)
    return calls


def test_default_build_uses_one_capture_and_unrequested_gates(tmp_path: Path, controlled_executions) -> None:
    result = build_project(tmp_path, build_document(seed=None))
    assert isinstance(result, ReadyWithGapsBuild), result
    assert result.coverage.open_gaps == (CoverageGapKind.SEEDED,)
    assert len(controlled_executions) == 1
    assert result.verification.smoke_export.status is VerificationGateStatus.NOT_REQUESTED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.NOT_REQUESTED


def test_smoke_failure_cannot_be_masked_by_passing_acceptance(tmp_path: Path, monkeypatch) -> None:
    failed = _captured(ok=False, smoke=SmokeExportCapture(True, 1, 1, 1))
    monkeypatch.setattr(CeBoundedExecutor, "execute", lambda executor, request: failed)
    result = build_project(tmp_path, build_document(), verification={"smoke_export": True})
    assert isinstance(result, RejectedBuild)
    assert result.phase is DiagnosticPhase.EVIDENCE
    assert result.verification.smoke_export.status is VerificationGateStatus.FAILED
    assert result.evidence[0].count == 2


@pytest.mark.parametrize("smoke_failed", [False, True], ids=["base_failure", "base_and_smoke_failure"])
def test_base_failure_preserves_exact_smoke_status_and_blocks_replay(tmp_path: Path, monkeypatch, smoke_failed) -> None:
    smoke = SmokeExportCapture(True, 1, 1, 1) if smoke_failed else SmokeExportCapture.not_requested()
    failed = _captured(ok=False, base_run_ok=False, smoke=smoke)
    calls = []

    def execute(executor, request):
        calls.append(request)
        return failed

    monkeypatch.setattr(CeBoundedExecutor, "execute", execute)
    result = build_project(
        tmp_path, build_document(), verification={"smoke_export": True, "deterministic_replay": True}
    )
    assert isinstance(result, RejectedBuild)
    assert len(calls) == 1
    expected = VerificationGateStatus.FAILED if smoke_failed else VerificationGateStatus.BLOCKED
    assert result.verification.smoke_export.status is expected
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED


def test_unknown_element_blocks_requested_gates_without_execution(tmp_path: Path, build_executions) -> None:
    result = build_project(
        tmp_path,
        "<setup><unknown-element/></setup>",
        verification={"smoke_export": True, "deterministic_replay": True},
    )
    assert isinstance(result, RejectedBuild)
    assert result.phase is DiagnosticPhase.XML
    assert build_executions == []
    assert result.verification.smoke_export.status is VerificationGateStatus.BLOCKED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED


def test_lint_failure_blocks_requested_gates_without_execution(tmp_path: Path, monkeypatch, build_executions) -> None:
    diagnostic = catalog_diagnostic(
        AuthoringRuleId.VALIDATION, "Controlled validation failure.", phase=DiagnosticPhase.XML
    )
    monkeypatch.setattr(
        CeDescriptorValidator,
        "validate",
        lambda validator, xml, **kwargs: LintResult(ok=False, diagnostics=(diagnostic,)),
    )
    result = build_project(
        tmp_path, build_document(), verification={"smoke_export": True, "deterministic_replay": True}
    )
    assert isinstance(result, RejectedBuild)
    assert result.phase is DiagnosticPhase.XML
    assert build_executions == []
    assert result.verification.smoke_export.status is VerificationGateStatus.BLOCKED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED


def test_replay_checks_complete_rows_beyond_response_samples(tmp_path: Path, monkeypatch) -> None:
    captures = iter((_captured(), _captured(rows=({"id": 1}, {"id": 99}))))
    calls = []

    def execute(executor, request):
        calls.append(request)
        return next(captures)

    monkeypatch.setattr(CeBoundedExecutor, "execute", execute)
    result = build_project(tmp_path, build_document(), sample_rows=1, verification={"deterministic_replay": True})
    assert isinstance(result, RejectedBuild)
    assert len(result.evidence[0].rows) == 1
    assert len(calls) == 2
    replay = result.verification.deterministic_replay
    assert replay.status is VerificationGateStatus.FAILED
    assert (replay.compared_products, replay.compared_rows) == (1, 2)
    assert replay.mismatches[0].kind is ReplayMismatchKind.ROW_CONTENT
    assert replay.mismatches[0].first_difference == 1


def test_seeded_replay_runs_once_per_hash_seed_and_passes(tmp_path: Path, controlled_executions) -> None:
    result = build_project(tmp_path, build_document(), sample_rows=1, verification={"deterministic_replay": True})
    assert isinstance(result, ReadyBuild), result
    assert [request.hash_seed for request in controlled_executions] == [1, 2, 3, 4]
    assert len(result.evidence[0].rows) == 1
    replay = result.verification.deterministic_replay
    assert replay.status is VerificationGateStatus.PASSED
    assert (replay.compared_products, replay.compared_rows) == (1, 2)


def test_unseeded_replay_fails_without_claiming_comparison(tmp_path: Path, controlled_executions) -> None:
    result = build_project(tmp_path, build_document(seed=None), verification={"deterministic_replay": True})
    assert isinstance(result, RejectedBuild)
    assert len(controlled_executions) == 1
    replay = result.verification.deterministic_replay
    assert replay.status is VerificationGateStatus.FAILED
    assert replay.compared_rows == 0
    assert "explicit" in replay.reason


def test_cli_application_byte_parity_for_smoke_and_replay(tmp_path: Path, monkeypatch) -> None:
    calls = []
    smoke = SmokeExportCapture(True, 1, 1, 0)

    def execute(executor, request):
        calls.append((request.hash_seed, request.smoke_export))
        return _captured(smoke=smoke if request.smoke_export else None)

    monkeypatch.setattr(CeBoundedExecutor, "execute", execute)
    expected = build_project(
        tmp_path, build_document(), sample_rows=1, verification={"smoke_export": True, "deterministic_replay": True}
    )
    assert isinstance(expected, ReadyBuild), expected
    result = CliRunner().invoke(app, ["authoring", "build", str(tmp_path)])
    assert result.exit_code == 0, result.stdout
    assert result.stdout.strip() == expected.model_dump_json(indent=2)
    assert calls == [(1, True), (2, False), (3, False), (4, False)] * 2


def test_missing_memstore_identity_proof_blocks_gates_before_execution(tmp_path: Path, build_executions) -> None:
    document = build_document(exporter=False).model_dump(mode="json")
    root = document["root"]
    root["children"][0]["properties"]["target"] = "store"
    root["children"].insert(0, {"kind": "memstore", "properties": {"id": "store"}})
    root["children"].append(
        {
            "kind": "generate",
            "properties": {
                "name": "readback",
                "source": "store",
                "type": "items",
                "distribution": "ordered",
            },
            "children": [{"kind": "key", "properties": {"name": "id", "script": "this.id"}}],
        }
    )
    result = build_project(
        tmp_path,
        DmJsonDocumentV1.model_validate(document),
        verification={"smoke_export": True, "deterministic_replay": True},
    )
    assert isinstance(result, RejectedBuild)
    assert result.phase is DiagnosticPhase.EXPECTATION
    assert build_executions == []
    assert result.verification.smoke_export.status is VerificationGateStatus.BLOCKED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED
