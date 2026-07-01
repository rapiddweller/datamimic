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


@pytest.mark.parametrize(
    "filename,match",
    [
        ("while_no_condition.xml", "condition"),  # required attribute missing
        ("while_empty_condition.xml", "empty"),  # condition=""
    ],
)
def test_while_invalid_condition_raises(filename, match):
    with pytest.raises(Exception, match=match):
        _run(filename)


def _luhn_ok(number: int) -> bool:
    digits = [int(c) for c in str(number)]
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d = d * 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def test_while_steps_to_next_luhn_valid_pan():
    # search — step each source value up (+1) to the next Luhn-valid PAN (a payment-testing staple)
    pans = [r["pan"] for r in _run("while_luhn_next_valid.xml", gen="cards")]
    assert len(pans) == 6
    assert all(_luhn_ok(p) for p in pans)
    # deterministic: same run, same PANs (DATAMIMIC's core promise)
    assert pans == [r["pan"] for r in _run("while_luhn_next_valid.xml", gen="cards")]


def test_while_compound_growth_counts_iterations():
    # iterative accumulation — years for a balance to double at 10% p.a. (1000 -> >2000)
    row = _run("while_compound_growth.xml", gen="accounts")[0]
    assert row["years"] == 8
    assert row["balance"] > 2000
