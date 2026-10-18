"""Typer declarations for the DATAMIMIC command line interface."""

from pathlib import Path
from typing import Annotated

import typer

from datamimic_ce.interfaces.cli import authoring as cli_authoring
from datamimic_ce.interfaces.cli import runtime as cli_runtime
from datamimic_ce.interfaces.demo import demo_autocomplete

app = typer.Typer(help="DATAMIMIC Command Line Interface.", rich_markup_mode="markdown")
demo_app = typer.Typer(help="Manage packaged demos.")
app.add_typer(demo_app, name="demo")
app.add_typer(cli_authoring.app, name="authoring")

DEFAULT_DESCRIPTOR_PATH = typer.Argument(Path("datamimic.xml"), help="Path to the descriptor file")
DEMO_NAME = typer.Argument(..., help="Packaged demo name", autocompletion=demo_autocomplete)
OPTIONAL_DEMO_NAME = typer.Argument(None, help="Packaged demo name", autocompletion=demo_autocomplete)


@app.command("version", help="Show DATAMIMIC version information.")
def version() -> None:
    cli_runtime.show_version()


@app.command("info", help="Show system and DATAMIMIC configuration information.")
def info() -> None:
    cli_runtime.show_system_information()


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
