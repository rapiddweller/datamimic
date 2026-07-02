import shutil
from pathlib import Path

from openpyxl import Workbook, load_workbook

from datamimic_ce.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def test_xlsx_export_writes_a_valid_workbook():
    output = _DIR / "output"
    shutil.rmtree(output, ignore_errors=True)
    try:
        DataMimicTest(test_dir=_DIR, filename="xlsx_export.xml").test_with_timer()

        files = list(_DIR.rglob("*.xlsx"))
        assert len(files) == 1, f"expected one xlsx, got {files}"

        rows = list(load_workbook(files[0]).active.iter_rows(values_only=True))
        assert rows[0] == ("id", "name", "score")  # header from field order
        assert len(rows) == 6  # header + 5 records
        assert [r[0] for r in rows[1:]] == [1, 2, 3, 4, 5]  # ids kept as numbers
        assert all(r[1] in {"Ann", "Bob", "Cy"} for r in rows[1:])
        assert all(1 <= r[2] <= 9 for r in rows[1:])  # score int in range
    finally:
        shutil.rmtree(output, ignore_errors=True)


def test_xlsx_source_is_read_row_by_row():
    fixture = _DIR / "people_fixture.xlsx"
    output = _DIR / "output"
    wb = Workbook()
    ws = wb.active
    ws.append(["name", "score"])
    ws.append(["Ann", 3])
    ws.append(["Bob", 5])
    wb.save(fixture)
    try:
        engine = DataMimicTest(test_dir=_DIR, filename="xlsx_read.xml", capture_test_result=True)
        engine.test_with_timer()
        rows = engine.capture_result()["rows"]
        assert [r["who"] for r in rows] == ["Ann", "Bob"]  # header-keyed columns
        assert [r["doubled"] for r in rows] == [6, 10]  # numbers read as numbers
    finally:
        fixture.unlink(missing_ok=True)
        shutil.rmtree(output, ignore_errors=True)
