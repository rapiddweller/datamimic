"""weights= and unique= take effect on <element values=> (#465): the element runtime reads both."""

from pathlib import Path

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def test_element_values_honour_weights_and_unique() -> None:
    engine = DataMimicTest(test_dir=_DIR, filename="element_values_weights_unique.xml", capture_test_result=True)
    engine.test_with_timer()
    holders = [row["holder"] for row in engine.capture_result()["g"]]
    assert {holder["@weighted"] for holder in holders} == {"b"}
    assert len({holder["@distinct"] for holder in holders}) == 12
