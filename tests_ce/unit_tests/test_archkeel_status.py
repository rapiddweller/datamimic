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
    [("PASS", 0, "green"), ("UNKNOWN", 2, "yellow"), ("FAIL", 1, "red")],
)
def test_status_colors(verdict, exit_code, color):
    result = module.make_status(
        {
            "status": verdict,
            "exit_code": exit_code,
            "outcome": "verdict",
            "frame": {"rules": {"rule": ["kind", verdict]}, "violations": []},
        }
    )
    assert result["color"] == color
    assert result[verdict.lower()] == 1
    assert result["exitCode"] == exit_code


def test_diagnostics_without_failed_rules_do_not_change_the_badge():
    validation = {
        "status": "UNKNOWN",
        "exit_code": 2,
        "outcome": "verdict",
        "frame": {"rules": {"rule": ["kind", "PASS"]}, "violations": {}, "gaps": ["gap"]},
    }
    assert module.make_status(validation)["color"] == "green"


def test_missing_frame_is_rejected():
    with pytest.raises(KeyError):
        module.make_status({"outcome": "verdict"})


def test_refusal_is_not_a_verdict():
    with pytest.raises(ValueError, match="did not return a verdict"):
        module.make_status({})
