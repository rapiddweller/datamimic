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
)
from datamimic_ce.authoring.service import check, run
from datamimic_ce.cli import app

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


def test_check_service_cli_parity(tmp_path: Path) -> None:
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(_XML, encoding="utf-8")
    request = CheckRequest(
        path=str(descriptor),
        max_diagnostics=17,
    )

    service_result = check(request)
    cli_result = CliRunner().invoke(
        app,
        ["lint", str(descriptor), "--format", "json", "--max-diagnostics", "17"],
    )

    assert cli_result.exit_code == 0
    cli_payload = json.loads(cli_result.stdout)
    assert cli_payload == service_result.model_dump(mode="json")


def test_run_service_cli_parity(tmp_path: Path) -> None:
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(_XML, encoding="utf-8")
    request = RunRequest(
        path=str(descriptor),
        max_count=2,
        sample_rows=1,
        timeout_seconds=7,
    )

    service_result = run(request)
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
    assert service_result.ok == cli_payload["ok"]
    assert service_result.stage is AuthoringStage.RUN
    assert cli_payload["stage"] == AuthoringStage.RUN.value
    assert cli_payload["products"] == [product.model_dump(mode="json") for product in service_result.products]
    assert cli_payload["diagnostics"] == [
        diagnostic.model_dump(mode="json") for diagnostic in service_result.diagnostics
    ]


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


@pytest.mark.parametrize(
    ("request_type", "kwargs"),
    [
        (CheckRequest, {"xml": "<setup/>", "max_diagnostics": "5"}),
        (RunRequest, {"xml": "<setup/>", "max_count": "5"}),
        (RunRequest, {"xml": "<setup/>", "allow_side_effects": "yes"}),
        (RunRequest, {"xml": "<setup/>", "smoke_export": "false"}),
        (ScaffoldRequest, {"spec": _SCAFFOLD_SPEC, "sample_rows": "5"}),
    ],
)
def test_authoring_requests_reject_coercive_scalar_inputs(
    request_type: type[CheckRequest] | type[RunRequest] | type[ScaffoldRequest],
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        request_type.model_validate(kwargs)


@pytest.mark.parametrize("request_type", [CheckRequest, RunRequest, ScaffoldRequest])
def test_authoring_requests_reject_unknown_fields(
    request_type: type[CheckRequest] | type[RunRequest] | type[ScaffoldRequest],
) -> None:
    kwargs: dict[str, object] = {"spec": _SCAFFOLD_SPEC} if request_type is ScaffoldRequest else {"xml": "<setup/>"}
    kwargs["response_format"] = "detailed"

    with pytest.raises(ValidationError, match="response_format"):
        request_type.model_validate(kwargs)
