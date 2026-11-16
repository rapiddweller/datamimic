# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.
"""Timing lines of the run log: none for a failed statement, nested ones say they are per parent invocation (#569)."""

import logging
from pathlib import Path

import pytest

from datamimic_ce.engine.runtime.api import run
from datamimic_ce.engine.runtime.contracts import RunRequest
from datamimic_ce.engine.runtime.logging import gen_timer
from datamimic_ce.errors import MissingSourceError


def timing_lines(caplog: pytest.LogCaptureFixture, level: int = logging.INFO) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno >= level and " took " in r.getMessage()]


def run_xml(tmp_path: Path, body: str) -> None:
    path = tmp_path / "model.xml"
    path.write_text(f'<setup rngSeed="7">{body}</setup>')
    run(RunRequest(descriptor_path=path, test_mode=True))


def test_failing_source_logs_no_timing_line(dm_caplog: pytest.LogCaptureFixture, tmp_path: Path) -> None:
    with pytest.raises(MissingSourceError):
        run_xml(tmp_path, '<generate name="x" source="missing.csv" count="2"><key name="a" constant="1"/></generate>')
    assert timing_lines(dm_caplog) == []


def test_successful_statement_keeps_its_timing_line(dm_caplog: pytest.LogCaptureFixture, tmp_path: Path) -> None:
    run_xml(tmp_path, '<generate name="x" count="2"><key name="a" constant="1"/></generate>')
    assert len(timing_lines(dm_caplog)) == 3  # generate, export, process


def test_nested_product_timing_says_per_parent_invocation(dm_caplog: pytest.LogCaptureFixture, tmp_path: Path) -> None:
    run_xml(
        tmp_path,
        '<generate name="customers" count="2"><key name="id" generator="IncrementGenerator"/>'
        '<generate name="orders" count="2"><key name="n" generator="IncrementGenerator"/></generate></generate>',
    )
    lines = timing_lines(dm_caplog)
    nested = [line for line in lines if "customers|orders" in line]
    top = [line for line in lines if "customers|orders" not in line]
    assert len(top) == 3
    assert len(nested) == 6  # generate, export, process once per parent row
    assert all("'customers|orders' per parent invocation took" in line for line in nested)
    assert not any("per parent invocation" in line for line in top)


@pytest.mark.parametrize("report_logging", [True, False])
def test_timer_stays_silent_on_exception(dm_caplog: pytest.LogCaptureFixture, report_logging: bool) -> None:
    with pytest.raises(ValueError), gen_timer("process", report_logging, "x"):
        raise ValueError("boom")
    assert timing_lines(dm_caplog) == []
