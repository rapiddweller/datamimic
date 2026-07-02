from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def _run(filename: str) -> list[dict]:
    engine = DataMimicTest(test_dir=_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()["g"]


def test_substring_slices_like_python():
    row = _run("substring.xml")[0]
    assert row["last4"] == "5861"  # Substring(-4): tail extract
    assert row["area"] == "171"  # Substring(5, 8): window
    assert row["from2"] == "49-171-2635861"  # Substring(2): from index to end


def test_substring_rejects_non_string():
    with pytest.raises(Exception, match=r"Substring.*string"):
        _run("substring_invalid.xml")
