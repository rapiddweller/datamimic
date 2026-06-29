# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Generated credit card numbers must be Luhn-valid (ISO/IEC 7812-1).

Surface: engine (datamimic_ce, finance domain). The validator below is an
independent mod-10 check (verification pass), deliberately NOT the production
luhn_check_digit, so it genuinely cross-checks the generated numbers.
"""

from __future__ import annotations

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _luhn_is_valid(number: str) -> bool:
    """Standard Luhn validation pass: double every 2nd digit from the right
    (the check digit at index 0 is not doubled); the total must be a multiple of 10."""
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _run(filename: str) -> dict:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_card_numbers_are_luhn_valid():
    rows = _run("credit_card_luhn.xml")["cards"]
    assert len(rows) == 50
    for r in rows:
        num = r["card_number"]
        assert num.isdigit(), f"non-numeric card number: {num!r}"
        assert _luhn_is_valid(num), f"card number fails Luhn: {num}"


def test_luhn_validator_rejects_tampered():
    # guard the test's own validator: a tampered valid number must fail
    assert _luhn_is_valid("79927398713")
    assert not _luhn_is_valid("79927398714")
