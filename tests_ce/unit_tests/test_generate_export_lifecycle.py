from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

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
