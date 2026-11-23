"""A count that a generator cannot fill is a warning, not a silent success."""

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


def test_a_step_sequence_that_runs_dry_before_the_count_is_warned_about(tmp_path, monkeypatch, dm_caplog):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "datamimic.xml").write_text(
        '<setup><generate name="rows" count="5">'
        '<key name="n" type="int" min="1" max="3" distribution="step"/></generate></setup>',
        encoding="utf-8",
    )
    engine = DataMimicTest(test_dir=tmp_path, filename="datamimic.xml", capture_test_result=True)
    engine.test_with_timer()
    assert [row["n"] for row in engine.capture_result()["rows"]] == [1, 2, 3]
    assert "'rows' wrote 3 of 5 rows of this page" in dm_caplog.text


def test_a_nested_generate_that_ends_early_for_each_parent_row_does_not_warn(tmp_path, monkeypatch, dm_caplog):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "datamimic.xml").write_text(
        '<setup><generate name="parents" count="3"><key name="id" generator="IncrementGenerator"/>'
        '<generate name="kids" count="5"><key name="n" type="int" min="1" max="2" distribution="step"/></generate>'
        "</generate></setup>",
        encoding="utf-8",
    )
    DataMimicTest(test_dir=tmp_path, filename="datamimic.xml").test_with_timer()
    assert " wrote " not in dm_caplog.text
