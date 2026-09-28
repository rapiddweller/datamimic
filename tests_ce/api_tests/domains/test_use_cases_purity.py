"""Static checks that domain use cases avoid direct file I/O."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

USE_CASE_PATHS = (
    Path("datamimic_ce/domains/shared/use_cases/person_api.py"),
    Path("datamimic_ce/domains/healthcare/use_cases/patient_api.py"),
    Path("datamimic_ce/domains/healthcare/use_cases/doctor_api.py"),
    Path("datamimic_ce/domains/shared/use_cases/address_api.py"),
)


@pytest.mark.parametrize("path", USE_CASE_PATHS)
def test_use_cases_do_not_call_open(path: Path) -> None:
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "open":
                pytest.fail(f"{path} should not call open() directly")
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "open"
                and isinstance(func.value, ast.Name)
                and func.value.id == "Path"
            ):
                pytest.fail(f"{path} should not invoke Path.open directly")
