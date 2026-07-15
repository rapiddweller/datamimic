"""Typer declarations for the DATAMIMIC command line interface."""

from pathlib import Path
from typing import Annotated

import typer

from datamimic_ce import cli_authoring, cli_runtime
from datamimic_ce.authoring.contracts import (
    AuthoringReferenceCategory,
    ReferenceTopic,
)
from datamimic_ce.cli_presenter import CliOutputFormat
from datamimic_ce.utils.demo_util import demo_autocomplete

app = typer.Typer(help="DATAMIMIC Command Line Interface.", rich_markup_mode="markdown")
demo_app = typer.Typer(help="Manage packaged demos.")
app.add_typer(demo_app, name="demo")

DESCRIPTOR_PATH = typer.Argument(..., help="Path to the descriptor file")
DEFAULT_DESCRIPTOR_PATH = typer.Argument(Path("datamimic.xml"), help="Path to the descriptor file")
SPEC_PATH = typer.Argument(..., help="Path to model.dm.json; use '-' for stdin")
DEMO_NAME = typer.Argument(..., help="Packaged demo name", autocompletion=demo_autocomplete)
OPTIONAL_DEMO_NAME = typer.Argument(None, help="Packaged demo name", autocompletion=demo_autocomplete)


@app.command("version", help="Show DATAMIMIC version information.")
def version() -> None:
    cli_runtime.show_version()


@app.command("info", help="Show system and DATAMIMIC configuration information.")
def info() -> None:
    cli_runtime.show_system_information()


@app.command(
    "capabilities",
    help="Print the DSL surface as JSON (compact index by default; --full for the complete manifest).",
)
def capabilities(
    section: Annotated[
        str | None,
        typer.Option("--section", help="Comma-separated manifest sections (e.g. elements,rules)"),
    ] = None,
    full: Annotated[
        bool, typer.Option("--full", help="Emit the complete manifest (today's output, unchanged)")
    ] = False,
) -> None:
    cli_authoring.show_capabilities(section, full)


@app.command("reference", help="Query canonical DATAMIMIC model, rule, and authoring reference data.")
def reference(
    topic: Annotated[ReferenceTopic, typer.Argument(help="Canonical reference topic")],
    name: Annotated[str | None, typer.Argument(help="Optional name within the topic")] = None,
    category: Annotated[AuthoringReferenceCategory | None, typer.Option("--category")] = None,
    kind: Annotated[str | None, typer.Option("--kind")] = None,
) -> None:
    cli_authoring.show_reference(topic, name, category, kind)


@app.command("scaffold", help="Compile and fully verify one model.dm.json document.")
def scaffold(
    spec_path: Path = SPEC_PATH,
    output_format: Annotated[CliOutputFormat, typer.Option("--format", "-f")] = CliOutputFormat.TEXT,
    max_count: Annotated[int, typer.Option("--max-count")] = 10,
    sample_rows: Annotated[int, typer.Option("--sample-rows")] = 5,
    smoke_export: Annotated[bool, typer.Option("--smoke-export")] = False,
    deterministic_replay: Annotated[bool, typer.Option("--deterministic-replay")] = False,
) -> None:
    cli_authoring.scaffold_model(
        spec_path,
        output_format,
        max_count,
        sample_rows,
        smoke_export,
        deterministic_replay,
    )


@app.command("lint", help="Lint one DATAMIMIC XML descriptor.")
def lint(
    descriptor_path: Path = DESCRIPTOR_PATH,
    output_format: Annotated[CliOutputFormat, typer.Option("--format", "-f")] = CliOutputFormat.TEXT,
    fail_on: Annotated[str, typer.Option("--fail-on")] = "error",
    max_diagnostics: Annotated[int, typer.Option("--max-diagnostics")] = 200,
) -> None:
    cli_authoring.lint_descriptor(descriptor_path, output_format, fail_on, max_diagnostics)


@app.command("dry-run", help="Safely execute one bounded, target-neutralized descriptor run.")
def dry_run(
    descriptor_path: Path = DESCRIPTOR_PATH,
    max_count: Annotated[int, typer.Option("--max-count")] = 10,
    sample_rows: Annotated[int, typer.Option("--sample-rows")] = 5,
    allow_side_effects: Annotated[bool, typer.Option("--allow-side-effects")] = False,
    timeout: Annotated[int, typer.Option("--timeout")] = 30,
    smoke_export: Annotated[bool, typer.Option("--smoke-export")] = False,
    output_format: Annotated[CliOutputFormat, typer.Option("--format", "-f")] = CliOutputFormat.TEXT,
) -> None:
    cli_authoring.dry_run_descriptor(
        descriptor_path,
        max_count,
        sample_rows,
        allow_side_effects,
        timeout,
        smoke_export,
        output_format,
    )


@app.command("init", help="Initialize a DATAMIMIC project.")
def init(
    project_name: Annotated[str, typer.Argument(help="Project directory name")],
    target_directory: Annotated[Path | None, typer.Option("--target", "-t")] = None,
    force: Annotated[bool, typer.Option("--force", "-f")] = False,
) -> None:
    cli_runtime.initialize_project(project_name, target_directory, force)


@demo_app.command("info")
def demo_info(demo_name: str = DEMO_NAME) -> None:
    cli_runtime.show_demo_information(demo_name)


@demo_app.command("list")
def demo_list() -> None:
    cli_runtime.list_demos()


@demo_app.command("create")
def demo_create(
    demo_name: str | None = OPTIONAL_DEMO_NAME,
    target_directory: Annotated[Path | None, typer.Option("--target", "-t")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite", "-o")] = False,
    all_demos: Annotated[bool, typer.Option("--all")] = False,
) -> None:
    cli_runtime.create_demo(demo_name, target_directory, overwrite, all_demos)


@app.command("run", help="Execute a DATAMIMIC XML descriptor.")
def run(
    descriptor_path: Path = DEFAULT_DESCRIPTOR_PATH,
    platform_configs: Annotated[str | None, typer.Option("--platform-configs")] = None,
    task_id: Annotated[str | None, typer.Option("--task-id")] = None,
    test_mode: Annotated[bool, typer.Option("--test-mode")] = False,
) -> None:
    cli_runtime.execute_descriptor(descriptor_path, platform_configs, task_id, test_mode)


if __name__ == "__main__":
    app(prog_name="DATAMIMIC")
