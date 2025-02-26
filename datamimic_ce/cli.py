# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import json
import os
from importlib.resources import files
from pathlib import Path

import toml
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from datamimic_ce.datamimic import DataMimic
from datamimic_ce.logger import logger
from datamimic_ce.utils.demo_util import demo_autocomplete, handle_demo
from datamimic_ce.utils.file_util import FileUtil
from datamimic_ce.utils.string_util import StringUtil
from datamimic_ce.utils.version_util import get_datamimic_lib_version

app = typer.Typer(help="DATAMIMIC Command Line Interface.", rich_markup_mode="markdown")
demo_app = typer.Typer(help="Manage demos")

# Subcommand for demos
app.add_typer(demo_app, name="demo")

# Constants
DEFAULT_DESCRIPTOR = "datamimic.xml"


@app.command("version", help="Show version information for DATAMIMIC.")
def version_info():
    """Show version information for DATAMIMIC."""
    version = get_datamimic_lib_version()
    typer.echo(f"DATAMIMIC version: {version}")
    raise typer.Exit()


@app.command("init")
def init(
    project_name: str = typer.Argument(..., help="Name of the project directory to create"),
    target_directory: str | None = typer.Option(None, "--target", "-t", help="Target directory for the project"),
    force: bool = typer.Option(False, "--force", "-f", help="Force creation even if directory exists"),
):
    """Initialize a new DATAMIMIC project with a predefined user data generation setup."""
    try:
        if not StringUtil.validate_project_name(project_name):
            typer.secho(
                "Error: Project name can only contain letters, numbers, underscores, and dashes.",
                fg=typer.colors.RED,
            )
            raise typer.Exit(1)

        # Convert target_directory to Path if provided
        project_dir = Path(target_directory) if target_directory else Path.cwd()
        project_dir = project_dir / project_name

        if project_dir.exists():
            if not force:
                typer.secho(
                    f"Error: Directory '{project_dir}' already exists. Use --force to overwrite.",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(1)
            if force and project_dir.is_file():
                typer.secho(
                    f"Error: '{project_dir}' exists and is a file.",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(1)

        project_dir.mkdir(parents=True, exist_ok=force)
        FileUtil.create_project_structure(project_dir)
        console = Console(width=80)
        # Show success message with project information
        console.print(
            Panel.fit(
                f"""Project '{project_name}' created successfully!

📁 Location: {project_dir}

The project is initialized with a sample descriptor that generates:
- User data with personal information
- Multiple output formats (CSV, JSON)
- 100 sample records

Next steps:
1. cd {project_name}
2. Review datamimic.xml to customize the data generation
3. Run 'datamimic run datamimic.xml' to start generation""",
                title="DATAMIMIC Project Initialized",
                border_style="green",
            )
        )

    except Exception as e:
        typer.secho(
            f"Error initializing project: {str(e)}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1) from e


@demo_app.command("list")
def demo_list():
    """List all available demo XML files."""
    demo_path = files("datamimic_ce").joinpath("demos")
    console = Console()
    toml_path: Path  # Placeholder for the toml file path
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name")
    table.add_column("Description")

    for demo_dir in demo_path.iterdir():
        if demo_dir.is_dir():
            toml_path = demo_dir / "info.toml"
            if toml_path.exists():
                demo_info = toml.load(toml_path)
                table.add_row(
                    demo_info.get("projectName", "Unnamed Demo"),
                    demo_info.get("description", "No description provided."),
                )

    console.print(table)


@demo_app.command("create")
def demo_create(
    demo_name: str | None = typer.Argument(
        None, help="Name of the demo directory to use", autocompletion=demo_autocomplete
    ),
    target_directory: Path | None = typer.Option(  # noqa: B008
        None, "--target", "-t", help="Target directory for the demo project"
    ),
    overwrite: bool = typer.Option(False, "--overwrite", "-o", help="Overwrite existing files if they exist"),
    all_demos: bool = typer.Option(False, "--all", help="Create all available demo projects"),
):
    """Creates a project from a specified demo directory or all demos if --all is used."""
    demos_path = files("datamimic_ce").joinpath("demos")

    # Handle the case when --all is specified
    if all_demos:
        if not target_directory:
            typer.echo("Target directory is required when using '--all'.")
            raise typer.Exit(code=1)

        typer.echo(f"Creating all demos in '{target_directory}'")
        target_directory.mkdir(parents=True, exist_ok=True)

        for demo in demos_path.iterdir():
            if demo.is_dir():
                handle_demo(demo.name, demo, overwrite, target_directory / demo.name)
    else:
        if not demo_name:
            typer.echo("Please specify a demo name or use '--all' to create all demos.")
            raise typer.Exit(code=1)

        demo_path = demos_path.joinpath(demo_name)
        handle_demo(demo_name, demo_path, overwrite, target_directory)


@app.command("run")
def run(
    descriptor_path: Path = typer.Argument(DEFAULT_DESCRIPTOR, help="Path to the descriptor file"),  # noqa: B008
    platform_configs: str | None = typer.Option(
        None,
        "--platform-configs",
        help="Platform configurations in JSON format (optional, related to memory limits)",
    ),
    task_id: str | None = typer.Option(None, "--task-id", help="Task identifier (optional for Community Edition)"),
    test_mode: bool = typer.Option(False, "--test-mode", help="Run in test mode to capture test results"),
):
    """Run DATAMIMIC with the specified descriptor file and configurations."""

    # Save the original working directory
    original_directory = Path.cwd()

    # Resolve the descriptor file's absolute path
    descriptor_path = Path(descriptor_path).resolve()

    # Check if the descriptor file exists
    if not descriptor_path.is_file():
        typer.echo(f"Invalid descriptor file path: {descriptor_path}")
        raise typer.Exit(code=1)

    # Change the current working directory to the descriptor's directory
    os.chdir(descriptor_path.parent)
    logger.info(f"Changed working directory to: {descriptor_path.parent}")

    platform_props = {}
    try:
        platform_props = FileUtil.parse_properties(Path(f"{descriptor_path.parent}/conf/environment.env.properties"))
    except FileNotFoundError:
        logger.warning("Environment properties file not found. Continuing with empty properties.")

    platform_configs_dict = json.loads(platform_configs) if platform_configs else None
    engine = DataMimic(descriptor_path, task_id, platform_props, platform_configs_dict, test_mode)

    # Execute the process
    try:
        engine.parse_and_execute()
    finally:
        # Switch back to the original directory
        os.chdir(original_directory)
        logger.info(f"Reverted working directory to: {original_directory}")


if __name__ == "__main__":
    app(prog_name="DATAMIMIC")
