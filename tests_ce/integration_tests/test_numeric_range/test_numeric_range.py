from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


def _run():
    engine = DataMimicTest(test_dir=Path(__file__).resolve().parent, filename="numeric_range.xml",
                           capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()["product"]


def test_native_numeric_range_respects_bounds_and_type():
    rows = _run()
    assert len(rows) == 20
    assert all(isinstance(r["qty"], int) and 1 <= r["qty"] <= 10 for r in rows)
    assert all(0.0 <= r["price"] <= 100.0 for r in rows)
    assert all(round(r["price"], 2) == r["price"] for r in rows)  # granularity 0.01


def test_native_numeric_range_is_seeded_reproducible():
    assert [(r["qty"], r["price"]) for r in _run()] == [(r["qty"], r["price"]) for r in _run()]
