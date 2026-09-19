from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def test_iterate_reads_a_dbunit_table_via_sourceentity():
    engine = DataMimicTest(test_dir=_DIR, filename="read_shop.xml", capture_test_result=True)
    engine.test_with_timer()
    cats = engine.capture_result()["cats"]
    assert len(cats) == 28
    assert cats[0]["id"] == "FOOD"
