# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import logging
import re
from pathlib import Path

import pytest

from datamimic_ce.errors import factory
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def _warnings(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch, model: str) -> list[str]:
    monkeypatch.setattr(factory, "_emitted_warnings", set())
    logger = logging.getLogger("DATAMIMIC")
    monkeypatch.setattr(logger, "propagate", False)
    logger.addHandler(caplog.handler)
    try:
        DataMimicTest(test_dir=_DIR, filename=model, capture_test_result=True).test_with_timer()
    finally:
        logger.removeHandler(caplog.handler)
    return [record.getMessage() for record in caplog.records if "[W008]" in record.getMessage()]


def test_a_seeded_script_that_draws_while_it_loads_is_named_with_file_and_line(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    messages = _warnings(caplog, monkeypatch, "seeded.xml")
    assert len(messages) == 3
    assert any("'leaky.scr.py' line 3" in message for message in messages)  # BOOT = random.randint(...)
    assert any("'leaky.scr.py' line 6" in message for message in messages)  # salt=random.random()
    assert any("'leaky.scr.py' line 7" in message for message in messages)  # import uuid in the body
    assert not any("random.randint" in message for message in messages)  # never source text


def test_drawing_inside_a_function_from_a_module_import_is_not_warned(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert _warnings(caplog, monkeypatch, "clean.xml") == []


def test_an_unseeded_run_reports_nothing(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    assert _warnings(caplog, monkeypatch, "unseeded.xml") == []


def _reported(messages: list[str]) -> set[tuple[str, int]]:
    return {
        (m.group(1), int(m.group(2)))
        for m in (re.search(r"'([^']+)' line (\d+)", message) for message in messages)
        if m
    }


def _marked_lines() -> set[tuple[str, int]]:
    """The lines a script marks with `# W008`: the expectation sits next to the code a reviewer reads."""
    return {
        (path.name, number)
        for path in sorted((_DIR / "script" / "flagged").glob("*.scr.py"))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if line.rstrip().endswith("# W008")
    }


def test_every_flagged_script_is_reported_on_exactly_its_marked_line(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    messages = _warnings(caplog, monkeypatch, "flagged.xml")
    assert len(_marked_lines()) == len(list((_DIR / "script" / "flagged").glob("*.scr.py")))  # one mark per script
    assert _reported(messages) == _marked_lines()
    assert len(messages) == len(_marked_lines())  # nothing is reported twice


def test_no_quiet_script_is_reported(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    assert _warnings(caplog, monkeypatch, "quiet.xml") == []


def test_inline_code_is_named_inline(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    messages = _warnings(caplog, monkeypatch, "inline.xml")
    assert [message for message in messages if "'inline'" in message and "line 2" in message] != []


def _rows(model: str) -> list[dict]:
    engine = DataMimicTest(test_dir=_DIR, filename=model, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()["rows"]


def test_a_load_time_draw_breaks_the_replay_that_the_seed_promises() -> None:
    assert _rows("replay_leaky.xml") != _rows("replay_leaky.xml")


def test_a_draw_inside_a_function_replays_with_the_same_seed() -> None:
    assert _rows("replay_quiet.xml") == _rows("replay_quiet.xml")
