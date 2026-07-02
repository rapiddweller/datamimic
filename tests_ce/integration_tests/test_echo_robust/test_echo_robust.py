from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


def test_broken_echo_placeholder_only_warns():
    engine = DataMimicTest(
        test_dir=Path(__file__).resolve().parent, filename="echo_robust.xml", capture_test_result=True
    )
    engine.test_with_timer()  # must not raise
    assert [r["v"] for r in engine.capture_result()["g"]] == ["ok", "ok"]
