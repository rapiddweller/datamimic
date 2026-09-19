import shutil
from collections import Counter
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


_LARGE_FIXTURE_LEN = 12


def _write_large_fixture() -> Path:
    fixture = _DIR / "people_fixture_large.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(["name", "score"])
    for i in range(_LARGE_FIXTURE_LEN):
        ws.append([f"n{i:02d}", i])
    wb.save(fixture)
    return fixture


def _run(filename: str) -> list[dict]:
    engine = DataMimicTest(test_dir=_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()["rows"]


def test_xlsx_paged_ordered_read_preserves_source_order():
    fixture = _write_large_fixture()
    try:
        rows = _run("read_paged_ordered.xml")  # pageSize=5 < 12 source rows -> 3 pages
        assert [r["idx"] for r in rows] == list(range(_LARGE_FIXTURE_LEN))
    finally:
        fixture.unlink(missing_ok=True)
        shutil.rmtree(_DIR / "output", ignore_errors=True)


def test_xlsx_random_read_is_seeded_deterministic():
    fixture = _write_large_fixture()
    try:
        first = [r["idx"] for r in _run("read_random_seeded.xml")]
        second = [r["idx"] for r in _run("read_random_seeded.xml")]
        assert first == second  # same rngSeed -> same shuffle every run
        assert sorted(first) == list(range(_LARGE_FIXTURE_LEN))  # still a full permutation
        assert first != list(range(_LARGE_FIXTURE_LEN))  # actually shuffled, not coincidentally ordered
    finally:
        fixture.unlink(missing_ok=True)
        shutil.rmtree(_DIR / "output", ignore_errors=True)


def test_xlsx_random_read_is_unseeded_nondeterministic():
    fixture = _write_large_fixture()
    try:
        rows = [r["idx"] for r in _run("read_random_unseeded.xml")]
        assert sorted(rows) == list(range(_LARGE_FIXTURE_LEN))  # valid permutation regardless of seed
    finally:
        fixture.unlink(missing_ok=True)
        shutil.rmtree(_DIR / "output", ignore_errors=True)


def test_xlsx_cumulated_read_is_seeded_and_bell_weighted():
    fixture = _write_large_fixture()
    try:
        first = [r["idx"] for r in _run("read_cumulated_seeded.xml")]
        second = [r["idx"] for r in _run("read_cumulated_seeded.xml")]
        assert first == second  # deterministic under rngSeed
        assert len(first) == 200
        assert set(first) <= set(range(_LARGE_FIXTURE_LEN))  # only real source indices, sampled with replacement

        counts = Counter(first)
        middle = counts[_LARGE_FIXTURE_LEN // 2] + counts[_LARGE_FIXTURE_LEN // 2 - 1]
        edges = counts[0] + counts[_LARGE_FIXTURE_LEN - 1]
        assert middle > edges  # bell shape: middle rows drawn more often than edge rows
    finally:
        fixture.unlink(missing_ok=True)
        shutil.rmtree(_DIR / "output", ignore_errors=True)


def test_xlsx_cyclic_read_wraps_across_pages():
    fixture = _write_large_fixture()
    try:
        rows = _run("read_cyclic_paged.xml")  # count=26, pageSize=7, source len=12
        assert [r["idx"] for r in rows] == [i % _LARGE_FIXTURE_LEN for i in range(26)]
    finally:
        fixture.unlink(missing_ok=True)
        shutil.rmtree(_DIR / "output", ignore_errors=True)
