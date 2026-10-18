import json

import pytest

from datamimic_ce.engine.runtime import logging as runtime_logging
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


@pytest.mark.parametrize("report_logging", [True, False])
def test_report_logging_controls_runtime_timing_without_changing_export(
    tmp_path, monkeypatch, report_logging: bool
) -> None:
    (tmp_path / "rows.xml").write_text(
        f'<setup multiprocessing="0" reportLogging="{str(report_logging).lower()}">'
        '<generate name="rows" count="3" target="JSON(chunk_size=2)" exportUri="results">'
        '<key name="id" generator="IncrementGenerator"/>'
        "</generate></setup>",
        encoding="utf-8",
    )
    messages: list[str] = []
    monkeypatch.setattr(runtime_logging.logger, "info", messages.append)

    DataMimicTest(test_dir=tmp_path, filename="rows.xml").test_with_timer()

    timings = [message.partition(" took")[0] for message in messages if " records 'rows' took" in message]
    assert timings == (
        [
            "Generating 3 records 'rows'",
            "Export phase for 3 records 'rows'",
            "Processing 3 records 'rows'",
        ]
        if report_logging
        else []
    )

    files = sorted((tmp_path / "output" / "results").glob("rows_*.json"))
    rows = [row for path in files for row in json.loads(path.read_text(encoding="utf-8"))]
    assert [path.name for path in files] == ["rows_0.json", "rows_1.json"]
    assert [row["id"] for row in rows] == [1, 2, 3]


@pytest.mark.parametrize("capture_test_result", [True, False])
@pytest.mark.parametrize("report_logging", [True, False])
def test_targetless_run_reports_phases_without_claiming_export(
    tmp_path, monkeypatch, capture_test_result: bool, report_logging: bool
) -> None:
    (tmp_path / "rows.xml").write_text(
        f'<setup multiprocessing="0" reportLogging="{str(report_logging).lower()}">'
        '<generate name="rows" count="3" target="">'
        '<key name="id" generator="IncrementGenerator"/>'
        "</generate></setup>",
        encoding="utf-8",
    )
    messages: list[str] = []
    monkeypatch.setattr(runtime_logging.logger, "info", messages.append)
    runner = DataMimicTest(test_dir=tmp_path, filename="rows.xml", capture_test_result=capture_test_result)

    runner.test_with_timer()

    timings = [message.partition(" took")[0] for message in messages if " records 'rows' took" in message]
    assert timings == (
        [
            "Generating 3 records 'rows'",
            "Export phase for 3 records 'rows'",
            "Processing 3 records 'rows'",
        ]
        if report_logging
        else []
    )
    assert not (tmp_path / "output").exists()
    if capture_test_result:
        assert runner.capture_result() == {"rows": [{"id": 1}, {"id": 2}, {"id": 3}]}
