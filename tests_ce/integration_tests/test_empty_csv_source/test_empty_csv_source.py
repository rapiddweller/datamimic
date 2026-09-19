from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


def test_empty_csv_source_yields_zero_records():
    engine = DataMimicTest(
        test_dir=Path(__file__).resolve().parent, filename="empty_csv_source.xml", capture_test_result=True
    )
    engine.test_with_timer()
    assert engine.capture_result().get("g", []) == []
