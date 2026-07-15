"""CLI boundary for canonical authoring application services."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
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

# Map Pydantic field names to CLI-facing option names for clean error messages.
_FIELD_LABELS: dict[str, str] = {
    "max_diagnostics": "max-diagnostics",
    "max_count": "max-count",
    "sample_rows": "sample-rows",
    "timeout_seconds": "timeout",
}


def _format_numeric_error(label: str, msg: str, ctx: dict[str, object]) -> str | None:
    """Return a formatted numeric-constraint message, or None if not a numeric error."""
    if "gt" in msg or "greater_than_equal" in msg:
        ge = ctx.get("ge")
        le = ctx.get("le")
        if ge is not None and le is not None:
            return f"Invalid {label}. Expected an integer from {ge} to {le}"
        if ge is not None:
            return f"Invalid {label}. Expected an integer >= {ge}"
        if le is not None:
            return f"Invalid {label}. Expected an integer <= {le}"
    if "less_than_equal" in msg:
        le = ctx.get("le")
        if le is not None:
            return f"Invalid {label}. Expected an integer <= {le}"
    return None


def _format_validation_error(error: ValidationError) -> str:
    """Project the first Pydantic error into a single-line CLI message."""
    for err in error.errors():
        field = str(err["loc"][0]) if err.get("loc") else "value"
        label = _FIELD_LABELS.get(field, field)
        msg = err.get("msg", "Invalid value")
        ctx = err.get("ctx", {})
        formatted = _format_numeric_error(label, msg, ctx)
        if formatted is not None:
            return formatted
        return f"Invalid {label}: {msg}"
    return f"Invalid value: {error}"


def lint_descriptor(
    descriptor_path: Path,
    output_format: CliOutputFormat,
    fail_on: str,
    max_diagnostics: int,
) -> None:
    if fail_on not in ("error", "warning"):
        cli_presenter.fail(f"Invalid fail-on '{fail_on}'. Expected: error | warning", output_format)
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
        cli_presenter.fail(_format_validation_error(error), output_format)
    cli_presenter.emit_check(service.check(request), descriptor_path, output_format, FailureThreshold(fail_on))


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
        cli_presenter.fail(_format_validation_error(error), output_format)
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
        cli_presenter.fail(_format_validation_error(error), output_format)
    cli_presenter.emit_scaffold(service.scaffold(request), output_format)


def _validate_show_reference_args(
    topic: ReferenceTopic,
    name: str | None,
    category: AuthoringReferenceCategory | None,
    kind: str | None,
) -> None:
    """Guard CLI args for show_reference; fail()s on invalid combinations."""
    if category is not None and topic is not ReferenceTopic.AUTHORING:
        cli_presenter.fail("--category/--kind are only valid for topic=authoring", code=1)
    if topic is ReferenceTopic.AUTHORING and name is not None:
        cli_presenter.fail("topic=authoring uses --category/--kind, not name", code=1)
    if (category is None) != (kind is None):
        cli_presenter.fail("--category and --kind must be provided together", code=1)


def show_reference(
    topic: ReferenceTopic,
    name: str | None,
    category: AuthoringReferenceCategory | None,
    kind: str | None,
) -> None:
    _validate_show_reference_args(topic, name, category, kind)
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


def show_capabilities(section: str | None = None, full: bool = False) -> None:
    from datamimic_ce.authoring.contracts import CapabilitiesRequest, UnknownCapabilitySection

    if section is not None and full:
        cli_presenter.fail("--section and --full are mutually exclusive", code=1)
    try:
        if section is not None:
            sections = tuple(s.strip() for s in section.split(",") if s.strip())
            request = CapabilitiesRequest(mode="sections", sections=sections)
        elif full:
            request = CapabilitiesRequest(mode="full")
        else:
            request = CapabilitiesRequest()
        cli_presenter.emit_capabilities(service.capabilities(request).root)
    except UnknownCapabilitySection as error:
        payload: dict[str, object] = {
            "ok": False,
            "error": str(error),
            "valid_sections": error.valid_sections,
        }
        typer.echo(json.dumps(payload, indent=2))
        raise typer.Exit(1) from None
