# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Step 4 (validate output) catches a search that breaks a rule. Each case removes or changes the lines of one
check in a copy of lib/staffing.scr.py and Builds the copy; the output check must reject it by name."""

import shutil
from pathlib import Path

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, RejectedBuild

_PROJECT = Path(__file__).resolve().parent
_R4 = """        if _position_key(other) == _position_key(position):
            return Rule.R4, "already holds a seat of this position"
"""
_R5 = """        if other["approval_id"] != position["approval_id"] and (other["exclusive"] or position["exclusive"]):
            return Rule.R5, f"holds a seat of approval {other['approval_id']}; one of the two is exclusive"
"""
_R6 = """        if other["company_id"] != position["company_id"]:
            return Rule.R6, f"holds a seat at company {other['company_id']}"
"""
_ELIGIBLE = """        for entry in position["eligible"]:
            person_id = entry["person_id"]
"""
_NEAR_MISSES_TOO = """        for entry in [*position["near_misses"], *position["eligible"]]:
            person_id = entry["person_id"]
"""

# (mutant, old lines, new lines, the expected text of the row condition that must reject it)
_MUTANTS = [
    ("search_ignores_suitability", _ELIGIBLE, _NEAR_MISSES_TOO, "all_eligible"),
    ("search_ignores_r4", _R4, "", "distinct_people"),
    ("search_ignores_r5", _R5, "", "approval_exclusive"),
    ("search_ignores_r6", _R6, "", "company_exclusive"),
]


@pytest.mark.parametrize(
    ("old", "new", "expected"), [case[1:] for case in _MUTANTS], ids=[case[0] for case in _MUTANTS]
)
def test_output_check_rejects_a_search_that_breaks_a_rule(tmp_path: Path, old: str, new: str, expected: str) -> None:
    project = shutil.copytree(_PROJECT, tmp_path / "project", ignore=shutil.ignore_patterns("negative", "output"))
    library = project / "lib" / "staffing.scr.py"
    text = library.read_text(encoding="utf-8")
    assert text.count(old) == 1, "lib/staffing.scr.py changed these lines; update the mutant"
    library.write_text(text.replace(old, new), encoding="utf-8")
    rejected = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(rejected, RejectedBuild), "Build accepted a search that breaks a rule"
    named = [str(item.expected) for item in rejected.diagnostics if str(item.code) == "row_condition"]
    assert expected in named, f"expected {expected!r}, Build reported {named}"
