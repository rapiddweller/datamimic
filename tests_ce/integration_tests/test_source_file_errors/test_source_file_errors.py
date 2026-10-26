# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Every file source reader reports a missing or invalid file with a catalog code and the file name only (#379).
The models are DSL files next to this test. `datamimic run` runs in a subprocess, so the assertion covers the text a
user sees: the log, the `Error:` line and any traceback."""

import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.errors import IssueCode, UserErrorBase
from datamimic_ce.interfaces.cli import app
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent
_HOST = "hostdir_q7z_private"  # a directory name that only the host path contains
_ENTITY = "secret_table"  # a descriptor value that a message must not echo

# descriptor, code of the refusal
_REFUSED = [
    ("xml_missing", IssueCode.SOURCE_FILE_NOT_FOUND),
    ("xml_malformed", IssueCode.SOURCE_INVALID_XML),
    ("xlsx_missing", IssueCode.SOURCE_FILE_NOT_FOUND),
    ("xlsx_not_a_workbook", IssueCode.SOURCE_INVALID_XLSX),
    ("xlsx_empty_file", IssueCode.SOURCE_INVALID_XLSX),
    ("dbunit_missing", IssueCode.SOURCE_FILE_NOT_FOUND),
    ("dbunit_malformed", IssueCode.SOURCE_INVALID_XML),
    ("dbunit_no_such_table", IssueCode.SOURCE_INVALID_XML),
    ("fixed_width_missing", IssueCode.SOURCE_FILE_NOT_FOUND),
    ("fixed_width_no_spec_header", IssueCode.SOURCE_INVALID_FIXED_WIDTH),
    ("fixed_width_bad_spec_column", IssueCode.SOURCE_INVALID_FIXED_WIDTH),
    ("json_missing", IssueCode.SOURCE_FILE_NOT_FOUND),
    ("json_malformed", IssueCode.SOURCE_INVALID_JSON),
    ("weighted_csv_empty", IssueCode.SOURCE_INVALID_CSV),
]
_IDS = [row[0] for row in _REFUSED]


def _project(tmp_path: Path) -> Path:
    project = tmp_path / _HOST / "project"
    shutil.copytree(_DIR, project, ignore=shutil.ignore_patterns("*.py", "__pycache__"))
    return project


def _leaks(output: str) -> list[str]:
    # The engine logs its own working directory; every other line must not name the host path.
    return [line for line in output.splitlines() if _HOST in line and "working directory" not in line]


@pytest.mark.parametrize(("model", "code"), _REFUSED, ids=_IDS)
def test_run_reports_the_code_and_only_the_file_name(tmp_path: Path, model: str, code: IssueCode) -> None:
    project = _project(tmp_path)
    run = subprocess.run(
        [sys.executable, "-m", "datamimic_ce.interfaces.cli", "run", f"{model}.xml"],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    output = run.stdout + run.stderr
    assert run.returncode != 0
    assert re.search(rf"^Error: \[E\d+/{code.value}\]", output, re.MULTILINE), output
    assert _leaks(output) == []
    assert _ENTITY not in output.replace(f'sourceEntity="{_ENTITY}"', "")


@pytest.mark.parametrize(("model", "code"), _REFUSED, ids=_IDS)
def test_the_error_keeps_its_type_and_dry_run_its_code(tmp_path: Path, model: str, code: IssueCode) -> None:
    engine = DataMimicTest(test_dir=_DIR, filename=f"{model}.xml", capture_test_result=True)
    with pytest.raises(UserErrorBase) as caught:
        engine.test_with_timer()
    assert caught.value.issue_code is code
    # A missing file stays catchable as the native error.
    assert isinstance(caught.value, FileNotFoundError) is (code is IssueCode.SOURCE_FILE_NOT_FOUND)

    project = _project(tmp_path)
    dry_run = CliRunner().invoke(app, ["authoring", "dry-run", str(project / f"{model}.xml")])
    assert _HOST not in dry_run.output
    (diagnostic,) = json.loads(dry_run.stdout)["diagnostics"]
    assert diagnostic["ce_error"]["issue_code"] == code.value


def _rows(project: Path, model: str) -> list[dict]:
    engine = DataMimicTest(test_dir=project, filename=f"{model}.xml", capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()["rows"]


def test_the_valid_fixed_width_neighbour_still_reads() -> None:
    assert _rows(_DIR, "fixed_width_valid") == [{"id": "1", "name": "a"}]


# CE and EE read NaN and Infinity as floats; a catalog code for them is left out by decision (ce-ee-parity.md).
@pytest.mark.parametrize(
    ("model", "score"),
    [
        ("json_nan", "nan"),
        ("json_infinity", "inf"),
        ("json_negative_infinity", "-inf"),
        ("json_above_max_float", "inf"),  # json.loads gives inf for 1e309
    ],
)
def test_a_non_finite_json_number_reads_as_a_float(model: str, score: str) -> None:
    (row,) = _rows(_DIR, model)
    assert row["id"] == 1
    assert isinstance(row["score"], float)
    assert str(row["score"]) == score  # str, because NaN never equals NaN


def test_a_json_file_that_ce_exports_with_nan_reads_back(tmp_path: Path) -> None:
    project = _project(tmp_path)
    DataMimicTest(test_dir=project, filename="json_nan_export.xml").test_with_timer()
    (exported,) = (project / "output").rglob("scores.json")
    assert "NaN" in exported.read_text(encoding="utf-8")  # the exporter writes NaN, not null
    shutil.copy(exported, project / "data" / "exported_nan.json")
    rows = _rows(project, "json_nan_readback")
    assert [row["id"] for row in rows] == [1, 2]
    assert all(math.isnan(row["score"]) for row in rows)
