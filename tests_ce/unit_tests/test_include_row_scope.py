"""An <include> inside a <generate> runs once for each row. The row's values are visible to the step only."""

import pytest

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


def test_the_step_reads_the_row_variable(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "inner.xml").write_text(
        '<setup><generate name="seen" count="1"><key name="seen" script="who"/></generate></setup>', encoding="utf-8"
    )
    (tmp_path / "datamimic.xml").write_text(
        '<setup><generate name="outer" count="2"><variable name="who" script="\'row-\' + str(1)"/>'
        '<include uri="inner.xml"/><key name="id" script="1"/></generate></setup>',
        encoding="utf-8",
    )
    engine = DataMimicTest(test_dir=tmp_path, filename="datamimic.xml", capture_test_result=True)
    engine.test_with_timer()
    assert {row["seen"] for row in engine.capture_result()["seen"]} == {"row-1"}


def test_a_later_sibling_cannot_read_a_row_variable_of_the_include(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "inner.xml").write_text(
        '<setup><generate name="seen" count="1"><key name="seen" script="leak"/></generate></setup>', encoding="utf-8"
    )
    (tmp_path / "datamimic.xml").write_text(
        '<setup><generate name="outer" count="2"><variable name="leak" constant="row"/>'
        '<include uri="inner.xml"/><key name="id" constant="1"/></generate>'
        '<generate name="after" count="1"><key name="v" script="leak"/></generate></setup>',
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="leak"):
        DataMimicTest(test_dir=tmp_path, filename="datamimic.xml").test_with_timer()
