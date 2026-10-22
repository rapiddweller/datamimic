# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""CONTROL lines are asserted by meaning: one kind=end per run, and only on stderr."""

import logging
import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from datamimic_ce.engine.runtime.api import create_run_session
from datamimic_ce.engine.runtime.contracts import RunRequest
from datamimic_ce.errors import UserErrorBase

REPO_ROOT = Path(__file__).resolve().parents[2]
OK_DESCRIPTOR = '<setup><generate name="a" count="1"><key name="v" constant="ok"/></generate></setup>'
BAD_DESCRIPTOR = '<setup><generate name="a" count="1"><bogus/></generate></setup>'


def _parse(message: str) -> dict[str, str]:
    return dict(part.split("=", 1) for part in message.split(" | ")[1:])


def _end_events(records: list[logging.LogRecord]) -> list[dict[str, str]]:
    parsed = [_parse(record.getMessage()) for record in records if record.getMessage().startswith("CONTROL |")]
    return [event for event in parsed if event["kind"] == "end"]


@pytest.fixture
def dm_caplog(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    # The DATAMIMIC logger sets propagate=False, so caplog must be attached to it directly.
    logger = logging.getLogger("DATAMIMIC")
    logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.INFO, logger="DATAMIMIC"):
            yield caplog
    finally:
        logger.removeHandler(caplog.handler)


def test_ok_run_logs_exactly_one_end_event(tmp_path: Path, dm_caplog: pytest.LogCaptureFixture) -> None:
    descriptor = tmp_path / "ok.xml"
    descriptor.write_text(OK_DESCRIPTOR, encoding="utf-8")

    create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True)).execute()

    assert _end_events(dm_caplog.records) == [{"kind": "end", "status": "ok"}]


def test_failed_run_logs_one_end_event_with_error_type(tmp_path: Path, dm_caplog: pytest.LogCaptureFixture) -> None:
    descriptor = tmp_path / "bad.xml"
    descriptor.write_text(BAD_DESCRIPTOR, encoding="utf-8")

    with pytest.raises(UserErrorBase) as raised:
        create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True)).execute()

    assert _end_events(dm_caplog.records) == [{"kind": "end", "status": "error", "reason": type(raised.value).__name__}]


def test_control_lines_go_to_stderr_only(tmp_path: Path) -> None:
    # Subprocess, not the console script: that entry point imports the main checkout, not this worktree.
    for name, descriptor_text, should_succeed in (("ok", OK_DESCRIPTOR, True), ("bad", BAD_DESCRIPTOR, False)):
        descriptor = tmp_path / f"{name}.xml"
        descriptor.write_text(descriptor_text, encoding="utf-8")
        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                "from datamimic_ce.interfaces.cli.__main__ import main; main()",
                "run",
                str(descriptor),
            ],
            cwd=REPO_ROOT,
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
            capture_output=True,
            text=True,
            check=False,
        )

        assert (proc.returncode == 0) == should_succeed
        assert "CONTROL |" not in proc.stdout
        # The stderr formatter prefixes each line with timestamp/level/worker, so the event starts mid-line.
        stderr_control = [line[line.index("CONTROL |") :] for line in proc.stderr.splitlines() if "CONTROL |" in line]
        end_events = [_parse(line) for line in stderr_control if _parse(line)["kind"] == "end"]
        assert len(end_events) == 1
        assert end_events[0]["status"] == ("ok" if should_succeed else "error")
