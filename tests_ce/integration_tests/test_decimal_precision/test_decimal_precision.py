# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Exact decimal generation (Benerator big_decimal -> exact money, no float drift).

Surface: engine (datamimic_ce). L3 property proof: type="decimal" produces real
Decimal values scaled to the granularity grid, with no binary-float artefact.

Determinism note: a literal <key generator="..."> is not bound to <setup rngSeed>
(see key_variable_task.py), so this asserts the *property* (exact scale, no drift),
not a fixed sequence -- which is exactly the Phase-3 "Done" clause.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str) -> dict:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_decimal_is_exact_two_dp():
    rows = _run("decimal_amount.xml")["payments"]
    assert len(rows) == 50

    for row in rows:
        for field in ("amount", "fee"):
            value = row[field]
            assert isinstance(value, Decimal), f"{field} is {type(value).__name__}, expected Decimal"
            # scale <= 2: no more than 2 decimal places
            assert -value.as_tuple().exponent <= 2, f"{field}={value} has scale > 2"
            # exact: equal to its own 2dp quantization, i.e. no 8.200000000000001 drift
            assert value == value.quantize(Decimal("0.01"))

    # generator-driven amounts respect the [0, 1000] bound
    assert all(Decimal("0") <= row["amount"] <= Decimal("1000") for row in rows)
