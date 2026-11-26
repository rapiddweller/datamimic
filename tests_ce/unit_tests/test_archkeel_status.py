# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.
"""Exercise ArchKeel status coloring without hiding uncertainty."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "script/architecture_study/archkeel_status.py"
spec = importlib.util.spec_from_file_location("archkeel_status", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.parametrize(
    "verdict,exit_code,color",
    [("PASS", 0, "green"), ("UNKNOWN", 2, "orange"), ("FAIL", 1, "red")],
)
def test_status_colors(verdict, exit_code, color):
    result = module.make_status(
        {
            "status": verdict,
            "exit_code": exit_code,
            "baseline": {"state": "current"},
            "frame": {"rules": {"rule": ["kind", verdict]}, "violations": []},
        }
    )
    assert result["color"] == color
    assert result[verdict.lower()] == 1
    assert result["exitCode"] == exit_code


@pytest.mark.parametrize("violations", [["violation"], {"violation": {}}])
def test_violations_are_red_even_without_failed_rules(violations):
    validation = {
        "status": "PASS",
        "exit_code": 0,
        "baseline": {"state": "current"},
        "frame": {"rules": {}, "violations": violations},
    }
    assert module.make_status(validation)["color"] == "red"


def test_missing_frame_is_rejected():
    with pytest.raises(KeyError):
        module.make_status({})
