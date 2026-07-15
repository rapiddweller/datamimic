"""CLI-only rendering and process exit policy."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import NoReturn

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from datamimic_ce.authoring.contracts import AuthoringStage, RunResult, ScaffoldResult
from datamimic_ce.authoring.diagnostics import LintResult
from datamimic_ce.authoring.rule_catalog import RuleSeverity


class CliOutputFormat(StrEnum):
    TEXT = "text"
    JSON = "json"


class FailureThreshold(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class SystemInformation:
    version: str
    python_version: str
    operating_system: str
    config_file: str
    output_directory: str
    log_level: str


@dataclass(frozen=True)
class DemoInformation:
    name: str
    project_name: str
    description: str
    dependencies: str
    usage: str


@dataclass(frozen=True)
class DemoSummary:
    name: str
    description: str


def fail(message: str, output_format: CliOutputFormat = CliOutputFormat.TEXT, code: int = 2) -> NoReturn:
    if output_format is CliOutputFormat.JSON:
        typer.echo(json.dumps({"ok": False, "error": message}, indent=2))
    else:
        typer.echo(f"Error: {message}")
    raise typer.Exit(code)


def emit_version(version: str) -> None:
    typer.echo(f"DATAMIMIC version: {version}")


def emit_system_information(information: SystemInformation) -> None:
    table = Table(title="System Information", show_header=True)
    table.add_column("Component", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("DATAMIMIC Version", information.version)
    table.add_row("Python Version", information.python_version)
    table.add_row("Operating System", information.operating_system)
    table.add_row("Config File", information.config_file)
    table.add_row("Output Directory", information.output_directory)
    table.add_row("Log Level", information.log_level)
    Console().print(table)


def emit_check(
    result: LintResult,
    descriptor_path: Path,
    output_format: CliOutputFormat,
    threshold: FailureThreshold,
) -> None:
    if output_format is CliOutputFormat.JSON:
        typer.echo(result.model_dump_json(indent=2))
    else:
        for diagnostic in result.diagnostics:
            location = f"{descriptor_path}:{diagnostic.line}" if diagnostic.line else str(descriptor_path)
            typer.echo(f"{location}  {diagnostic.severity.value.upper():<7} {diagnostic.rule}  {diagnostic.message}")
            typer.echo(f"    -> {diagnostic.fix_hint}")
        suffix = f" (+{result.truncated} truncated)" if result.truncated else ""
        typer.echo(f"Summary: {result.summary()}{suffix}")
    severities = {RuleSeverity.ERROR}
    if threshold is FailureThreshold.WARNING:
        severities.add(RuleSeverity.WARNING)
    raise typer.Exit(1 if any(item.severity in severities for item in result.diagnostics) else 0)


def emit_run(result: RunResult, output_format: CliOutputFormat) -> None:
    if output_format is CliOutputFormat.JSON:
        typer.echo(result.model_dump_json(indent=2))
    else:
        typer.echo(f"ok: {result.ok}")
        typer.echo(f"stage: {result.stage.value}")
        if result.timing_ms is not None:
            typer.echo(f"timing: {result.timing_ms}ms")
        for product in result.products:
            note = " (truncated)" if product.truncated_rows else ""
            typer.echo(f"{product.name}: {product.count} rows{note}")
            for row in product.sample:
                typer.echo(f"  {row}")
        if result.products_truncated:
            typer.echo(f"(+{result.products_truncated} products truncated)")
        for diagnostic in result.diagnostics:
            typer.echo(f"{diagnostic.severity.value.upper():<7} {diagnostic.rule}  {diagnostic.message}")
            typer.echo(f"    -> {diagnostic.fix_hint}")
    raise typer.Exit(0 if result.ok else 1)


def emit_scaffold(result: ScaffoldResult, output_format: CliOutputFormat) -> None:
    if output_format is CliOutputFormat.JSON:
        typer.echo(result.model_dump_json(indent=2, exclude_none=True))
    else:
        for issue in result.issues:
            typer.echo(f"Error: {issue.summary()}")
        for diagnostic in result.diagnostics:
            severity = diagnostic.severity.value.upper()
            typer.echo(f"{severity:<7} {diagnostic.rule}  {diagnostic.message}")
            typer.echo(f"    -> {diagnostic.fix_hint}")
        if result.summary:
            typer.echo(f"Summary: {result.summary}")
        if result.xml and result.stage not in (AuthoringStage.LINT, AuthoringStage.DRY_RUN):
            typer.echo(result.xml)
        if result.products:
            typer.echo("Dry-run successful:")
        for product in result.products:
            typer.echo(f"{product.name}: {product.count} rows")
        if result.acceptance:
            typer.echo(
                f"Acceptance: {result.acceptance.passed} passed, "
                f"{result.acceptance.failed} failed, {result.acceptance.unevaluable} unevaluable"
            )
        typer.echo(f"verified: {result.verified}")
    if not result.ok or not result.verified:
        raise typer.Exit(2 if result.stage is AuthoringStage.RENDER else 1)
    raise typer.Exit(0)


def emit_reference(content: str) -> None:
    typer.echo(content)


def emit_capabilities(payload: Mapping[str, object]) -> None:
    typer.echo(json.dumps(payload, indent=2, default=str))


def emit_demo_information(information: DemoInformation) -> None:
    Console().print(
        Panel(
            "\n".join(
                (
                    "[bold]Demo Information[/bold]",
                    "",
                    f"Name: {information.project_name}",
                    f"Description: {information.description}",
                    "",
                    "Required Dependencies:",
                    information.dependencies,
                    "",
                    "Usage Example:",
                    information.usage,
                )
            ),
            title=f"Demo: {information.name}",
            border_style="green",
        )
    )


def emit_demo_list(demos: tuple[DemoSummary, ...]) -> None:
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name")
    table.add_column("Description")
    for demo in demos:
        table.add_row(demo.name, demo.description)
    Console().print(table)


def emit_project_created(project_name: str, project_dir: Path) -> None:
    Console(width=80).print(
        Panel.fit(
            f"Project '{project_name}' created successfully!\n\nLocation: {project_dir}\n\n"
            f"Next: cd {project_name} && datamimic run datamimic.xml",
            title="DATAMIMIC Project Initialized",
            border_style="green",
        )
    )
