from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from datamimic_ce.engine.io.exporters.formats.json_exporter import JsonExporter
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

REPO = Path(__file__).resolve().parents[2]


def _write_descriptor(directory: Path, *, multiprocessing: bool) -> None:
    directory.mkdir()
    setup = 'multiprocessing="True" numProcess="2"' if multiprocessing else 'multiprocessing="0"'
    (directory / "rows.xml").write_text(
        f'<setup {setup}><generate name="rows" count="5" target="JSON(chunk_size=2)" '
        'exportUri="results"><key name="id" generator="IncrementGenerator"/>'
        "</generate></setup>",
        encoding="utf-8",
    )


def _read_exported_ids(directory: Path) -> tuple[list[Path], list[int]]:
    files = sorted((directory / "output" / "results").glob("rows*.json"))
    ids = [row["id"] for path in files for row in json.loads(path.read_text(encoding="utf-8"))]
    return files, ids


@pytest.mark.parametrize("multiprocessing", [False, True], ids=["single", "multi"])
def test_generate_finalizes_all_buffered_json_chunks(tmp_path: Path, multiprocessing: bool) -> None:
    directory = tmp_path / ("multi" if multiprocessing else "single")
    _write_descriptor(directory, multiprocessing=multiprocessing)

    DataMimicTest(test_dir=directory, filename="rows.xml").test_with_timer()

    files, ids = _read_exported_ids(directory)
    assert len(files) == 3
    assert len(ids) == 5
    assert sorted(ids) == [1, 2, 3, 4, 5]
    if not multiprocessing:
        assert [path.name for path in files] == ["rows_0.json", "rows_1.json", "rows_2.json"]
        assert [path.read_bytes() for path in files] == [
            b'[\n{"id": 1},\n{"id": 2}]',
            b'[\n{"id": 3},\n{"id": 4}]',
            b'[\n{"id": 5}]',
        ]


def test_single_process_export_session_does_not_leak_into_later_mp_workers(tmp_path: Path) -> None:
    descriptor = tmp_path / "mixed_workers.xml"
    descriptor.write_text(
        '<setup multiprocessing="0">'
        '<generate name="warmup" count="1" target="">'
        '<key name="id" generator="IncrementGenerator"/>'
        "</generate>"
        '<generate name="rows" count="4" numProcess="2" target="JSON(chunk_size=2)" '
        'exportUri="results"><key name="id" generator="IncrementGenerator"/>'
        "</generate></setup>",
        encoding="utf-8",
    )
    run = (
        "import sys; from pathlib import Path; "
        "from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest; "
        "DataMimicTest(test_dir=Path(sys.argv[1]), filename='mixed_workers.xml').test_with_timer()"
    )

    completed = subprocess.run(
        [sys.executable, "-c", run, str(tmp_path)],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(REPO)},
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert completed.returncode == 0, completed.stderr
    files = sorted((tmp_path / "output" / "results").glob("rows*.json"))
    ids = [row["id"] for path in files for row in json.loads(path.read_text(encoding="utf-8"))]
    assert len(files) == 2
    assert len(ids) == 4
    assert sorted(ids) == [1, 2, 3, 4]


def test_mixed_buffered_targets_publish_all_chunks(tmp_path: Path) -> None:
    descriptor = tmp_path / "mixed_targets.xml"
    descriptor.write_text(
        '<setup multiprocessing="0"><generate name="rows" count="3" '
        'target="JSON(chunk_size=2),CSV(chunk_size=2)" exportUri="results">'
        '<key name="id" generator="IncrementGenerator"/>'
        "</generate></setup>",
        encoding="utf-8",
    )

    DataMimicTest(test_dir=tmp_path, filename=descriptor.name).test_with_timer()

    output = tmp_path / "output" / "results"
    json_files = sorted(output.glob("rows_*.json"))
    csv_files = sorted(output.glob("rows_*.csv"))
    assert [row["id"] for path in json_files for row in json.loads(path.read_text(encoding="utf-8"))] == [1, 2, 3]
    csv_rows = [
        row
        for path in csv_files
        for row in csv.DictReader(path.read_text(encoding="utf-8").splitlines())
    ]
    assert [row["id"] for row in csv_rows] == ["1", "2", "3"]
    assert len(json_files) == len(csv_files) == 2


@pytest.mark.parametrize(
    "wrapped",
    [
        pytest.param(False, id="direct-child"),
        pytest.param(
            True,
            id="condition-child",
            marks=pytest.mark.xfail(
                strict=True,
                reason="step-14-export-lifecycle.md: conditional child artifacts are not published",
            ),
        ),
    ],
)
def test_nested_buffered_child_is_finalized_and_published(tmp_path: Path, wrapped: bool) -> None:
    descriptor = tmp_path / "nested.xml"
    child = (
        '<generate name="children" count="3" target="JSON(chunk_size=2)" exportUri="results">'
        '<key name="id" generator="IncrementGenerator"/>'
        "</generate>"
    )
    nested = f"<condition><if condition=\"True\">{child}</if></condition>" if wrapped else child
    descriptor.write_text(
        '<setup multiprocessing="0"><generate name="parents" count="1" target="">'
        '<key name="id" generator="IncrementGenerator"/>'
        f"{nested}</generate></setup>",
        encoding="utf-8",
    )

    DataMimicTest(test_dir=tmp_path, filename=descriptor.name).test_with_timer()

    files = sorted((tmp_path / "output" / "results").glob("children_*.json"))
    ids = [row["id"] for path in files for row in json.loads(path.read_text(encoding="utf-8"))]
    assert len(files) == 2
    assert ids == [1, 2, 3]


def test_finalization_failure_does_not_publish_buffered_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    descriptor = tmp_path / "failed_finalize.xml"
    descriptor.write_text(
        '<setup multiprocessing="0"><generate name="rows" count="2" '
        'target="JSON(chunk_size=2)" exportUri="results">'
        '<key name="id" generator="IncrementGenerator"/>'
        "</generate></setup>",
        encoding="utf-8",
    )

    def fail_finalize(_self: JsonExporter, _worker_id: int) -> None:
        raise RuntimeError("finalization failed")

    monkeypatch.setattr(JsonExporter, "finalize_chunks", fail_finalize)
    with pytest.raises(RuntimeError, match="finalization failed"):
        DataMimicTest(test_dir=tmp_path, filename=descriptor.name).test_with_timer()

    assert not (tmp_path / "output" / "results").exists()
    assert not list(tmp_path.glob("temp_result_*"))
