# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Run the neutral CE/EE conformance cases (README.md holds the contract). Each case is a descriptor plus an
expected outcome with codes and row counts, never values. EE runs the same files in its own runner."""

import json
import logging
import shutil
from pathlib import Path

import pytest

from datamimic_ce.errors import UserErrorBase
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_CASES = Path(__file__).resolve().parent / "cases"
_END = "CONTROL | kind=end"


class _Records(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.INFO)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _control(records: list[logging.LogRecord]) -> list[str]:
    """Each CONTROL record as `kind=..|status=..|reason=..`; other fields (pid, descriptor) vary per run."""
    wanted = ("kind", "status", "reason")
    lines = []
    for record in records:
        message = record.getMessage()
        if message.startswith("CONTROL | "):
            fields = dict(part.split("=", 1) for part in message.split(" | ")[1:] if "=" in part)
            lines.append("|".join(f"{key}={fields[key]}" for key in wanted if key in fields))
    return lines


def _error_record_before_end(records: list[logging.LogRecord]) -> bool:
    end = next(i for i, record in enumerate(records) if record.getMessage().startswith(_END))
    return any(record.levelno >= logging.ERROR for record in records[:end])


_NAMES = sorted(path.name for path in _CASES.iterdir() if path.is_dir())


@pytest.mark.parametrize("name", _NAMES)
def test_case(name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    expected = json.loads((_CASES / name / "expected.json").read_text(encoding="utf-8"))
    work = tmp_path / name
    shutil.copytree(_CASES / name, work)
    monkeypatch.chdir(work)  # SQLite files live under the working directory
    engine = DataMimicTest(test_dir=work, filename="descriptor.xml", capture_test_result=True)
    capture = _Records()
    logger = logging.getLogger("DATAMIMIC")
    logger.addHandler(capture)
    try:
        _run_and_check(engine, expected)
    finally:
        logger.removeHandler(capture)
    if "control" in expected:
        assert _control(capture.records) == expected["control"]
    if expected.get("error_record_before_end"):
        assert _error_record_before_end(capture.records)


def _run_and_check(engine: DataMimicTest, expected: dict) -> None:
    if expected["outcome"] == "ok":
        engine.test_with_timer()
        captured = engine.capture_result() or {}
        assert {product: len(rows) for product, rows in captured.items() if product in expected["products"]} == (
            expected["products"]
        )
        return
    with pytest.raises(UserErrorBase) as caught:
        engine.test_with_timer()
    error = caught.value
    assert error.issue_code is not None
    assert error.issue_code.value == expected["issue_code"]
    if "error_code" in expected:
        assert error.code is not None
        assert error.code.value == expected["error_code"]
