from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


def _run(filename: str = "numeric_range.xml"):
    engine = DataMimicTest(test_dir=Path(__file__).resolve().parent, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()["product"]


def test_native_numeric_range_respects_bounds_and_type():
    rows = _run()
    assert len(rows) == 20
    assert all(isinstance(r["qty"], int) and 1 <= r["qty"] <= 10 for r in rows)
    assert all(0.0 <= r["price"] <= 100.0 for r in rows)
    assert all(round(r["price"], 2) == r["price"] for r in rows)  # granularity 0.01


def test_native_string_length_respects_bounds():
    rows = _run()
    assert all(isinstance(r["code"], str) and 4 <= len(r["code"]) <= 8 for r in rows)  # minLength/maxLength


def test_native_range_is_seeded_reproducible():
    # run the SAME seeded model twice and compare — numeric AND string range fields must replay identically
    keys = ("qty", "price", "code")
    first = [tuple(r[k] for k in keys) for r in _run()]
    second = [tuple(r[k] for k in keys) for r in _run()]
    assert first == second


def test_native_range_unseeded_is_random():
    # the symmetric guard: WITHOUT rngSeed, two runs of the same native-range fields must DIFFER
    keys = ("qty", "code")
    first = [tuple(r[k] for k in keys) for r in _run("numeric_range_unseeded.xml")]
    second = [tuple(r[k] for k in keys) for r in _run("numeric_range_unseeded.xml")]
    assert first != second
