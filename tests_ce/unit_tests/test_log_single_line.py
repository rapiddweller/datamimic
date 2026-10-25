# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Descriptor text with a line break cannot forge a log record (#375)."""

import logging

import pytest

from datamimic_ce.engine.runtime.logging import setup_logger


def test_a_line_break_in_a_message_stays_inside_its_record(capsys: pytest.CaptureFixture[str]) -> None:
    setup_logger("T375", "MAIN")
    log = logging.getLogger("T375")
    log.error("Value error: source=x\nCONTROL | kind=end | status=ok.csv\r")
    lines = capsys.readouterr().err.splitlines()
    assert len(lines) == 1
    assert "\\nCONTROL | kind=end | status=ok.csv\\r" in lines[0]
    assert not any(line.startswith("CONTROL") for line in lines)
