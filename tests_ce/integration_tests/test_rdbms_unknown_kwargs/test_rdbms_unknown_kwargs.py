import shutil
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def test_unknown_connection_knobs_do_not_reach_create_engine():
    shutil.rmtree(_DIR / "db", ignore_errors=True)
    try:
        engine = DataMimicTest(test_dir=_DIR, filename="unknown_kwarg.xml", capture_test_result=True)
        engine.test_with_timer()  # must not raise "Invalid argument(s) 'clean' sent to create_engine"
        assert engine.capture_result()["g"][0]["v"] == 5
    finally:
        shutil.rmtree(_DIR / "db", ignore_errors=True)
