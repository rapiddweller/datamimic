"""CE verification guarantees survive the scaffold-to-Build migration."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring import create_authoring_application
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
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId, DiagnosticPhase
from datamimic_ce.authoring.domain.proof import ReplayMismatchKind, VerificationGateStatus
from datamimic_ce.authoring.domain.requests import (
    BoundedExecutionEvidence,
    BuildRequestV4,
    LintResult,
    ReadyBuild,
    RejectedBuild,
)
from datamimic_ce.interfaces.cli import app


def _request(*, seed: int | None = 7, count: int = 2, exporter: bool = True, **options) -> BuildRequestV4:
    properties = {"name": "items", "count": count}
    if exporter:
        properties["target"] = "JSON"
    return BuildRequestV4.model_validate(
        {
            "document": {
                "root": {
                    "kind": "setup",
                    "properties": {"rng_seed": seed} if seed is not None else {},
                    "children": [
                        {
                            "kind": "generate",
                            "properties": properties,
                            "children": [
                                {"kind": "key", "properties": {"name": "id", "generator": "IncrementGenerator"}},
                            ],
                        },
                    ],
                }
            },
            **options,
        }
    )


def _captured(*, rows=({"id": 1}, {"id": 2}), ok=True, base_run_ok=True, smoke=None) -> BoundedExecutionEvidence:
    provenance = ProductCaptureEvidence(
        status=CaptureStatus.COMPLETE,
        requested=len(rows),
        observed=len(rows),
        limit=10,
        reason="Complete controlled executor-port capture",
    )
    return BoundedExecutionEvidence(
        ok=ok,
        base_run_ok=base_run_ok,
        captured=CapturedProducts((CapturedProduct("items", tuple(rows), provenance),), 10),
        smoke_export=smoke or SmokeExportCapture.not_requested(),
    )


@pytest.fixture
def executions(monkeypatch):
    original = CeBoundedExecutor.execute
    calls = []

    def recorded(executor, request):
        calls.append(request)
        return original(executor, request)

    monkeypatch.setattr(CeBoundedExecutor, "execute", recorded)
    return calls


def test_default_build_uses_one_real_capture_and_unrequested_gates(tmp_path: Path, executions) -> None:
    result = create_authoring_application(workspace_root=tmp_path).build(_request())
    assert isinstance(result, ReadyBuild), result
    assert len(executions) == 1
    assert result.verification.smoke_export.status is VerificationGateStatus.NOT_REQUESTED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.NOT_REQUESTED


def test_smoke_reuses_first_capture_and_real_json_exporter(tmp_path: Path, executions) -> None:
    result = create_authoring_application(workspace_root=tmp_path).build(_request(verification={"smoke_export": True}))
    assert isinstance(result, ReadyBuild), result
    assert [request.smoke_export for request in executions] == [True]
    smoke = result.verification.smoke_export
    assert smoke.status is VerificationGateStatus.PASSED
    assert (smoke.applicable_exporters, smoke.attempted_exporters, smoke.failed_exporters) == (1, 1, 0)
    assert not list(tmp_path.iterdir()), "Bounded smoke must not write project artifacts."


def test_requested_smoke_without_exporter_is_not_applicable(tmp_path: Path) -> None:
    result = create_authoring_application(workspace_root=tmp_path).build(
        _request(exporter=False, verification={"smoke_export": True})
    )
    assert isinstance(result, ReadyBuild), result
    assert result.verification.smoke_export.status is VerificationGateStatus.NOT_APPLICABLE
    assert result.verification.smoke_export.applicable_exporters == 0


def test_smoke_failure_cannot_be_masked_by_passing_acceptance(tmp_path: Path, monkeypatch) -> None:
    failed = _captured(ok=False, smoke=SmokeExportCapture(True, 1, 1, 1))
    monkeypatch.setattr(CeBoundedExecutor, "execute", lambda executor, request: failed)
    result = create_authoring_application(workspace_root=tmp_path).build(_request(verification={"smoke_export": True}))
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
    result = create_authoring_application(workspace_root=tmp_path).build(
        _request(verification={"smoke_export": True, "deterministic_replay": True})
    )
    assert isinstance(result, RejectedBuild)
    assert len(calls) == 1
    expected = VerificationGateStatus.FAILED if smoke_failed else VerificationGateStatus.BLOCKED
    assert result.verification.smoke_export.status is expected
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED


def test_compile_failure_blocks_requested_gates_without_execution(tmp_path: Path, executions) -> None:
    request = BuildRequestV4.model_validate(
        {
            "document": {
                "root": {
                    "kind": "setup",
                    "children": [
                        {"kind": "unknown-element"},
                    ],
                }
            },
            "verification": {"smoke_export": True, "deterministic_replay": True},
        }
    )
    result = create_authoring_application(workspace_root=tmp_path).build(request)
    assert isinstance(result, RejectedBuild)
    assert result.phase is DiagnosticPhase.COMPILE
    assert executions == []
    assert result.verification.smoke_export.status is VerificationGateStatus.BLOCKED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED


def test_lint_failure_blocks_requested_gates_without_execution(tmp_path: Path, monkeypatch, executions) -> None:
    diagnostic = catalog_diagnostic(
        AuthoringRuleId.VALIDATION, "Controlled validation failure.", phase=DiagnosticPhase.XML
    )
    monkeypatch.setattr(
        CeDescriptorValidator,
        "validate",
        lambda validator, xml, **kwargs: LintResult(ok=False, diagnostics=(diagnostic,)),
    )
    result = create_authoring_application(workspace_root=tmp_path).build(
        _request(verification={"smoke_export": True, "deterministic_replay": True})
    )
    assert isinstance(result, RejectedBuild)
    assert result.phase is DiagnosticPhase.XML
    assert executions == []
    assert result.verification.smoke_export.status is VerificationGateStatus.BLOCKED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED


def test_replay_checks_complete_rows_beyond_response_samples(tmp_path: Path, monkeypatch) -> None:
    captures = iter((_captured(), _captured(rows=({"id": 1}, {"id": 99}))))
    calls = []

    def execute(executor, request):
        calls.append(request)
        return next(captures)

    monkeypatch.setattr(CeBoundedExecutor, "execute", execute)
    result = create_authoring_application(workspace_root=tmp_path).build(
        _request(sample_rows=1, verification={"deterministic_replay": True})
    )
    assert isinstance(result, RejectedBuild)
    assert len(result.evidence[0].rows) == 1
    assert len(calls) == 2
    replay = result.verification.deterministic_replay
    assert replay.status is VerificationGateStatus.FAILED
    assert (replay.compared_products, replay.compared_rows) == (1, 2)
    assert replay.mismatches[0].kind is ReplayMismatchKind.ROW_CONTENT
    assert replay.mismatches[0].first_difference == 1


def test_seeded_replay_runs_exactly_twice_and_passes(tmp_path: Path, executions) -> None:
    result = create_authoring_application(workspace_root=tmp_path).build(
        _request(sample_rows=1, verification={"deterministic_replay": True})
    )
    assert isinstance(result, ReadyBuild), result
    assert len(executions) == 2
    assert len(result.evidence[0].rows) == 1
    replay = result.verification.deterministic_replay
    assert replay.status is VerificationGateStatus.PASSED
    assert (replay.compared_products, replay.compared_rows) == (1, 2)


def test_unseeded_replay_fails_without_claiming_comparison(tmp_path: Path, executions) -> None:
    result = create_authoring_application(workspace_root=tmp_path).build(
        _request(seed=None, verification={"deterministic_replay": True})
    )
    assert isinstance(result, RejectedBuild)
    assert len(executions) == 1
    replay = result.verification.deterministic_replay
    assert replay.status is VerificationGateStatus.FAILED
    assert replay.compared_rows == 0
    assert "explicit" in replay.reason


def test_capped_acceptance_cannot_be_rescued_by_replay(tmp_path: Path, executions) -> None:
    result = create_authoring_application(workspace_root=tmp_path).build(
        _request(max_count=1, sample_rows=1, verification={"deterministic_replay": True})
    )
    assert isinstance(result, RejectedBuild)
    assert result.phase is DiagnosticPhase.EVIDENCE
    assert len(executions) == 1
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED
    assert 'count="2"' in result.review_artifact.compiled_xml


def test_cli_application_byte_parity_for_smoke_and_replay(tmp_path: Path) -> None:
    request = _request(sample_rows=1, verification={"smoke_export": True, "deterministic_replay": True})
    expected = create_authoring_application(workspace_root=tmp_path).build(request)
    assert isinstance(expected, ReadyBuild), expected
    result = CliRunner().invoke(
        app,
        ["authoring", "build", "-", "--workspace-root", str(tmp_path)],
        input=request.model_dump_json(exclude_none=True),
    )
    assert result.exit_code == 0, result.stdout
    assert result.stdout.strip() == expected.model_dump_json(indent=2, exclude_none=True)


def test_missing_memstore_identity_proof_blocks_gates_before_execution(tmp_path: Path, executions) -> None:
    payload = json.loads(_request(exporter=False).model_dump_json())
    root = payload["document"]["root"]
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
    payload["verification"] = {"smoke_export": True, "deterministic_replay": True}
    result = create_authoring_application(workspace_root=tmp_path).build(BuildRequestV4.model_validate(payload))
    assert isinstance(result, RejectedBuild)
    assert result.phase is DiagnosticPhase.EXPECTATION
    assert executions == []
    assert result.verification.smoke_export.status is VerificationGateStatus.BLOCKED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED
