# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Every source reader reports a missing or invalid file with a catalog code and the file name only (#379).

Python-level because the reader is chosen by the file's format; the DSL-level path (`generate source=`) reaches
the same functions, and test_portable_errors.py / test_cli_v4.py pin the dry-run and run output for CSV."""

from pathlib import Path

import pytest

from datamimic_ce.engine.dsl.api import SourceFileFormat
from datamimic_ce.engine.io.files.readers import FileUtil, load_source_rows
from datamimic_ce.errors import InvalidSourceError, IssueCode, MissingSourceError

_MISSING = [
    ("missing.csv", SourceFileFormat.CSV),
    ("missing.json", SourceFileFormat.JSON),
    ("missing.xml", SourceFileFormat.XML),
    ("missing.xlsx", SourceFileFormat.XLSX),
    ("missing.txt", SourceFileFormat.FIXED_WIDTH),
]


@pytest.mark.parametrize(("name", "source_format"), _MISSING, ids=[item[1].name for item in _MISSING])
def test_a_missing_source_file_is_a_portable_i101_without_the_host_path(
    tmp_path: Path, name: str, source_format: SourceFileFormat
) -> None:
    with pytest.raises(FileNotFoundError) as caught:
        load_source_rows(tmp_path / name, ",", source_format)
    error = caught.value
    assert type(error) is MissingSourceError
    assert error.issue_code is IssueCode.SOURCE_FILE_NOT_FOUND
    assert name in str(error)
    assert str(tmp_path) not in str(error)


def test_a_missing_dbunit_file_is_a_portable_i101(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError) as caught:
        FileUtil.read_dbunit_to_dict_list(tmp_path / "missing.dbunit.xml", "t")
    assert type(caught.value) is MissingSourceError
    assert str(tmp_path) not in str(caught.value)


@pytest.mark.parametrize(
    ("name", "content", "source_format", "code"),
    [
        ("bad.xml", "<a><b></a>", SourceFileFormat.XML, IssueCode.SOURCE_INVALID_XML),
        ("items.xml", "<list><item>text</item></list>", SourceFileFormat.XML, IssueCode.SOURCE_INVALID_XML),
        ("bad.json", "[{", SourceFileFormat.JSON, IssueCode.SOURCE_INVALID_JSON),
    ],
)
def test_an_invalid_xml_or_json_source_carries_its_code_and_no_host_path(
    tmp_path: Path, name: str, content: str, source_format: SourceFileFormat, code: IssueCode
) -> None:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    with pytest.raises(InvalidSourceError) as caught:
        load_source_rows(path, ",", source_format)
    assert caught.value.issue_code is code
    assert name in str(caught.value)
    assert str(tmp_path) not in str(caught.value)


@pytest.mark.parametrize(
    ("name", "content", "source_format"),
    [
        ("broken.xlsx", b"not a workbook", SourceFileFormat.XLSX),
        ("plain.txt", b"no spec header\nrow", SourceFileFormat.FIXED_WIDTH),
    ],
)
def test_the_remaining_invalid_sources_do_not_leak_the_host_path(
    tmp_path: Path, name: str, content: bytes, source_format: SourceFileFormat
) -> None:
    # No catalog code exists for these two yet (it needs a shared CE/EE code); the message must at least be portable.
    path = tmp_path / name
    path.write_bytes(content)
    with pytest.raises(ValueError) as caught:
        load_source_rows(path, ",", source_format)
    assert name in str(caught.value)
    assert str(tmp_path) not in str(caught.value)
