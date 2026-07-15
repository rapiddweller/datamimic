# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Contract and transport parity tests for the authoring service gateway."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

import datamimic_ce.authoring.service as authoring_service
from datamimic_ce.authoring.contracts import (
    AuthoringStage,
    CheckRequest,
    CheckResult,
    ProductResult,
    RunRequest,
    RunResult,
    ScaffoldRequest,
    ScaffoldResult,
)
from datamimic_ce.authoring.diagnostics import LintResult
from datamimic_ce.authoring.dryrun import (
    CapturedProduct,
    CapturedProducts,
    CapturedRun,
    DryRunProduct,
    DryRunResult,
)
from datamimic_ce.authoring.service import check, run
from datamimic_ce.cli import app
from datamimic_ce.mcp.models import CheckArgs, RunArgs, ScaffoldArgs
from datamimic_ce.mcp.server import check_impl, run_impl

_XML = """<setup rngSeed="1">
    <generate name="items" count="3" target="">
        <key name="id" generator="IncrementGenerator"/>
    </generate>
</setup>"""

_SCAFFOLD_SPEC = {
    "version": "1",
    "seed": 1,
    "products": [
        {
            "kind": "generated",
            "name": "items",
            "count": 2,
            "fields": [{"kind": "increment", "name": "id"}],
        }
    ],
}


def test_mcp_authoring_models_are_canonical_contract_aliases() -> None:
    assert CheckArgs is CheckRequest
    assert RunArgs is RunRequest
    assert ScaffoldArgs is ScaffoldRequest


def test_authoring_result_models_have_one_canonical_owner() -> None:
    assert CheckResult is LintResult
    assert DryRunProduct is ProductResult
    assert DryRunResult is RunResult


def test_authoring_stage_is_typed_and_serialized_only_at_the_boundary() -> None:
    run_result = RunResult(ok=True, stage=AuthoringStage.RUN)
    scaffold_result = ScaffoldResult(ok=True, stage=AuthoringStage.ACCEPTANCE)

    assert run_result.stage is AuthoringStage.RUN
    assert scaffold_result.stage is AuthoringStage.ACCEPTANCE
    assert run_result.model_dump(mode="json")["stage"] == "run"
    assert scaffold_result.model_dump(mode="json")["stage"] == "acceptance"

    with pytest.raises(ValidationError):
        RunResult(ok=True, stage="unknown")
    with pytest.raises(ValidationError):
        ScaffoldResult(ok=True, stage="unknown")


def test_service_returns_low_level_canonical_results_without_copying(monkeypatch) -> None:
    lint_result = LintResult(ok=True)
    run_result = RunResult(ok=True, stage=AuthoringStage.RUN)
    monkeypatch.setattr(authoring_service, "lint_source", lambda *_args, **_kwargs: lint_result)
    monkeypatch.setattr(authoring_service, "dry_run_source", lambda *_args, **_kwargs: run_result)

    assert authoring_service.check(CheckRequest(xml=_XML)) is lint_result
    assert authoring_service.run(RunRequest(xml=_XML)) is run_result


def test_scaffold_dry_run_uses_only_the_canonical_dry_run_pipeline(monkeypatch) -> None:
    calls = {"lint": 0, "dry_run": 0}

    def unexpected_lint(*_args, **_kwargs):
        calls["lint"] += 1
        pytest.fail("dry-run scaffold branch must not pre-lint")

    def fake_dry_run(*_args, **_kwargs) -> CapturedRun:
        calls["dry_run"] += 1
        return CapturedRun(
            result=RunResult(
                ok=True,
                stage=AuthoringStage.RUN,
                lint=LintResult(ok=True),
            ),
            captured=CapturedProducts(
                (CapturedProduct("items", ({"id": 1}, {"id": 2})),),
                max_count=10,
            ),
        )

    monkeypatch.setattr(authoring_service, "lint_source", unexpected_lint)
    monkeypatch.setattr(authoring_service, "dry_run_source_captured", fake_dry_run)

    result = authoring_service.scaffold(ScaffoldRequest(spec=_SCAFFOLD_SPEC))

    assert result.ok
    assert result.stage is AuthoringStage.ACCEPTANCE
    assert calls == {"lint": 0, "dry_run": 1}


def test_scaffold_rejects_removed_lint_only_switch() -> None:
    with pytest.raises(ValidationError, match="dry_run"):
        ScaffoldRequest(spec=_SCAFFOLD_SPEC, dry_run=False)


def test_check_service_mcp_cli_parity(tmp_path: Path) -> None:
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(_XML, encoding="utf-8")
    request = CheckRequest(
        path=str(descriptor),
        response_format="detailed",
        max_diagnostics=17,
    )

    service_result = check(request)
    mcp_result = check_impl(request)
    cli_result = CliRunner().invoke(
        app,
        ["lint", str(descriptor), "--format", "json", "--max-diagnostics", "17"],
    )

    assert cli_result.exit_code == 0
    cli_payload = json.loads(cli_result.stdout)
    assert mcp_result == {
        "ok": service_result.ok,
        "summary": service_result.summary(),
        "diagnostics": [diagnostic.model_dump(mode="json") for diagnostic in service_result.diagnostics],
        "truncated": service_result.truncated,
    }
    assert cli_payload == service_result.model_dump(mode="json")


def test_run_service_mcp_cli_parity(tmp_path: Path) -> None:
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(_XML, encoding="utf-8")
    request = RunRequest(
        path=str(descriptor),
        response_format="detailed",
        max_count=2,
        sample_rows=1,
        timeout_seconds=7,
    )

    service_result = run(request)
    mcp_result = run_impl(request)
    cli_result = CliRunner().invoke(
        app,
        [
            "dry-run",
            str(descriptor),
            "--format",
            "json",
            "--max-count",
            "2",
            "--sample-rows",
            "1",
            "--timeout",
            "7",
        ],
    )

    assert cli_result.exit_code == 0
    cli_payload = json.loads(cli_result.stdout)
    assert mcp_result["ok"] == service_result.ok == cli_payload["ok"]
    assert service_result.stage is AuthoringStage.RUN
    assert mcp_result["stage"] == cli_payload["stage"] == AuthoringStage.RUN.value
    assert mcp_result["products"] == [
        product.model_dump(mode="json") for product in service_result.products
    ]
    assert cli_payload["products"] == mcp_result["products"]
    assert mcp_result["diagnostics"] == cli_payload["diagnostics"]


@pytest.mark.parametrize(
    ("request_type", "field", "value"),
    [
        (CheckRequest, "max_diagnostics", 0),
        (CheckRequest, "max_diagnostics", 201),
        (RunRequest, "max_count", 0),
        (RunRequest, "max_count", 1001),
        (RunRequest, "sample_rows", 0),
        (RunRequest, "sample_rows", 51),
        (RunRequest, "timeout_seconds", 0),
        (RunRequest, "timeout_seconds", 121),
        (ScaffoldRequest, "max_count", 0),
        (ScaffoldRequest, "max_count", 1001),
        (ScaffoldRequest, "sample_rows", 0),
        (ScaffoldRequest, "sample_rows", 51),
    ],
)
def test_canonical_authoring_bounds_reject_out_of_range_values(
    request_type: type[CheckRequest] | type[RunRequest] | type[ScaffoldRequest],
    field: str,
    value: int,
) -> None:
    if request_type is ScaffoldRequest:
        kwargs = {"spec": {"generates": []}, field: value}
    else:
        kwargs = {"xml": "<setup/>", field: value}

    with pytest.raises(ValidationError):
        request_type(**kwargs)
