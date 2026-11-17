# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

from pathlib import Path

import pytest

from datamimic_ce.engine.io.exporters.formats.csv_exporter import CSVExporter
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


@pytest.mark.parametrize("failure_call", [0, 1, 2])
def test_csv_retry_does_not_duplicate_partial_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure_call: int
) -> None:
    (tmp_path / "rows.xml").write_text(
        '<setup multiprocessing="0"><generate name="rows" count="2" pageSize="1" '
        'target="CSV" exportUri="results"><key name="id" generator="IncrementGenerator"/>'
        "</generate></setup>",
        encoding="utf-8",
    )
    original = CSVExporter._write_data_to_buffer
    calls = 0

    def write_then_fail(self: CSVExporter, data: list[dict], worker_id: int, chunk_idx: int) -> None:
        nonlocal calls
        calls += 1
        original(self, data, worker_id, chunk_idx)
        if calls == failure_call:
            raise OSError("transient write failure")

    monkeypatch.setattr(CSVExporter, "_write_data_to_buffer", write_then_fail)
    monkeypatch.setattr(CSVExporter, "RETRY_DELAY", 0)
    DataMimicTest(tmp_path, "rows.xml").test_with_timer()
    assert (tmp_path / "output/results/rows.csv").read_text() == "id\n1\n2\n"
