from __future__ import annotations

import json
import re
from pathlib import Path

STARTER_FILES = {
    "datamimic.xml": """
<setup rngSeed="7">
    <generate name="datamimic_user_list" count="10" target="CSV,JSON">
        <variable name="person" entity="Person(min_age=18, max_age=90, female_quota=0.5)"/>
        <key name="id" generator="IncrementGenerator"/>
        <key name="given_name" script="person.given_name"/>
        <key name="family_name" script="person.family_name"/>
        <key name="gender" script="person.gender"/>
        <key name="birthDate" script="person.birthdate" converter="DateFormat('%d.%m.%Y')"/>
        <key name="email" script="person.family_name + '@' + person.given_name + '.de'"/>
        <key name="ce_user" values="True, False"/>
        <key name="ee_user" values="True, False"/>
        <key name="datamimic_lover" constant="DEFINITELY"/>
    </generate>
</setup>
        """,
    "acceptance/build.json": json.dumps(
        {
            "version": "5.0",
            "expectations": [
                {
                    "kind": "exact_count",
                    "subject": {"kind": "product", "product": "datamimic_user_list"},
                    "count": 10,
                }
            ],
        },
        indent=2,
    )
    + "\n",
    "README.md": """
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
The project is initialized with a sample descriptor that generates user data with the following fields:
- User ID (auto-incrementing)
- First Name
- Last Name
- Gender
- Birth Date
- Email
- CE User status
- EE User status
- DATAMIMIC Lover status

## Getting Started
1. Review and modify the `datamimic.xml` file to customize your data generation
2. Place any required input files in the `data/` directory
3. Verify the project using: `datamimic authoring build .`
4. Run the project using: `datamimic run datamimic.xml`
        """,
}


def validate_project_name(name: str) -> bool:
    """Return whether a project name contains only letters, digits, dashes, and underscores."""
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", name))


def create_project_structure(project_dir: Path) -> None:
    """Create the initial project structure with necessary files and directories."""
    for directory in ("data", "output", "script", "config"):
        (project_dir / directory).mkdir(exist_ok=True)
    for relative_path, content in STARTER_FILES.items():
        target = project_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content.replace("{project_name}", project_dir.name), encoding="utf-8")
