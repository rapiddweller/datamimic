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
from datamimic_ce.authoring.domain.common import MAX_AUTHORING_MAX_COUNT
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest
from datamimic_ce.interfaces.cli import app
from tests_ce.authoring_project import write_project

_FIXTURES = Path(__file__).parent / "fixtures"


def test_datetime_bound_layout_failure_names_argument_and_layout() -> None:
    path = _FIXTURES / "fx_datetime_date_only_bounds.xml"
    logical = PurePosixPath(path.name)
    result = CeBoundedExecutor(AuthoringWorkspaceContext(path.parent, logical)).execute(
        BoundedExecutionRequest(xml=path.read_text(encoding="utf-8"), descriptor_path=logical)
    )
    assert not result.ok
    assert result.diagnostics[0].message.startswith(
        "DateTimeGenerator min does not match the default layout '%Y-%m-%d %H:%M:%S'."
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


_NAMESPACE_SECRET = "Hunter2SECRET"
_NAMESPACE = f"https://admin:{_NAMESPACE_SECRET}@db.internal/"


@pytest.mark.parametrize(
    ("generate", "rule"),
    [
        (
            f'<generate name="r" count="1"><key xmlns:s="{_NAMESPACE}" s:x="1" name="id" constant="1"/></generate>',
            "DM103",
        ),
        (
            f'<generate xmlns:s="{_NAMESPACE}" s:name="r" name="r" count="1"><key name="id" constant="1"/></generate>',
            "DM103",
        ),
        (f'<generate name="r" count="1"><key xmlns="{_NAMESPACE}" name="id" constant="1"/></generate>', "I604"),
    ],
)
def test_namespace_uri_is_never_echoed(tmp_path: Path, generate: str, rule: str) -> None:
    """A namespace URI is an attribute value; lxml carries it in the Clark name {uri}local of each namespaced name."""
    write_project(tmp_path, f"<setup>{generate}</setup>")
    runner = CliRunner()
    outputs = [
        runner.invoke(app, ["authoring", "lint", str(tmp_path / "datamimic.xml")]).output,
        runner.invoke(app, ["authoring", "dry-run", str(tmp_path / "datamimic.xml")]).output,
        runner.invoke(app, ["authoring", "build", str(tmp_path)]).output,
    ]
    for output in outputs:
        assert _NAMESPACE_SECRET not in output
    # Negative control: every command still reports the namespaced name, so the check above cannot pass vacuously.
    assert all(rule in output for output in outputs), outputs


@pytest.mark.parametrize(
    ("key", "rule"),
    [
        ('type="int" min="1" max="5" separator="{secret}"', "DM214"),
        ('constant="1" min="{secret}" max="{secret}"', "DM218"),
    ],
)
def test_names_only_rules_never_echo_attribute_values(tmp_path: Path, key: str, rule: str) -> None:
    """DM214 and DM218 name attributes from the schema constraints, never from the document."""
    sentinel = "AUDIT_NAMES_ONLY_SECRET_9c1"
    xml = f'<setup><generate name="r" count="1"><key name="k" {key.format(secret=sentinel)}/></generate></setup>'
    write_project(tmp_path, xml)
    runner = CliRunner()
    outputs = [
        runner.invoke(app, ["authoring", "lint", str(tmp_path / "datamimic.xml")]).output,
        runner.invoke(app, ["authoring", "build", str(tmp_path)]).output,
    ]
    for output in outputs:
        assert sentinel not in output
        assert rule in output, output


def test_capped_capture_names_reason_and_exact_retry_bound(tmp_path: Path) -> None:
    """A source without count leaves the declared total unknown, so the limit stays 10 and the capture is capped."""
    (tmp_path / "empty.csv").write_text("id\n", encoding="utf-8")
    write_project(
        tmp_path,
        '<setup rngSeed="1"><generate name="customers" count="50"><key name="id" generator="IncrementGenerator"/>'
        '</generate><generate name="copies" source="empty.csv" distribution="ordered" separator=",">'
        '<key name="copy" script="id"/></generate></setup>',
        expectations=[{"kind": "exact_count", "subject": {"kind": "product", "product": "customers"}, "count": 50}],
    )
    result = CliRunner().invoke(app, ["authoring", "build", str(tmp_path)])
    assert result.exit_code == 1, result.output
    capped = json.loads(result.output)["diagnostics"][0]
    assert capped["message"] == "Product capture is capped: static count 50 exceeds per-invocation limit 10."
    assert capped["remediation"] == "Increase max_count to at least 50 and retry the same transaction."


def test_declared_rows_above_max_count_name_the_exact_retry_bound(tmp_path: Path) -> None:
    write_project(
        tmp_path,
        (_FIXTURES / "fx_static_count_above_limit.xml").read_text(encoding="utf-8"),
        expectations=[{"kind": "exact_count", "subject": {"kind": "product", "product": "customers"}, "count": 50}],
        max_count=10,
    )
    result = CliRunner().invoke(app, ["authoring", "build", str(tmp_path)])
    assert result.exit_code == 1, result.output
    [limit] = json.loads(result.output)["diagnostics"]
    assert limit["message"] == (
        "The products declare 50 rows in total, above max_count 10; max_count limits the rows of all products together."
    )
    assert (limit["expected"], limit["actual"]) == (10, 50)
    assert limit["remediation"].startswith("Set max_count to at least 50")


def test_missing_acceptance_file_is_named_without_its_host_directory(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["authoring", "build", str(tmp_path)])
    assert result.exit_code == 1
    assert (
        json.loads(result.output)["diagnostics"][0]["message"] == "The project has no readable acceptance/build.json."
    )
    assert str(tmp_path) not in result.output


def test_bounded_option_violation_names_the_option(tmp_path: Path) -> None:
    descriptor = tmp_path / "model.xml"
    descriptor.write_text("<setup/>", encoding="utf-8")
    result = CliRunner().invoke(app, ["authoring", "dry-run", str(descriptor), "--max-count", "5000"])
    assert result.exit_code == 1
    assert f"max_count: Input should be less than or equal to {MAX_AUTHORING_MAX_COUNT}" in result.output
