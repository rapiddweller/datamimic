from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


def test_include_uri_is_resolved_from_a_variable():
    engine = DataMimicTest(
        test_dir=Path(__file__).resolve().parent, filename="dynamic_include.xml", capture_test_result=True
    )
    engine.test_with_timer()
    rows = engine.capture_result()["g"]
    assert len(rows) == 7  # product_count from the dynamically-included properties file
    assert all(r["r"] == "EU" for r in rows)  # region from the same file
