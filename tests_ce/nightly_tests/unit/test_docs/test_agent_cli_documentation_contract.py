# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import shutil
from pathlib import Path

import pytest

from tests_ce.documentation_contract_fixtures import ROOT, _build, _projects


@pytest.mark.parametrize(
    "index", range(5), ids=["nested_fk", "memstore_readback", "time_series", "file_sources", "create_table"]
)
def test_documented_structural_projects_build_ready(index: int, tmp_path: Path) -> None:
    projects = _projects(ROOT / "docs/examples/authoring.md")
    assert len(projects) == 5
    # The file-source example reads the fixture of the scenario that holds the complete project.
    if index == 3:
        shutil.copytree(ROOT / "tests_ce/scenarios/s22_file_filter/data", tmp_path / "data")
    result = _build(projects[index], tmp_path)
    assert result["outcome"] == "ready", result
