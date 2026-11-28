# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import uuid
from pathlib import Path

import pytest

from datamimic_ce.engine.io.exporters.core.exporter_state_manager import ExporterStateManager
from datamimic_ce.engine.io.exporters.formats.dbunit_exporter import DbUnitExporter
from datamimic_ce.engine.io.exporters.formats.json_exporter import JsonExporter
from datamimic_ce.engine.io.exporters.formats.xlsx_exporter import XLSXExporter
from datamimic_ce.engine.io.exporters.formats.xml_exporter import XMLExporter
from tests_ce.unit_tests.test_exporter.exporter_test_util import MockSetupContext, generate_mock_data, make_exporter

EXPORTERS = {"xml": XMLExporter, "json": JsonExporter, "dbunit": DbUnitExporter, "xlsx": XLSXExporter}


def _buffer_bytes(root: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def _export(kind: str, tmp_path: Path, rows: int, chunk_size: int | None, finalizations: int) -> dict[str, bytes]:
    context = MockSetupContext(task_id=f"task_{uuid.uuid4().hex}", descriptor_dir=tmp_path)
    exporter = make_exporter(
        EXPORTERS[kind],
        setup_context=context,
        product_name="movies",
        chunk_size=chunk_size,
    )
    if rows:
        exporter.consume(("movies", generate_mock_data(rows)), "movies", ExporterStateManager(1))
    for _ in range(finalizations):
        exporter.finalize_chunks(1)
    return _buffer_bytes(tmp_path)


# Equivalence classes: empty output (0 rows), one row (XML flattens it), multiple chunks (5 rows, chunk 2),
# finalize twice. A second finalize must leave the bytes of the first one unchanged.
@pytest.mark.parametrize("kind", sorted(EXPORTERS))
@pytest.mark.parametrize(
    ("rows", "chunk_size"),
    [(0, None), (1, None), (1, 1000), (5, 2), (5, None)],
    ids=["empty", "one-row", "one-row-chunked", "multi-chunk", "single-file"],
)
def test_second_finalize_is_a_no_op(kind: str, rows: int, chunk_size: int | None, tmp_path: Path) -> None:
    once = _export(kind, tmp_path / "once", rows, chunk_size, 1)
    twice = _export(kind, tmp_path / "twice", rows, chunk_size, 2)
    assert twice.keys() == once.keys()
    for name, content in once.items():
        if kind == "xlsx":
            continue  # a workbook zip embeds its creation time; compared by readability below
        assert twice[name] == content


@pytest.mark.parametrize("kind", ["xml", "json", "dbunit"])
@pytest.mark.parametrize("rows", [0, 1, 5])
def test_single_finalize_bytes_match_the_per_file_finalizer(kind: str, rows: int, tmp_path: Path) -> None:
    """One finalize_chunks equals calling the format's own finalizer once per file (the pre-change path)."""
    context = MockSetupContext(task_id=f"task_{uuid.uuid4().hex}", descriptor_dir=tmp_path / "direct")
    exporter = make_exporter(EXPORTERS[kind], setup_context=context, product_name="movies", chunk_size=2)
    if rows:
        exporter.consume(("movies", generate_mock_data(rows)), "movies", ExporterStateManager(1))
    for buffer_file in sorted((tmp_path / "direct").rglob("*.*")):
        exporter._finalize_buffer_file(buffer_file)
    direct = _buffer_bytes(tmp_path / "direct")
    assert _export(kind, tmp_path / "via", rows, 2, 1) == direct


def test_xlsx_second_finalize_keeps_rows(tmp_path: Path) -> None:
    from openpyxl import load_workbook

    twice = _export("xlsx", tmp_path, 5, 2, 2)
    total = 0
    for path in sorted(tmp_path.rglob("*.xlsx")):
        total += len(list(load_workbook(path).active.iter_rows())) - 1
    assert total == 5
    assert twice


def test_negative_control_unfinalized_buffer_differs(tmp_path: Path) -> None:
    """The comparison can fail: an unfinalized XML buffer differs from the finalized one."""
    assert _export("xml", tmp_path / "none", 3, None, 0) != _export("xml", tmp_path / "one", 3, None, 1)
