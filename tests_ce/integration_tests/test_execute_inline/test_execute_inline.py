# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# See LICENSE file for the full text of the license.

"""Inline <execute> code: python (flat statement), sql (against a db), bash (side-effect + warning)."""

import logging
from pathlib import Path

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
