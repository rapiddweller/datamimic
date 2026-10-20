# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Authoring diagnostics name the concrete cause without echoing descriptor values.

Each case reproduces a friction point from the blind Haiku authoring test: the
agent saw a generic message and had to bisect the descriptor to find the cause.
Descriptor values may be resolved secrets (--param-env), so causes are carried by
static rule/reason texts and structural paths only."""

import json
from pathlib import Path, PurePosixPath

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest
from datamimic_ce.interfaces.cli import app

_FIXTURES = Path(__file__).parent / "fixtures"


def test_datetime_bound_layout_failure_names_argument_and_layout() -> None:
    path = _FIXTURES / "fx_datetime_date_only_bounds.xml"
    logical = PurePosixPath(path.name)
    result = CeBoundedExecutor(AuthoringWorkspaceContext(path.parent, logical)).execute(
        BoundedExecutionRequest(xml=path.read_text(encoding="utf-8"), descriptor_path=logical)
    )
    assert not result.ok
    assert result.diagnostics[0].message == (
        "DateTimeGenerator min does not match input_format; "
        "the default layout is '%Y-%m-%d %H:%M:%S', pass input_format for other layouts"
    )


def test_custom_input_format_mismatch_does_not_recommend_the_default() -> None:
    from datamimic_ce.domains.shared.literal_generators.temporal.datetime_generator import DateTimeGenerator
    from datamimic_ce.errors import GeneratorConfigError

    with pytest.raises(GeneratorConfigError) as caught:
        DateTimeGenerator(min="2025-01-01", input_format="%d/%m/%Y")
    assert caught.value.constructor_reason == "DateTimeGenerator min does not match the configured input_format"


@pytest.mark.parametrize(
    "key",
    [
        'type="int" min="1" max="5" distribution="{secret}"',
        'type="{secret}" min="1" max="5"',
        "generator=\"DateTimeGenerator(min='{secret}')\"",
        'generator="IntegerGenerator" min="{secret}"',
    ],
)
def test_lint_and_dry_run_never_echo_descriptor_values(tmp_path: Path, key: str) -> None:
    sentinel = "AUDIT_AUTHORING_SECRET_7f3"
    descriptor = tmp_path / "model.xml"
    descriptor.write_text(
        f'<setup><generate name="r" count="1"><key name="k" {key.format(secret=sentinel)}/></generate></setup>',
        encoding="utf-8",
    )
    runner = CliRunner()
    for command in ("lint", "dry-run"):
        result = runner.invoke(app, ["authoring", command, str(descriptor)])
        assert sentinel not in result.output
    assert result.exit_code == 1, result.output  # every case is rejected at the latest by bounded execution


def test_capped_capture_names_reason_and_exact_retry_bound(tmp_path: Path) -> None:
    runner = CliRunner()
    decompiled = runner.invoke(app, ["authoring", "decompile", str(_FIXTURES / "fx_static_count_above_limit.xml")])
    document = json.loads(decompiled.output)["document"]
    build = tmp_path / "build.json"
    build.write_text(
        json.dumps(
            {
                "document": document,
                "expectations": [
                    {"kind": "exact_count", "subject": {"kind": "product", "product": "customers"}, "count": 50}
                ],
            }
        ),
        encoding="utf-8",
    )
    result = runner.invoke(app, ["authoring", "build", str(build)])
    assert result.exit_code == 1, result.output
    capped = json.loads(result.output)["diagnostics"][0]
    assert capped["message"] == "Product capture is capped: static count 50 exceeds per-invocation limit 10."
    assert capped["remediation"] == "Increase max_count to at least 50 and retry the same transaction."


def test_missing_build_file_is_named_without_its_host_directory(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["authoring", "build", str(tmp_path / "absent.json")])
    assert result.exit_code == 1
    assert json.loads(result.output)["diagnostics"][0]["message"] == "Input file not found: absent.json"
    assert str(tmp_path) not in result.output


def test_bounded_option_violation_names_the_option(tmp_path: Path) -> None:
    descriptor = tmp_path / "model.xml"
    descriptor.write_text("<setup/>", encoding="utf-8")
    result = CliRunner().invoke(app, ["authoring", "dry-run", str(descriptor), "--max-count", "5000"])
    assert result.exit_code == 1
    assert "max_count: Input should be less than or equal to 1000" in result.output
