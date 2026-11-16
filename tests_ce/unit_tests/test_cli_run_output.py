# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.
"""Run output of the CLI: one channel for user errors, one descriptor location, quiet INFO log (#547)."""

import json
import logging
from pathlib import Path

import pytest
import typer
from lxml import etree

from datamimic_ce.engine.dsl.parsers.document.descriptor_parser import _invalid_xml
from datamimic_ce.errors.codes import IssueCode
from datamimic_ce.errors.factory import parser_validation_error
from datamimic_ce.interfaces.cli import presenter


def test_text_error_goes_to_stderr_only(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(typer.Exit):
        presenter.fail("boom", code=1)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "Error: boom\n"


def test_json_error_keeps_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(typer.Exit):
        presenter.fail("boom", presenter.CliOutputFormat.JSON, code=1)
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"ok": False, "error": "boom"}
    assert captured.err == ""


def test_not_well_formed_message_names_descriptor_and_location_once() -> None:
    with pytest.raises(etree.XMLSyntaxError) as caught:
        etree.fromstring(b"<setup")
    message = str(_invalid_xml(caught.value, "datamimic.xml"))
    assert message.count("datamimic.xml") == 1
    assert message.count("line ") == 1
    assert "uploaded assets" not in message
    assert "project environment" not in message


def test_descriptor_hint_still_appended_without_location_descriptor() -> None:
    error = parser_validation_error(
        code=IssueCode.PARSER_DESCRIPTOR_NOT_FOUND, name="missing.xml", descriptor_name="datamimic.xml"
    )
    assert "uploaded assets" not in str(error)
    assert str(error).count("datamimic.xml") == 1


def test_starter_run_logs_one_saving_line_per_exporter_without_init_noise(tmp_path: Path) -> None:
    from datamimic_ce.interfaces.cli.runtime import execute_descriptor

    (tmp_path / "datamimic.xml").write_text(
        '<setup><generate name="people" count="3" target="CSV,JSON"><key name="id" generator="IncrementGenerator"/>'
        "</generate></setup>"
    )
    records: list[str] = []

    class Collector(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            if record.levelno >= logging.INFO:
                records.append(record.getMessage())

    logger = logging.getLogger("DATAMIMIC")
    collector = Collector(logging.DEBUG)
    logger.addHandler(collector)
    try:
        execute_descriptor(tmp_path / "datamimic.xml", None, None, False)
    finally:
        logger.removeHandler(collector)
    info = records
    assert not [
        m for m in info if "initialized with chunk size" in m or "processing page" in m or "default page size" in m
    ]
    saving = [m for m in info if "Saving exported result" in m]
    assert len(saving) == 2
    assert any("CSV" in m.upper() for m in saving) and any("JSON" in m.upper() for m in saving)
    assert len(set(saving)) == 2
