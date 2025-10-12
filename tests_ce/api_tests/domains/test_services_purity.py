"""Static checks that domain services avoid direct file I/O."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

SERVICE_PATHS = (
    Path("datamimic_ce/domains/person/service.py"),
    Path("datamimic_ce/domains/patient/service.py"),
    Path("datamimic_ce/domains/doctor/service.py"),
    Path("datamimic_ce/domains/address/service.py"),
)


@pytest.mark.parametrize("path", SERVICE_PATHS)
def test_services_do_not_call_open(path: Path) -> None:
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "open":
                pytest.fail(f"{path} should not call open() directly")
            if isinstance(func, ast.Attribute) and func.attr == "open":
                if isinstance(func.value, ast.Name) and func.value.id == "Path":
                    pytest.fail(f"{path} should not invoke Path.open directly")
