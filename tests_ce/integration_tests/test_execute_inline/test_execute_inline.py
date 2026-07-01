# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# See LICENSE file for the full text of the license.

"""Inline <execute> code: python (flat statement), sql (against a db), bash (side-effect + warning)."""

import logging
from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str, gen: str = "g") -> list[dict]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()[gen]


def test_inline_python_updates_namespace():
    rows = _run("inline_python.xml")
    assert [r["v"] for r in rows] == [42, 42]


def test_inline_sql_seeds_a_table():
    rows = _run("inline_sql.xml")
    assert [r["v"] for r in rows] == [5]


def test_inline_bash_runs_and_warns_about_determinism():
    from datamimic_ce.tasks import execute_task

    execute_task._bash_warned = False  # let the one-time nudge fire in this test
    messages: list[str] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            messages.append(record.getMessage())

    handler = _Capture()
    log = logging.getLogger("DATAMIMIC")
    log.addHandler(handler)
    try:
        rows = _run("inline_bash.xml")  # a failing shell command would raise
    finally:
        log.removeHandler(handler)

    assert len(rows) == 1
    assert any("determinism" in m and "bash" in m for m in messages)


@pytest.mark.parametrize(
    "filename,match",
    [
        ("exec_uri_and_inline.xml", "exactly one"),  # uri AND inline code
        ("exec_neither.xml", "exactly one"),  # neither uri nor inline code
        ("exec_invalid_type.xml", "must be one of"),  # type="js"
    ],
)
def test_inline_execute_invalid_raises(filename, match):
    with pytest.raises(Exception, match=match):
        _run(filename)


def test_multiline_block_defines_reusable_helper():
    # a multi-line <execute type="python"> block defines a function that generation calls per row
    assert [r["net"] for r in _run("exec_multiline_block.xml")] == [81.0, 81.0]


def test_malformed_multiline_python_raises_with_hint():
    # a broken block becomes a DATAMIMIC error pointing to <while>/<condition>/a .py file, not a raw traceback
    with pytest.raises(Exception, match="could not be parsed"):
        _run("exec_bad_multiline.xml")
