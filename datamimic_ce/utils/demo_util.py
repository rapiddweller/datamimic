# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import shutil
from importlib.resources import files
from pathlib import Path

import typer


def handle_demo(demo_name, demo_path, overwrite, target_directory):
    # If no target directory is specified, create a new directory with the demo name
    if target_directory is None:
        target_directory = Path.cwd() / demo_name
    # Create the target directory if it doesn't exist
    target_directory.mkdir(parents=True, exist_ok=True)
    # Copy demo contents to the target directory
    for item in demo_path.iterdir():
        target_file_path = target_directory / item.name

        # Check if the target file already exists
        if target_file_path.exists():
            if overwrite:
                typer.echo(f"Overwriting existing file: {target_file_path}")
            else:
                typer.echo(f"File already exists: {target_file_path}. Use --overwrite to overwrite.")
                continue  # Skip copying this file

        try:
            if item.is_file() and item.suffix != ".toml":
                shutil.copy2(item, target_file_path)  # Copy the file
                typer.echo(f"Copied file '{item.name}' to '{target_directory}'")
            elif item.is_dir():
                shutil.copytree(item, target_file_path)  # Copy the directory
                typer.echo(f"Copied directory '{item.name}' to '{target_directory}'")
        except Exception as e:
            typer.echo(f"Error copying '{item.name}': {e}")
            raise typer.Exit(code=1) from e  # Exit with error code 1
    typer.echo(f"Demo '{demo_name}' has been created in '{target_directory}'")


def demo_autocomplete(incomplete: str):
    """Autocomplete function for demo names."""
    demo_dir = files("datamimic_ce").joinpath("demos")
    for demo in demo_dir.iterdir():
        if demo.is_dir() and demo.name.startswith(incomplete):
            yield demo.name
