# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import json
import os
import platform
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
from datamimic_ce.utils.xml_util import XMLValidator

app = typer.Typer(help="DATAMIMIC Command Line Interface.", rich_markup_mode="markdown")
demo_app = typer.Typer(help="Manage demos")

# Subcommand for demos
app.add_typer(demo_app, name="demo")

# Constants
DEFAULT_DESCRIPTOR = "datamimic.xml"


# Pre-defined argument objects to avoid B008 errors
def descriptor_path_arg():
    return typer.Argument(..., help="Path to the descriptor file to validate")


def default_descriptor_arg():
    return typer.Argument(DEFAULT_DESCRIPTOR, help="Path to the descriptor file")


def demo_name_arg():
    return typer.Argument(..., help="Name of the demo to get information about", autocompletion=demo_autocomplete)


def optional_demo_name_arg():
    return typer.Argument(None, help="Name of the demo directory to use", autocompletion=demo_autocomplete)


# Global singleton objects for argument defaults
DESCRIPTOR_PATH = typer.Argument(..., help="Path to the descriptor file to validate")
DEFAULT_DESCRIPTOR_PATH = typer.Argument(DEFAULT_DESCRIPTOR, help="Path to the descriptor file")
DEMO_NAME = typer.Argument(..., help="Name of the demo to get information about", autocompletion=demo_autocomplete)
OPTIONAL_DEMO_NAME = typer.Argument(None, help="Name of the demo directory to use", autocompletion=demo_autocomplete)

# Global singleton objects for option defaults
TARGET_DIRECTORY_OPTION = typer.Option(None, "--target", "-t", help="Target directory for the demo project")
OVERWRITE_OPTION = typer.Option(False, "--overwrite", "-o", help="Overwrite existing files if they exist")
ALL_DEMOS_OPTION = typer.Option(False, "--all", help="Create all available demo projects")
PLATFORM_CONFIGS_OPTION = typer.Option(None, "--platform-configs", help="Platform configurations in JSON format")
TASK_ID_OPTION = typer.Option(None, "--task-id", help="Task identifier")
TEST_MODE_OPTION = typer.Option(False, "--test-mode", help="Run in test mode")

# Environment variables
DATAMIMIC_CONFIG = os.getenv("DATAMIMIC_CONFIG")
DATAMIMIC_OUTPUT_DIR = os.getenv("DATAMIMIC_OUTPUT_DIR")
DATAMIMIC_LOG_LEVEL = os.getenv("DATAMIMIC_LOG_LEVEL", "INFO")


@app.command("version", help="Show version information for DATAMIMIC.")
def version_info():
    """Show version information for DATAMIMIC."""
    version = get_datamimic_lib_version()
    typer.echo(f"DATAMIMIC version: {version}")
    raise typer.Exit()


@app.command("info", help="Display system and configuration information.")
def info():
    """Display detailed system and configuration information."""
    console = Console()
    version = get_datamimic_lib_version()

    info_table = Table(title="System Information", show_header=True)
    info_table.add_column("Component", style="cyan")
    info_table.add_column("Value", style="green")

    info_table.add_row("DATAMIMIC Version", version)
    info_table.add_row("Python Version", platform.python_version())
    info_table.add_row("Operating System", platform.platform())
    info_table.add_row("Config File", str(DATAMIMIC_CONFIG or "Default"))
    info_table.add_row("Output Directory", str(DATAMIMIC_OUTPUT_DIR or "Current Directory"))
    info_table.add_row("Log Level", str(DATAMIMIC_LOG_LEVEL))

    console.print(info_table)


@app.command("validate", help="Validate an XML descriptor file.")
def validate(
    descriptor_path: Path = DESCRIPTOR_PATH,
):
    """Validate the syntax and structure of an XML descriptor file."""
    try:
        if not descriptor_path.is_file():
            typer.echo(f"Error: File not found: {descriptor_path}")
            raise typer.Exit(1)

        validator = XMLValidator()
        is_valid = validator.validate_descriptor(descriptor_path)

        if is_valid:
            typer.echo("Descriptor validation successful!")
            raise typer.Exit(0)
        else:
            typer.echo("Descriptor validation failed!")
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Validation error: {str(e)}")
        raise typer.Exit(1) from e


@demo_app.command("info")
def demo_info(
    demo_name: str = DEMO_NAME,
):
    """Display detailed information about a specific demo."""
    # Get the demo directory from resources
    demo_resource = files("datamimic_ce").joinpath("demos")
    # Convert to Path object so we can use path operations reliably
    demo_dir = Path(str(demo_resource)) / demo_name
    toml_path = demo_dir / "info.toml"

    if not demo_dir.exists():
        typer.echo(f"Error: Demo '{demo_name}' not found.")
        raise typer.Exit(1)

    if not toml_path.exists():
        typer.echo(f"Error: Demo information file not found for '{demo_name}'.")
        raise typer.Exit(1)

    try:
        # Use string conversion for the path to make it compatible with toml.load
        demo_info = toml.load(str(toml_path))
        console = Console()

        info_panel = Panel(
            f"""[bold]Demo Information[/bold]

Name: {demo_info.get("projectName", "Unknown")}
Description: {demo_info.get("description", "No description available")}

Required Dependencies:
{demo_info.get("dependencies", "No dependencies specified")}

Usage Example:
{demo_info.get("usage", "No usage example available")}""",
            title=f"Demo: {demo_name}",
            border_style="green",
        )
        console.print(info_panel)
    except Exception as e:
        typer.echo(f"Error reading demo information: {str(e)}")
        raise typer.Exit(1) from e


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
    # Get the demo path from resources
    demo_resource = files("datamimic_ce").joinpath("demos")
    # Convert to Path for proper type checking
    demo_path = Path(str(demo_resource))
    console = Console()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name")
    table.add_column("Description")

    for demo_dir in demo_path.iterdir():
        if demo_dir.is_dir():
            toml_path = demo_dir / "info.toml"
            if toml_path.exists():
                demo_info = toml.load(str(toml_path))
                table.add_row(
                    demo_info.get("projectName", "Unnamed Demo"),
                    demo_info.get("description", "No description provided."),
                )

    console.print(table)


@demo_app.command("create")
def demo_create(
    demo_name: str | None = OPTIONAL_DEMO_NAME,
    target_directory: Path | None = TARGET_DIRECTORY_OPTION,
    overwrite: bool = OVERWRITE_OPTION,
    all_demos: bool = ALL_DEMOS_OPTION,
):
    """Creates a project from a specified demo directory or all demos if --all is used."""
    # Get the demos path from resources
    demos_resource = files("datamimic_ce").joinpath("demos")
    # Convert to Path for proper type checking
    demos_path = Path(str(demos_resource))

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

        # Get specific demo path
        demo_path = demos_path / demo_name
        handle_demo(demo_name, demo_path, overwrite, target_directory)


@app.command("run")
def run(
    descriptor_path: Path = DEFAULT_DESCRIPTOR_PATH,
    platform_configs: str | None = PLATFORM_CONFIGS_OPTION,
    task_id: str | None = TASK_ID_OPTION,
    test_mode: bool = TEST_MODE_OPTION,
):
    """Run DATAMIMIC with the specified descriptor file and configurations."""
    # Save the original working directory
    original_directory = Path.cwd()

    # Resolve the descriptor file's absolute path
    descriptor_path = Path(descriptor_path).resolve()

    # Check if the descriptor file exists
    if not descriptor_path.is_file():
        typer.echo(f"Invalid descriptor file path: {descriptor_path}")
        raise typer.Exit(1)

    # Change the current working directory to the descriptor's directory
    os.chdir(descriptor_path.parent)
    logger.info(f"Changed working directory to: {descriptor_path.parent}")

    platform_props = {}
    try:
        platform_props = FileUtil.parse_properties(Path(f"{descriptor_path.parent}/conf/environment.env.properties"))
    except FileNotFoundError:
        logger.warning("Environment properties file not found. Continuing with empty properties.")

    # Add platform configurations
    platform_configs_dict = json.loads(platform_configs) if platform_configs else {}

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
