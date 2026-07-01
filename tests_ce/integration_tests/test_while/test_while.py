# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# See LICENSE file for the full text of the license.

"""<while>: a per-row loop that repeats its body while a condition holds, with a mandatory
max_iterations cap that RAISES (never silently stops)."""

from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str, gen: str = "g") -> list[dict]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()[gen]


def test_while_loops_until_condition_false():
    # each row resets n=0 and the body increments it until n reaches 3
    rows = _run("while_counter.xml")
    assert [r["final"] for r in rows] == [3, 3, 3]


def test_while_max_iterations_raises_on_infinite_loop():
    with pytest.raises(Exception, match="max_iterations"):
        _run("while_cap.xml")
