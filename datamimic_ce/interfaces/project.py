from __future__ import annotations

from pathlib import Path


def create_project_structure(project_dir: Path) -> None:
    """Create the initial project structure with necessary files and directories."""
    initial_descriptor_content = """
<setup>
    <generate name="datamimic_user_list" count="1000" target="CSV,JSON">
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
        """

    (project_dir / "data").mkdir(exist_ok=True)
    (project_dir / "output").mkdir(exist_ok=True)
    (project_dir / "script").mkdir(exist_ok=True)
    (project_dir / "config").mkdir(exist_ok=True)

    (project_dir / "datamimic.xml").write_text(initial_descriptor_content, encoding="utf-8")

    readme_content = f"""
# DATAMIMIC Project: {project_dir.name}
This project was created using DATAMIMIC.

## Project Structure
- `data/`: Directory for input data files, like .ent.csv or .wgt.csv
- `script/`: Directory for input scripts or custom functions
- `output/`: Directory for generated output
- `config/`: Configuration files
- `datamimic.xml`: Main project descriptor file

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
3. Run the project using: `datamimic run datamimic.xml`
        """
    (project_dir / "README.md").write_text(readme_content, encoding="utf-8")
