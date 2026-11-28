# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.
"""Run real descriptors with every exporter finalized twice; the published output must not change."""

import shutil
from pathlib import Path

import pytest
from lxml import etree
from openpyxl import load_workbook

from datamimic_ce.engine.io.exporters.core.unified_buffered_exporter import UnifiedBufferedExporter
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


@pytest.fixture
def finalize_twice(monkeypatch: pytest.MonkeyPatch) -> None:
    original = UnifiedBufferedExporter.finalize_chunks

    def twice(self: UnifiedBufferedExporter, worker_id: int) -> None:
        original(self, worker_id)
        original(self, worker_id)

    monkeypatch.setattr(UnifiedBufferedExporter, "finalize_chunks", twice)


def _ids_xlsx(path: Path) -> list[int]:
    return [int(row[0]) for row in list(load_workbook(path).active.iter_rows(values_only=True))[1:]]


def _ids_dbunit(path: Path) -> list[int]:
    return [int(row.get("id")) for row in etree.parse(str(path)).getroot()]


# Each descriptor is one equivalence class: empty output, one row, many rows in one file, many rows in chunks.
# DbUnit ignores chunk_size (one document per table), so its chunked descriptor yields one file.
_CASES = [
    ("finalize_twice_xlsx_empty.xml", "xlsx", _ids_xlsx, []),
    ("finalize_twice_xlsx_one_row.xml", "xlsx", _ids_xlsx, [[1]]),
    ("finalize_twice_xlsx_unchunked.xml", "xlsx", _ids_xlsx, [[1, 2, 3, 4, 5]]),
    ("finalize_twice_xlsx_chunked.xml", "xlsx", _ids_xlsx, [[1, 2], [3, 4], [5]]),
    ("finalize_twice_dbunit_empty.xml", "dbunit.xml", _ids_dbunit, []),
    ("finalize_twice_dbunit_one_row.xml", "dbunit.xml", _ids_dbunit, [[1]]),
    ("finalize_twice_dbunit_unchunked.xml", "dbunit.xml", _ids_dbunit, [[1, 2, 3, 4, 5]]),
    ("finalize_twice_dbunit_chunked.xml", "dbunit.xml", _ids_dbunit, [[1, 2, 3, 4, 5]]),
]


@pytest.mark.parametrize(("descriptor", "suffix", "read_ids", "expected"), _CASES, ids=[c[0] for c in _CASES])
def test_repeated_finalize_leaves_rows_unchanged(
    finalize_twice: None, descriptor: str, suffix: str, read_ids, expected: list[list[int]]
) -> None:
    engine = DataMimicTest(test_dir=_DIR, filename=descriptor)
    engine.test_with_timer()
    out = _DIR / "output" / engine.task_id
    try:
        files = sorted(p for p in out.glob("*") if p.name.endswith(f".{suffix}")) if out.exists() else []
        assert [read_ids(p) for p in files] == expected
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_repeated_finalize_keeps_the_flattened_single_xml_item(monkeypatch: pytest.MonkeyPatch) -> None:
    def published_bytes() -> bytes:
        engine = DataMimicTest(test_dir=_DIR, filename="finalize_twice_xml_one_row.xml")
        engine.test_with_timer()
        out = _DIR / "output" / engine.task_id
        try:
            (path,) = sorted(out.glob("*.xml"))
            return path.read_bytes()
        finally:
            shutil.rmtree(out, ignore_errors=True)

    once = published_bytes()
    original = UnifiedBufferedExporter.finalize_chunks

    def twice(self: UnifiedBufferedExporter, worker_id: int) -> None:
        original(self, worker_id)
        original(self, worker_id)

    monkeypatch.setattr(UnifiedBufferedExporter, "finalize_chunks", twice)
    assert published_bytes() == once
