# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import logging
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
