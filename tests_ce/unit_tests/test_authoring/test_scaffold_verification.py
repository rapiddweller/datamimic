# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

"""Canonical scaffold verification gates and transport parity."""

import json

from typer.testing import CliRunner

import datamimic_ce.authoring.service as service_module
from datamimic_ce.authoring.contracts import (
    AuthoringStage,
    CaptureStatus,
    ProductCaptureEvidence,
    ReplayMismatchKind,
    RunResult,
    ScaffoldRequest,
    ScaffoldVerification,
    VerificationGateStatus,
)
from datamimic_ce.authoring.diagnostics import Diagnostic, LintResult
from datamimic_ce.authoring.dryrun import (
    CapturedProduct,
    CapturedProducts,
    CapturedRun,
    SmokeExportCapture,
)
from datamimic_ce.authoring.service import scaffold
from datamimic_ce.cli import app
from datamimic_ce.authoring.rule_catalog import RuleSeverity


def _spec(*, seed: int | None = 7, count: int = 2) -> dict[str, object]:
    payload: dict[str, object] = {
        "version": "1",
        "products": [
            {
                "kind": "generated",
                "name": "items",
                "count": count,
                "fields": [{"kind": "increment", "name": "id"}],
                "targets": [{"kind": "file_export", "format": "JSON"}],
            }
        ],
    }
    if seed is not None:
        payload["seed"] = seed
    return payload


def _captured_run(
    rows: tuple[dict[str, int], ...],
    *,
    smoke_export: SmokeExportCapture | None = None,
    ok: bool = True,
    base_run_ok: bool = True,
) -> CapturedRun:
    capture = ProductCaptureEvidence(
        status=CaptureStatus.COMPLETE,
        requested=len(rows),
        observed=len(rows),
        limit=10,
        reason="test capture is complete",
    )
    diagnostics = []
    if not ok:
        diagnostics.append(
            Diagnostic(
                rule="DM002",
                severity=RuleSeverity.ERROR,
                message="Captured execution diagnostic",
                fix_hint="Use the typed run evidence to classify this failure",
                element="generate",
                path="/setup",
            )
        )
    return CapturedRun(
        result=RunResult(
            ok=ok,
            stage=AuthoringStage.RUN,
            diagnostics=diagnostics,
        ),
        captured=CapturedProducts(
            products=(CapturedProduct("items", rows, capture),),
            max_count=10,
        ),
        base_run_ok=base_run_ok,
        smoke_export=smoke_export or SmokeExportCapture.not_requested(),
    )


def test_default_scaffold_calls_captured_runner_once(monkeypatch) -> None:
    calls = 0
    original = service_module.dry_run_source_captured

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(service_module, "dry_run_source_captured", counted)

    result = scaffold(ScaffoldRequest(spec=_spec()))

    assert calls == 1
    assert result.verified
    assert result.verification.smoke_export.status is VerificationGateStatus.NOT_REQUESTED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.NOT_REQUESTED


def test_smoke_export_reuses_first_capture_and_real_json_exporter_passes(monkeypatch) -> None:
    calls: list[bool] = []
    original = service_module.dry_run_source_captured

    def counted(*args, **kwargs):
        calls.append(kwargs["smoke_export"])
        return original(*args, **kwargs)

    monkeypatch.setattr(service_module, "dry_run_source_captured", counted)

    result = scaffold(
        ScaffoldRequest(
            spec=_spec(),
            verification=ScaffoldVerification(smoke_export=True),
        )
    )

    assert calls == [True]
    assert result.verified
    assert result.verification.smoke_export.status is VerificationGateStatus.PASSED
    assert result.verification.smoke_export.applicable_exporters == 1
    assert result.verification.smoke_export.attempted_exporters == 1
    assert result.verification.smoke_export.failed_exporters == 0


def test_requested_smoke_without_file_exporter_is_not_applicable() -> None:
    spec = _spec()
    products = spec["products"]
    assert isinstance(products, list)
    product = products[0]
    assert isinstance(product, dict)
    product["targets"] = []

    result = scaffold(
        ScaffoldRequest(
            spec=spec,
            verification=ScaffoldVerification(smoke_export=True),
        )
    )

    assert result.verified
    assert result.verification.smoke_export.status is VerificationGateStatus.NOT_APPLICABLE
    assert result.verification.smoke_export.applicable_exporters == 0


def test_smoke_export_failure_is_not_masked(monkeypatch) -> None:
    failed = _captured_run(
        ({"id": 1}, {"id": 2}),
        smoke_export=SmokeExportCapture(
            requested=True,
            applicable_exporters=1,
            attempted_exporters=1,
            failed_exporters=1,
        ),
        ok=False,
    )
    monkeypatch.setattr(
        service_module,
        "dry_run_source_captured",
        lambda *_args, **_kwargs: failed,
    )

    result = scaffold(
        ScaffoldRequest(
            spec=_spec(),
            verification=ScaffoldVerification(smoke_export=True),
        )
    )

    assert not result.ok
    assert not result.verified
    assert result.stage is AuthoringStage.VERIFICATION
    assert result.acceptance is not None and result.acceptance.verified
    assert result.verification.smoke_export.status is VerificationGateStatus.FAILED


def test_base_run_failure_blocks_requested_gates_and_keeps_dry_run_stage(monkeypatch) -> None:
    failed = _captured_run(
        ({"id": 1}, {"id": 2}),
        ok=False,
        base_run_ok=False,
    )
    monkeypatch.setattr(
        service_module,
        "dry_run_source_captured",
        lambda *_args, **_kwargs: failed,
    )

    result = scaffold(
        ScaffoldRequest(
            spec=_spec(),
            verification=ScaffoldVerification(
                smoke_export=True,
                deterministic_replay=True,
            ),
        )
    )

    assert result.stage is AuthoringStage.DRY_RUN
    assert not result.ok and not result.verified
    assert result.verification.smoke_export.status is VerificationGateStatus.BLOCKED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED


def test_base_and_smoke_failure_keep_base_stage_with_exact_gate_evidence(monkeypatch) -> None:
    failed = _captured_run(
        ({"id": 1}, {"id": 2}),
        smoke_export=SmokeExportCapture(
            requested=True,
            applicable_exporters=1,
            attempted_exporters=1,
            failed_exporters=1,
        ),
        ok=False,
        base_run_ok=False,
    )
    monkeypatch.setattr(
        service_module,
        "dry_run_source_captured",
        lambda *_args, **_kwargs: failed,
    )

    result = scaffold(
        ScaffoldRequest(
            spec=_spec(),
            verification=ScaffoldVerification(
                smoke_export=True,
                deterministic_replay=True,
            ),
        )
    )

    assert result.stage is AuthoringStage.DRY_RUN
    assert not result.ok and not result.verified
    assert result.verification.smoke_export.status is VerificationGateStatus.FAILED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED


def test_render_failure_blocks_requested_gates() -> None:
    result = scaffold(
        ScaffoldRequest(
            spec={},
            verification=ScaffoldVerification(
                smoke_export=True,
                deterministic_replay=True,
            ),
        )
    )

    assert result.stage is AuthoringStage.RENDER
    assert result.verification.smoke_export.status is VerificationGateStatus.BLOCKED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED


def test_lint_failure_blocks_requested_gates(monkeypatch) -> None:
    diagnostic = Diagnostic(
        rule="DM001",
        severity=RuleSeverity.ERROR,
        message="Lint failed",
        fix_hint="Fix the descriptor",
        element="setup",
        path="/setup",
    )
    lint = LintResult(ok=False, diagnostics=[diagnostic])
    failed = CapturedRun(
        result=RunResult(
            ok=False,
            stage=AuthoringStage.LINT,
            lint=lint,
            diagnostics=[diagnostic],
        ),
        captured=CapturedProducts(products=(), max_count=10),
        base_run_ok=False,
    )
    monkeypatch.setattr(
        service_module,
        "dry_run_source_captured",
        lambda *_args, **_kwargs: failed,
    )

    result = scaffold(
        ScaffoldRequest(
            spec=_spec(),
            verification=ScaffoldVerification(
                smoke_export=True,
                deterministic_replay=True,
            ),
        )
    )

    assert result.stage is AuthoringStage.LINT
    assert result.verification.smoke_export.status is VerificationGateStatus.BLOCKED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED


def test_replay_compares_complete_rows_beyond_sample_projection(monkeypatch) -> None:
    runs = iter(
        (
            _captured_run(({"id": 1}, {"id": 2})),
            _captured_run(({"id": 1}, {"id": 99})),
        )
    )
    calls = 0

    def next_run(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return next(runs)

    monkeypatch.setattr(service_module, "dry_run_source_captured", next_run)

    result = scaffold(
        ScaffoldRequest(
            spec=_spec(),
            sample_rows=1,
            verification=ScaffoldVerification(deterministic_replay=True),
        )
    )

    assert calls == 2
    assert not result.ok
    assert not result.verified
    assert result.stage is AuthoringStage.VERIFICATION
    replay = result.verification.deterministic_replay
    assert replay.status is VerificationGateStatus.FAILED
    assert replay.compared_products == 1
    assert replay.compared_rows == 2
    assert replay.mismatches[0].kind is ReplayMismatchKind.ROW_CONTENT
    assert replay.mismatches[0].first_difference == 1


def test_seeded_replay_passes_and_runs_canonical_capture_twice(monkeypatch) -> None:
    calls = 0
    original = service_module.dry_run_source_captured

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(service_module, "dry_run_source_captured", counted)

    result = scaffold(
        ScaffoldRequest(
            spec=_spec(),
            sample_rows=1,
            verification=ScaffoldVerification(deterministic_replay=True),
        )
    )

    assert calls == 2
    assert result.verified
    replay = result.verification.deterministic_replay
    assert replay.status is VerificationGateStatus.PASSED
    assert replay.compared_products == 1
    assert replay.compared_rows == 2


def test_unseeded_replay_fails_closed_without_claiming_a_comparison(monkeypatch) -> None:
    calls = 0
    original = service_module.dry_run_source_captured

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(service_module, "dry_run_source_captured", counted)

    result = scaffold(
        ScaffoldRequest(
            spec=_spec(seed=None),
            verification=ScaffoldVerification(deterministic_replay=True),
        )
    )

    assert calls == 1
    assert not result.verified
    assert result.stage is AuthoringStage.VERIFICATION
    assert result.verification.deterministic_replay.status is VerificationGateStatus.FAILED
    assert "explicit seed" in result.verification.deterministic_replay.reason


def test_matching_replay_does_not_override_incomplete_acceptance() -> None:
    result = scaffold(
        ScaffoldRequest(
            spec=_spec(count=2),
            max_count=1,
            sample_rows=1,
            verification=ScaffoldVerification(deterministic_replay=True),
        )
    )

    assert result.ok
    assert not result.verified
    assert result.stage is AuthoringStage.ACCEPTANCE
    assert result.acceptance is not None and not result.acceptance.verified
    assert result.verification.deterministic_replay.status is VerificationGateStatus.PASSED


def test_cli_service_byte_parity_for_smoke_and_replay() -> None:
    request = ScaffoldRequest(
        spec=_spec(),
        sample_rows=1,
        verification=ScaffoldVerification(
            smoke_export=True,
            deterministic_replay=True,
        ),
    )
    service_payload = scaffold(request).model_dump(mode="json", exclude_none=True)
    cli_result = CliRunner().invoke(
        app,
        [
            "scaffold",
            "-",
            "--format",
            "json",
            "--sample-rows",
            "1",
            "--smoke-export",
            "--deterministic-replay",
        ],
        input=json.dumps(_spec()),
    )

    assert cli_result.exit_code == 0
    assert json.loads(cli_result.stdout) == service_payload
