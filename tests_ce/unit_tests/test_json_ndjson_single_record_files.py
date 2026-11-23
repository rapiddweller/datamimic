"""An .ndjson file holds one record on one line, also with chunk_size=1."""

import json

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


def test_ndjson_with_chunk_size_one_writes_one_line_per_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "datamimic.xml").write_text(
        '<setup><generate name="rows" count="2" target="JSON(use_ndjson=True, chunk_size=1)">'
        '<key name="n" generator="IncrementGenerator"/></generate></setup>',
        encoding="utf-8",
    )
    DataMimicTest(test_dir=tmp_path, filename="datamimic.xml").test_with_timer()
    files = sorted(tmp_path.glob("output/*/rows_*.ndjson"))
    assert len(files) == 2
    for number, file in enumerate(files, start=1):
        lines = file.read_text(encoding="utf-8").splitlines()
        assert [json.loads(line) for line in lines] == [{"n": number}]
