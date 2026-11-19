# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.
"""Run output of the CLI: one channel for user errors, one descriptor location, quiet INFO log (#547)."""

import json
import logging
import re
import subprocess
import sys
from pathlib import Path

import pytest
import typer
from lxml import etree

from datamimic_ce.engine.dsl.parsers.document.descriptor_parser import _invalid_xml
from datamimic_ce.errors.codes import IssueCode
from datamimic_ce.errors.factory import parser_validation_error
from datamimic_ce.interfaces.cli import presenter


def test_failed_run_ends_with_the_cli_error_line(tmp_path: Path) -> None:
    # Scripts and the integration tests read the `Error: [Exxx/Iyyy]` line; the run log keeps its own record.
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text("<setup", encoding="utf-8")
    result = subprocess.run(
        [str(Path(sys.executable).with_name("datamimic")), "run", str(descriptor)], capture_output=True, text=True
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert re.search(
        r"^Error: \[E\d+/I\d+\] .*Descriptor validation error: XML is not well-formed", result.stderr, re.MULTILINE
    )
    assert "Descriptor XML" not in result.stderr
    assert " | ERROR | DATAMIMIC" in result.stderr


def test_failed_run_retains_error_record(tmp_path: Path) -> None:
    from datamimic_ce.interfaces.cli.runtime import execute_descriptor

    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text("<setup", encoding="utf-8")
    records: list[logging.LogRecord] = []

    class Collector(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logger = logging.getLogger("DATAMIMIC")
    collector = Collector()
    logger.addHandler(collector)
    try:
        with pytest.raises(typer.Exit) as caught:
            execute_descriptor(descriptor, None, None, False)
    finally:
        logger.removeHandler(collector)
    assert caught.value.exit_code == 1
    assert (
        sum(
            r.levelno == logging.ERROR and "Descriptor validation error: XML is not well-formed" in r.getMessage()
            for r in records
        )
        == 1
    )


def test_error_before_runner_is_presented(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    from datamimic_ce.interfaces.cli import runtime

    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text("<setup/>", encoding="utf-8")

    def fail_loading(path: Path) -> dict[str, str]:
        raise parser_validation_error(code=IssueCode.PARSER_DESCRIPTOR_NOT_FOUND, name=path.name)

    monkeypatch.setattr(runtime, "load_descriptor_properties", fail_loading)
    with pytest.raises(typer.Exit):
        runtime.execute_descriptor(descriptor, None, None, False)
    # Count CLI result lines only; a stale log handler from an earlier CliRunner test can add "ValueError: " noise.
    assert len(re.findall(r"^Error: ", capsys.readouterr().err, re.MULTILINE)) == 1


@pytest.mark.parametrize(
    ("options", "message"),
    [
        (["--param", "oops"], "--param requires NAME=VALUE"),
        (["--platform-configs", "[1]"], "--platform-configs must be a JSON object"),
    ],
)
def test_run_option_error_is_still_presented_once(tmp_path: Path, options: list[str], message: str) -> None:
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text("<setup/>", encoding="utf-8")
    result = subprocess.run(
        [str(Path(sys.executable).with_name("datamimic")), "run", str(descriptor), *options],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert result.stderr.count(f"Error: {message}") == 1


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


def test_refused_init_does_not_leave_a_new_project_directory(tmp_path: Path, monkeypatch) -> None:
    from typer.testing import CliRunner

    from datamimic_ce.interfaces.cli import app, runtime

    def refuse(project_dir: Path, *, overwrite: bool) -> None:
        raise ValueError("starter path is unsafe")

    monkeypatch.setattr(runtime, "create_project_structure", refuse)
    result = CliRunner().invoke(app, ["init", "refused", "--target", str(tmp_path)])
    assert result.exit_code == 1
    assert not (tmp_path / "refused").exists()
