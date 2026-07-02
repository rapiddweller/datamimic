import shutil
from pathlib import Path

from openpyxl import load_workbook

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
