# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A search mutant in negative/ is a copy of the library with one check changed. A library edit that is not
copied to the mutants makes this test fail, so a negative never tests stale code."""

import difflib
from pathlib import Path

import pytest

_PROJECT = Path(__file__).resolve().parent
_LIBRARY = (_PROJECT / "lib" / "staffing.scr.py").read_text(encoding="utf-8").splitlines()
_MUTANTS = sorted(_PROJECT.glob("negative/*/lib/staffing.scr.py"))


@pytest.mark.parametrize("mutant", _MUTANTS, ids=lambda path: path.parts[-3])
def test_mutant_changes_two_lines_of_the_library(mutant: Path) -> None:
    diff = difflib.unified_diff(_LIBRARY, mutant.read_text(encoding="utf-8").splitlines(), n=0, lineterm="")
    changed = [line for line in diff if line[:1] in "+-" and not line.startswith(("+++", "---"))]
    assert len(changed) == 2, changed
