"""DSL-driven coverage for <key type="binary">: happy paths, determinism, casting,
error handling, and the export boundary (base64 in CSV/XLSX/JSON, raw bytes in a DB BLOB).
"""

import base64
import csv
import json
from pathlib import Path

import pytest
from openpyxl import load_workbook

from datamimic_ce.errors import ErrorCode, IssueCode, TaskConfigError
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


def _run(project_dir: Path, filename: str) -> dict:
    engine = DataMimicTest(test_dir=project_dir, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


# ---------- happy paths ----------


def test_binary_lengths_and_types(project_dir):
    rows = _run(project_dir, "binary_happy.xml")["g"]
    assert len(rows) == 8
    for r in rows:
        assert isinstance(r["default_bin"], bytes) and 1 <= len(r["default_bin"]) <= 16
        assert isinstance(r["exact8"], bytes) and len(r["exact8"]) == 8
        assert isinstance(r["ranged"], bytes) and 4 <= len(r["ranged"]) <= 10
        assert r["hexlen"] == 8  # sibling script can len() the bytes


def test_binary_seeded_reproducible_unseeded_not(project_dir):
    first = [r["exact8"] for r in _run(project_dir, "binary_happy.xml")["g"]]
    second = [r["exact8"] for r in _run(project_dir, "binary_happy.xml")["g"]]
    assert first == second  # rngSeed -> byte-identical

    a = [r["b"] for r in _run(project_dir, "binary_unseeded.xml")["g"]]
    b = [r["b"] for r in _run(project_dir, "binary_unseeded.xml")["g"]]
    assert a != b  # unseeded -> different runs differ


def test_binary_casts_str_script_to_utf8_bytes(project_dir):
    rows = _run(project_dir, "binary_cast.xml")["g"]
    assert rows[0]["from_str"] == b"hello"


def test_binary_generator_attribute_applies_the_mime_signature(project_dir):
    """generator="BinaryGenerator" mimeType= is the call form BinaryGenerator(mime_type=...) (#466)."""
    for row in _run(project_dir, "binary_generator_mime_type.xml")["g"]:
        assert row["png"].startswith(b"\x89PNG\r\n\x1a\n") and len(row["png"]) == 64
        assert row["typed"].startswith(b"\x89PNG\r\n\x1a\n")


# ---------- error handling ----------


def test_binary_min_greater_than_max_raises(project_dir):
    with pytest.raises(Exception, match=r"min length 9 exceeds max length 4"):
        _run(project_dir, "binary_min_gt_max.xml")


def test_binary_negative_length_raises(project_dir):
    with pytest.raises(Exception, match=r"lengths must be >= 0"):
        _run(project_dir, "binary_negative.xml")


def test_binary_cannot_cast_int(project_dir):
    with pytest.raises(TaskConfigError) as caught:
        _run(project_dir, "binary_cast_invalid.xml")
    assert caught.value.code is ErrorCode.TASK_CONFIG
    assert caught.value.issue_code is IssueCode.TASK_DATATYPE_INVALID
    assert "Expect datatype binary but get 'int'" in str(caught.value)
    assert type(caught.value.__cause__) is ValueError


# ---------- export boundary ----------


def test_binary_exports_base64_to_files_and_raw_to_db(project_dir):
    result = _run(project_dir, "binary_export.xml")
    payloads = [r["payload"] for r in result["blobs"]]
    assert all(isinstance(p, bytes) and len(p) == 6 for p in payloads)

    # DB round-trip: raw bytes survive the sqlite BLOB write and read back with the same length
    assert [r["len_back"] for r in result["back"]] == [6, 6, 6, 6, 6]
    assert sorted(r["payload"] for r in result["back"]) == sorted(payloads)

    out = project_dir / "output"
    csv_file = next(out.rglob("*.csv"))
    with csv_file.open() as f:
        csv_rows = list(csv.DictReader(f, delimiter="|"))
    assert [base64.b64decode(r["payload"]) for r in csv_rows] == payloads  # base64 text in csv

    xlsx_rows = list(load_workbook(next(out.rglob("*.xlsx"))).active.iter_rows(values_only=True))
    col = xlsx_rows[0].index("payload")
    assert [base64.b64decode(r[col]) for r in xlsx_rows[1:]] == payloads  # base64 text in xlsx

    json_rows = json.loads(next(out.rglob("*.json")).read_text())
    decoded = [base64.b64decode(r["payload"]) for r in json_rows]
    assert decoded == payloads  # serializer base64-encodes non-utf8 bytes
