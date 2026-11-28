# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Level names are formatted for DATAMIMIC lines only; RUNTIME_ENVIRONMENT is read when asked (#725)."""

import io
import logging

import pytest

from datamimic_ce.engine.runtime.lifecycle.config import get_settings
from datamimic_ce.engine.runtime.logging import setup_logger


@pytest.mark.parametrize(
    ("level", "padded", "standard"),
    [
        (logging.DEBUG, "DEBUG", "DEBUG"),
        (logging.INFO, "INFO ", "INFO"),
        (logging.WARNING, "WARN ", "WARNING"),
        (logging.ERROR, "ERROR", "ERROR"),
        (logging.CRITICAL, "CRTCL", "CRITICAL"),
    ],
)
def test_datamimic_lines_pad_level_names_and_a_foreign_logger_keeps_its_own(
    capsys: pytest.CaptureFixture[str], level: int, padded: str, standard: str
) -> None:
    setup_logger("T725", "MAIN", level=logging.DEBUG)
    own = logging.getLogger("T725")
    foreign = logging.getLogger("T725-foreign")
    foreign_stream = io.StringIO()
    handler = logging.StreamHandler(foreign_stream)
    handler.setFormatter(logging.Formatter("%(levelname)s|%(message)s"))
    foreign.addHandler(handler)
    foreign.propagate = False
    foreign.setLevel(logging.DEBUG)
    try:
        own.log(level, "hello")
        foreign.log(level, "hello")
        assert f" | {padded} | T725 " in capsys.readouterr().err
        assert foreign_stream.getvalue() == f"{standard}|hello\n"
        assert logging.getLevelName(level) == standard
    finally:
        for log in (own, foreign):
            for h in log.handlers[:]:
                log.removeHandler(h)
                h.close()


@pytest.mark.parametrize(("first", "second"), [("production", "development"), ("development", "production")])
def test_runtime_environment_change_within_a_process_is_honoured(
    monkeypatch: pytest.MonkeyPatch, first: str, second: str
) -> None:
    monkeypatch.setenv("RUNTIME_ENVIRONMENT", first)
    assert first == get_settings().RUNTIME_ENVIRONMENT
    monkeypatch.setenv("RUNTIME_ENVIRONMENT", second)
    assert second == get_settings().RUNTIME_ENVIRONMENT
    monkeypatch.delenv("RUNTIME_ENVIRONMENT")
    assert get_settings().RUNTIME_ENVIRONMENT == "production"


def test_unchanged_environment_returns_the_same_settings_object() -> None:
    assert get_settings() is get_settings()
