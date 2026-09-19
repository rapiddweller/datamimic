from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


def test_this_addresses_current_scope():
    engine = DataMimicTest(
        test_dir=Path(__file__).resolve().parent, filename="this_scope.xml", capture_test_result=True
    )
    engine.test_with_timer()
    rows = engine.capture_result()["g"]
    assert len(rows) == 4
    for r in rows:
        assert r["via_this"] == r["via_bare"]  # this.base == base
        assert r["via_this"] == r["base"] * 10  # earlier sibling visible via this.*
        assert r["var_via_this"] == 7  # this.<variable> resolves too
