"""DSL-driven edge-case coverage for XLSX read and write:
empty / header-only / ragged / blank-header / invalid files, mixed types,
cyclic reads, nested + None + list write values, and multi-chunk volume.
"""

import shutil
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

from datamimic_ce.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def _clean():
    shutil.rmtree(_DIR / "output", ignore_errors=True)
    for f in _DIR.glob("fixture.xlsx"):
        f.unlink(missing_ok=True)


def _write_fixture(rows: list[list]):
    """Write rows (row 0 = header) to fixture.xlsx that the read descriptors point at."""
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    wb.save(_DIR / "fixture.xlsx")


def _write_raw_fixture(content: bytes):
    (_DIR / "fixture.xlsx").write_bytes(content)


def _run(filename: str, product: str = "rows") -> list[dict]:
    engine = DataMimicTest(test_dir=_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result().get(product, [])  # 0-record product is absent from the result


def _find_xlsx() -> Path:
    files = [f for f in _DIR.rglob("*.xlsx") if f.name != "fixture.xlsx"]
    assert len(files) == 1, f"expected one output xlsx, got {files}"
    return files[0]


# ---------- READ edge cases ----------


def test_read_empty_file_yields_zero_rows():
    _clean()
    try:
        _write_fixture([])  # no rows at all
        assert _run("read_count_only.xml") == []
    finally:
        _clean()


def test_read_header_only_yields_zero_rows():
    _clean()
    try:
        _write_fixture([["x", "y", "z"]])  # header, no data
        assert _run("read_count_only.xml") == []
    finally:
        _clean()


def test_read_ragged_rows_pad_and_truncate():
    _clean()
    try:
        # header x,y,z; one short row (2 cells), one long row (4 cells)
        _write_fixture([["x", "y", "z"], [1, 2], [4, 5, 6, 7]])
        rows = _run("read_xyz.xml")
        assert len(rows) == 2
        # short row: missing 3rd cell -> None; long row: 4th cell ignored, no None-keyed column.
        assert (rows[0]["rx"], rows[0]["ry"], rows[0]["rz"]) == (1, 2, None)
        assert (rows[1]["rx"], rows[1]["ry"], rows[1]["rz"]) == (4, 5, 6)
        assert None not in rows[1]  # extra 4th cell did not create a None key
    finally:
        _clean()


def test_read_blank_header_columns_are_dropped():
    _clean()
    try:
        _write_fixture([[None, "y", None], [1, 2, 3]])  # only 'y' is a real column
        rows = _run("read_count_only.xml")
        assert rows == [{"y": 2}]
    finally:
        _clean()


def test_read_invalid_file_raises_clear_error():
    _clean()
    try:
        _write_raw_fixture(b"this is plainly not a zip-based xlsx")
        with pytest.raises(Exception, match=r"Invalid XLSX file"):
            _run("read_count_only.xml")
    finally:
        _clean()


def test_read_mixed_types_and_cyclic_transform():
    _clean()
    try:
        # columns i(int) f(float) s(str) n(None); 3 source rows, cyclic to count=10
        _write_fixture(
            [
                ["i", "f", "s", "n"],
                [1, 1.5, "aa", None],
                [2, 2.5, "bb", "x"],
                [3, 3.5, "cc", None],
            ]
        )
        rows = _run("read_complex_cyclic.xml")
        assert len(rows) == 10  # cyclic wrap over 3 source rows
        # every emitted row is a correct transform of one of the 3 source rows
        expected = {1001: ("AA", 3.0, False), 1002: ("BB", 5.0, True), 1003: ("CC", 7.0, False)}
        for r in rows:
            assert (r["upper"], r["price_2"], r["has_note"]) == expected[r["id_plus"]]
        assert {r["id_plus"] for r in rows} == {1001, 1002, 1003}  # all sources seen
        assert len(rows) > len(expected)  # cyclic: rows repeat to reach count=10
    finally:
        _clean()


# ---------- WRITE edge cases ----------


def test_write_none_nested_and_list_cells():
    _clean()
    try:
        _run("write_edge.xml", product="edge")
        rows = list(load_workbook(_find_xlsx()).active.iter_rows(values_only=True))
        header = rows[0]
        assert "id" in header and "maybe_null" in header and "nested" in header
        body = rows[1:]
        assert len(body) == 3
        col = {name: i for i, name in enumerate(header)}
        assert body[0][col["maybe_null"]] is None  # None stays an empty cell
        assert body[0][col["nested"]] == '{"inner": "7"}'  # nested dict stringified as JSON
    finally:
        _clean()


def test_write_multi_chunk_keeps_all_rows():
    _clean()
    try:
        _run("write_chunked.xml", product="big")
        total = 0
        ids = set()
        for f in _DIR.rglob("*.xlsx"):
            if f.name == "fixture.xlsx":
                continue
            body = list(load_workbook(f).active.iter_rows(values_only=True))[1:]
            total += len(body)
            ids.update(r[0] for r in body)
        assert total == 250  # all rows across chunk files
        assert ids == set(range(1, 251))  # every id present exactly once
    finally:
        _clean()
