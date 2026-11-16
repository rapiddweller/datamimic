from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path, PurePosixPath

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.adapters.workspace import write_project_scaffold
from datamimic_ce.authoring.domain.project_scaffold import ProjectPattern, ProjectScaffold, ProjectScaffoldFile

PROJECT_DIRECTORIES = ("data", "output", "script", "config")
README_TEMPLATE = """
# DATAMIMIC Project: {project_name}
This project was created using DATAMIMIC.

## Project Structure
- `data/`: Directory for input data files, like .ent.csv or .wgt.csv
- `script/`: Directory for input scripts or custom functions
- `output/`: Directory for generated output
- `config/`: Configuration files
- `datamimic.xml`: Main project descriptor file
- `acceptance/build.json`: Build expectations

## Initial Setup
The project starts with the same minimal descriptor and acceptance that `datamimic authoring init` writes,
which `datamimic authoring build .` proves as `ready`.

## Getting Started
1. Review and modify the `datamimic.xml` file to customize your data generation
2. Place any required input files in the `data/` directory
3. Verify the project using: `datamimic authoring build .`
4. Run the project using: `datamimic run datamimic.xml`
        """


def project_scaffold(project_name: str) -> ProjectScaffold:
    """The authoring starter plus the README that only `datamimic init` adds."""
    application = create_authoring_application()
    starter = application.scaffold(ProjectPattern.FLAT)
    readme = ProjectScaffoldFile(PurePosixPath("README.md"), README_TEMPLATE.replace("{project_name}", project_name))
    return replace(starter, files=(*starter.files, readme))


def validate_project_name(name: str) -> bool:
    """Return whether a project name contains only letters, digits, dashes, and underscores."""
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", name))


def create_project_structure(project_dir: Path) -> None:
    """Create the initial project structure; the starter files overwrite same-named files.

    Raises `ValueError` before anything is created when a starter path cannot be written safely.
    """
    write_project_scaffold(
        project_dir, project_scaffold(project_dir.name), overwrite=True, directories=PROJECT_DIRECTORIES
    )
