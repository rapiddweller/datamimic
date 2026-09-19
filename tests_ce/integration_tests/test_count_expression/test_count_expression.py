from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def _run(filename: str) -> dict:
    engine = DataMimicTest(test_dir=_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_count_accepts_an_expression():
    orders = _run("count_expression.xml")["orders"]
    assert len(orders) == 12  # {customers * orders_per_customer} = 4 * 3


def test_count_still_rejects_plain_garbage():
    with pytest.raises(Exception, match=r"digits or script"):
        _run("count_invalid.xml")
