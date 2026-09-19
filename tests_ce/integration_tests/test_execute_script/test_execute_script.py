"""<execute script="...">: the evaluated expression IS the code to run — the DSL-native way to
execute dynamically assembled statements (paired with <variable string="...__var__..."/>).
"""

import shutil
from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def _run(filename: str) -> dict:
    engine = DataMimicTest(test_dir=_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def _clean():
    shutil.rmtree(_DIR / "db", ignore_errors=True)


def test_execute_script_runs_assembled_sql():
    _clean()
    try:
        rows = _run("execute_script_sql.xml")["rows"]
        assert [(r["id"], r["note"]) for r in rows] == [(1, "a"), (2, "b")]
    finally:
        _clean()


def test_execute_script_runs_assembled_python():
    rows = _run("execute_script_python.xml")["g"]
    assert [r["v"] for r in rows] == [42, 42]


def test_execute_script_non_string_value_raises():
    _clean()
    try:
        with pytest.raises(Exception, match=r"script.*must evaluate to a string|evaluate[sd]? to.*int"):
            _run("execute_script_non_string.xml")
    finally:
        _clean()


def test_execute_script_plus_uri_is_a_parse_error():
    with pytest.raises(Exception, match=r"exactly one of"):
        _run("execute_script_and_uri.xml")


def test_execute_script_plus_inline_body_is_a_parse_error():
    with pytest.raises(Exception, match=r"exactly one of"):
        _run("execute_script_and_body.xml")
