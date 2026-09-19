import shutil
from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def _clean():
    shutil.rmtree(_DIR / "output", ignore_errors=True)


def _run(f):
    DataMimicTest(test_dir=_DIR, filename=f, capture_test_result=True).test_with_timer()


def test_exporturi_puts_the_file_under_that_prefix():
    _clean()
    try:
        _run("csv_uri.xml")
        under_prefix = list((_DIR / "output" / "reports" / "2026").glob("rows*.csv"))
        assert under_prefix, f"no rows.csv under output/reports/2026 (tree: {[str(p.relative_to(_DIR)) for p in (_DIR/'output').rglob('*.csv')]})"
    finally:
        _clean()


def test_without_exporturi_the_default_task_id_dir_is_unchanged():
    _clean()
    try:
        _run("csv_default.xml")
        # not under a 'reports' prefix; still lands somewhere under output/
        assert list((_DIR / "output").rglob("rows*.csv"))
        assert not (_DIR / "output" / "reports").exists()
    finally:
        _clean()


@pytest.mark.parametrize("f,msg", [
    ("uri_traversal.xml", r"path|traversal|\.\."),
    ("uri_scheme.xml", r"scheme|://"),
])
def test_invalid_exporturi_is_rejected(f, msg):
    with pytest.raises(Exception, match=msg):
        _run(f)


def test_exporturi_works_for_json_too():
    _clean()
    try:
        _run("json_uri.xml")
        assert list((_DIR / "output" / "out" / "json").glob("rows*.json"))
    finally:
        _clean()
