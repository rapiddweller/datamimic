"""README facts that a repository file proves stay equal to that file."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
README = (ROOT / "README.md").read_text(encoding="utf-8")
SHOP = ROOT / "tests_ce/scenarios/s50_readme_shop"


def test_readme_shop_project_is_the_scenario_project() -> None:
    xml_blocks = [block.strip() for block in re.findall(r"```xml\n(.*?)```", README, re.DOTALL)]
    json_blocks = [json.loads(block) for block in re.findall(r"```json\n(.*?)```", README, re.DOTALL)]

    assert (SHOP / "datamimic.xml").read_text(encoding="utf-8").strip() in xml_blocks
    assert json.loads((SHOP / "acceptance/build.json").read_text(encoding="utf-8")) in json_blocks


def test_readme_determinism_matrix_size_equals_the_workflow() -> None:
    workflow = (ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8")
    matrix = workflow.split("runtime_determinism_matrix:", 1)[1]
    cells = len(re.findall(r"^\s+cell: ", matrix, re.MULTILINE))
    stated = int(re.search(r"compares seeded output on (\d+) configurations", README).group(1))

    assert stated == cells


def test_readme_scenario_count_is_not_above_the_repository() -> None:
    stated = int(re.search(r"Each of the (\d+) \[scenarios\]", README).group(1))
    scenarios = [p for p in (ROOT / "tests_ce/scenarios").iterdir() if re.match(r"s\d+_", p.name)]

    assert len(scenarios) >= stated
