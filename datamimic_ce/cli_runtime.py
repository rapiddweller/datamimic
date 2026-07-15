"""CLI application actions for runtime, projects, and packaged demos."""

from __future__ import annotations

import json
import os
import platform
from importlib.resources import files
from pathlib import Path

import toml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from datamimic_ce import cli_presenter
from datamimic_ce.cli_presenter import DemoInformation, DemoSummary, SystemInformation
from datamimic_ce.datamimic import DataMimic
from datamimic_ce.logger import logger
from datamimic_ce.utils.demo_util import handle_demo
from datamimic_ce.utils.file_util import FileUtil
from datamimic_ce.utils.string_util import StringUtil
from datamimic_ce.utils.version_util import get_datamimic_lib_version


class DemoMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")

    project_name: str = Field("Unknown", validation_alias="projectName")
    description: str = "No description available"
    dependencies: str = "No dependencies specified"
    usage: str = "No usage example available"


def show_version() -> None:
    cli_presenter.emit_version(get_datamimic_lib_version())


def show_system_information() -> None:
    cli_presenter.emit_system_information(
        SystemInformation(
            version=get_datamimic_lib_version(),
            python_version=platform.python_version(),
            operating_system=platform.platform(),
            config_file=os.getenv("DATAMIMIC_CONFIG", "Default"),
            output_directory=os.getenv("DATAMIMIC_OUTPUT_DIR", "Current Directory"),
            log_level=os.getenv("DATAMIMIC_LOG_LEVEL", "INFO"),
        )
    )


def initialize_project(project_name: str, target_directory: Path | None, force: bool) -> None:
    if not StringUtil.validate_project_name(project_name):
        cli_presenter.fail("Project name can only contain letters, numbers, underscores, and dashes", code=1)
    project_dir = (target_directory or Path.cwd()) / project_name
    if project_dir.exists() and not force:
        cli_presenter.fail(f"Directory '{project_dir}' already exists. Use --force to overwrite", code=1)
    if project_dir.is_file():
        cli_presenter.fail(f"'{project_dir}' exists and is a file", code=1)
    project_dir.mkdir(parents=True, exist_ok=force)
    FileUtil.create_project_structure(project_dir)
    cli_presenter.emit_project_created(project_name, project_dir)


def show_demo_information(demo_name: str) -> None:
    demo_dir = Path(str(files("datamimic_ce").joinpath("demos"))) / demo_name
    metadata_path = demo_dir / "info.toml"
    if not metadata_path.is_file():
        cli_presenter.fail(f"Demo '{demo_name}' not found", code=1)
    try:
        metadata = DemoMetadata.model_validate(toml.load(str(metadata_path)))
    except (OSError, ValidationError) as error:
        cli_presenter.fail(f"Cannot read demo metadata: {error}", code=1)
    cli_presenter.emit_demo_information(
        DemoInformation(
            name=demo_name,
            project_name=metadata.project_name,
            description=metadata.description,
            dependencies=metadata.dependencies,
            usage=metadata.usage,
        )
    )


def list_demos() -> None:
    demos_path = Path(str(files("datamimic_ce").joinpath("demos")))
    summaries: list[DemoSummary] = []
    for demo_dir in sorted(demos_path.iterdir()):
        metadata_path = demo_dir / "info.toml"
        if demo_dir.is_dir() and metadata_path.is_file():
            metadata = DemoMetadata.model_validate(toml.load(str(metadata_path)))
            summaries.append(DemoSummary(metadata.project_name, metadata.description))
    cli_presenter.emit_demo_list(tuple(summaries))


def create_demo(
    demo_name: str | None,
    target_directory: Path | None,
    overwrite: bool,
    all_demos: bool,
) -> None:
    demos_path = Path(str(files("datamimic_ce").joinpath("demos")))
    if all_demos:
        if target_directory is None:
            cli_presenter.fail("Target directory is required with --all", code=1)
        target_directory.mkdir(parents=True, exist_ok=True)
        for demo in sorted(demos_path.iterdir()):
            if demo.is_dir():
                handle_demo(demo.name, demo, overwrite, target_directory / demo.name)
        return
    if demo_name is None:
        cli_presenter.fail("Specify a demo name or use --all", code=1)
    handle_demo(demo_name, demos_path / demo_name, overwrite, target_directory)


def execute_descriptor(
    descriptor_path: Path,
    platform_configs: str | None,
    task_id: str | None,
    test_mode: bool,
) -> None:
    """Full runtime execution — intentionally bypasses authoring.service, which only
    offers the bounded dry-run path. This is the production engine boundary."""
    descriptor = descriptor_path.resolve()
    if not descriptor.is_file():
        cli_presenter.fail(f"Invalid descriptor file path: {descriptor}", code=1)
    try:
        platform_config_values = json.loads(platform_configs) if platform_configs else {}
    except json.JSONDecodeError as error:
        cli_presenter.fail(f"Invalid platform configuration JSON: {error}", code=1)
    original_directory = Path.cwd()
    try:
        os.chdir(descriptor.parent)
        logger.info(f"Changed working directory to: {descriptor.parent}")
        try:
            environment = FileUtil.parse_properties(descriptor.parent / "conf/environment.env.properties")
        except FileNotFoundError:
            environment = {}
        DataMimic(descriptor, task_id, environment, platform_config_values, test_mode).parse_and_execute()
    finally:
        os.chdir(original_directory)
        logger.info(f"Reverted working directory to: {original_directory}")
