"""CLI boundary for canonical authoring application services."""

from __future__ import annotations

import sys
from pathlib import Path

from pydantic import JsonValue, TypeAdapter, ValidationError

from datamimic_ce import cli_presenter
from datamimic_ce.authoring import service
from datamimic_ce.authoring.contracts import (
    AUTHORING_REFERENCE_QUERY_ADAPTER,
    AuthoringReferenceCategory,
    AuthoringResponseFormat,
    CheckRequest,
    ReferenceRequest,
    ReferenceTopic,
    RunRequest,
    ScaffoldRequest,
    ScaffoldVerification,
)
from datamimic_ce.cli_presenter import CliOutputFormat, FailureThreshold

JSON_OBJECT_ADAPTER = TypeAdapter(dict[str, JsonValue])


def lint_descriptor(
    descriptor_path: Path,
    output_format: CliOutputFormat,
    fail_on: FailureThreshold,
    max_diagnostics: int,
) -> None:
    if not descriptor_path.is_file():
        cli_presenter.fail(f"File not found: {descriptor_path}", output_format)
    try:
        request = CheckRequest(
            xml=None,
            path=str(descriptor_path),
            response_format=AuthoringResponseFormat.DETAILED,
            max_diagnostics=max_diagnostics,
        )
    except ValidationError as error:
        cli_presenter.fail(str(error), output_format)
    cli_presenter.emit_check(service.check(request), descriptor_path, output_format, fail_on)


def dry_run_descriptor(
    descriptor_path: Path,
    max_count: int,
    sample_rows: int,
    allow_side_effects: bool,
    timeout_seconds: int,
    smoke_export: bool,
    output_format: CliOutputFormat,
) -> None:
    if not descriptor_path.is_file():
        cli_presenter.fail(f"File not found: {descriptor_path}", output_format)
    try:
        request = RunRequest(
            xml=None,
            path=str(descriptor_path),
            response_format=AuthoringResponseFormat.DETAILED,
            max_count=max_count,
            sample_rows=sample_rows,
            allow_side_effects=allow_side_effects,
            timeout_seconds=timeout_seconds,
            smoke_export=smoke_export,
        )
    except ValidationError as error:
        cli_presenter.fail(str(error), output_format)
    cli_presenter.emit_run(service.run(request), output_format)


def scaffold_model(
    spec_path: Path,
    output_format: CliOutputFormat,
    max_count: int,
    sample_rows: int,
    smoke_export: bool,
    deterministic_replay: bool,
) -> None:
    if str(spec_path) != "-" and not spec_path.is_file():
        cli_presenter.fail(f"File not found: {spec_path}", output_format)
    try:
        text = sys.stdin.read() if str(spec_path) == "-" else spec_path.read_text(encoding="utf-8")
    except OSError as error:
        cli_presenter.fail(str(error), output_format)
    try:
        spec = JSON_OBJECT_ADAPTER.validate_json(text)
        request = ScaffoldRequest(
            spec=spec,
            max_count=max_count,
            sample_rows=sample_rows,
            response_format=AuthoringResponseFormat.DETAILED,
            verification=ScaffoldVerification(
                smoke_export=smoke_export,
                deterministic_replay=deterministic_replay,
            ),
        )
    except ValidationError as error:
        cli_presenter.fail(str(error), output_format)
    cli_presenter.emit_scaffold(service.scaffold(request), output_format)


def show_reference(
    topic: ReferenceTopic,
    name: str | None,
    category: AuthoringReferenceCategory | None,
    kind: str | None,
) -> None:
    if category is not None and topic is not ReferenceTopic.AUTHORING:
        cli_presenter.fail("--category/--kind are only valid for topic=authoring", code=1)
    if topic is ReferenceTopic.AUTHORING and name is not None:
        cli_presenter.fail("topic=authoring uses --category/--kind, not name", code=1)
    if (category is None) != (kind is None):
        cli_presenter.fail("--category and --kind must be provided together", code=1)
    try:
        query = (
            AUTHORING_REFERENCE_QUERY_ADAPTER.validate_python({"category": category, "kind": kind})
            if category is not None and kind is not None
            else None
        )
        result = service.reference(ReferenceRequest(topic=topic, name=name, query=query))
    except ValidationError as error:
        cli_presenter.fail(str(error), code=1)
    if not result.ok or result.content is None:
        cli_presenter.fail(result.error or "Reference projection failed", code=1)
    cli_presenter.emit_reference(result.content)


def show_capabilities() -> None:
    cli_presenter.emit_capabilities(service.capabilities().root)
