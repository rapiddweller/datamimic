"""Rendering and process exit policy for the CLI."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import NoReturn

import typer
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from datamimic_ce.authoring.domain.requests import ReadyBuild, ReadyCompileDocument, ReadyDecompileDocument


class CliOutputFormat(StrEnum):
    TEXT = "text"
    JSON = "json"


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


def emit_authoring(
    result: BaseModel | Mapping[str, object], output_format: CliOutputFormat, *, exit_code: int = 0
) -> NoReturn:
    if output_format is CliOutputFormat.TEXT and isinstance(result, (ReadyCompileDocument, ReadyBuild)):
        for diagnostic in result.diagnostics:
            typer.echo(f"{diagnostic.severity}: {diagnostic.message}", err=True)
        typer.echo(result.artifact.compiled_xml)
    elif output_format is CliOutputFormat.TEXT and isinstance(result, ReadyDecompileDocument):
        for diagnostic in result.diagnostics:
            typer.echo(f"{diagnostic.severity}: {diagnostic.message}", err=True)
        typer.echo(result.document.model_dump_json(indent=2, exclude_none=True))
    elif isinstance(result, BaseModel):
        typer.echo(result.model_dump_json(indent=2))
    else:
        typer.echo(json.dumps(dict(result), indent=2, ensure_ascii=False))
    raise typer.Exit(exit_code)
