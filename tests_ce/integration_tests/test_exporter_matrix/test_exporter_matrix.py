# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Exporter matrix: ONE generate writes to EVERY registered buffered exporter, each
format is read back. Self-extending gate — registering a new buffered exporter without
adding a reader here fails the coverage assert."""

import csv
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from datamimic_ce.constants.exporter_constants import (
    EXPORTER_CSV,
    EXPORTER_DBUNIT,
    EXPORTER_FIXED_WIDTH,
    EXPORTER_JSON,
    EXPORTER_TXT,
    EXPORTER_XLSX,
    EXPORTER_XML,
)
from datamimic_ce.data_mimic_test import DataMimicTest
from datamimic_ce.exporters.exporter_util import _BUFFERED_EXPORTERS
from datamimic_ce.utils.file_util import FileUtil

_DIR = Path(__file__).resolve().parent
_OUT = _DIR / "output" / "matrix_out"
_COUNT = 10


def _file(ext: str) -> Path:
    # exact name: "*.xml" would also match the ".dbunit.xml" dataset
    hits = list(_OUT.rglob(f"matrix_rows.{ext}"))
    assert len(hits) == 1, f"expected exactly one matrix_rows.{ext} in {_OUT}, found {[p.name for p in hits]}"
    return hits[0]


def _read_csv() -> list[int]:
    with _file("csv").open() as f:
        return [int(row["id"]) for row in csv.DictReader(f)]


def _read_json() -> list[int]:
    return [int(row["id"]) for row in json.loads(_file("json").read_text())]


def _read_xml() -> list[int]:
    root = ET.parse(str(_file("xml"))).getroot()
    return [int(item.findtext("id")) for item in root.iter("item")]


def _read_xlsx() -> list[int]:
    from openpyxl import load_workbook

    sheet = load_workbook(_file("xlsx")).active
    rows = list(sheet.iter_rows(values_only=True))
    header, data = rows[0], rows[1:]
    id_col = header.index("id")
    return [int(row[id_col]) for row in data]


def _read_txt() -> list[int]:
    lines = [ln for ln in _file("txt").read_text().splitlines() if ln]
    assert all(ln.startswith("matrix_rows: ") for ln in lines)
    # TXT lines are "<product>: <record dict repr>" — eval the dict repr for the id
    return [int(eval(ln.split(": ", 1)[1])["id"]) for ln in lines]


def _read_dbunit() -> list[int]:
    root = ET.parse(str(_file("dbunit.xml"))).getroot()
    return [int(row.get("id")) for row in root if row.tag == "matrix_rows"]


def _read_fixed_width() -> list[int]:
    return [int(row["id"]) for row in FileUtil.read_fixed_width_to_dict_list(_file("fcw"))]


_READERS = {
    EXPORTER_CSV: _read_csv,
    EXPORTER_JSON: _read_json,
    EXPORTER_XML: _read_xml,
    EXPORTER_XLSX: _read_xlsx,
    EXPORTER_TXT: _read_txt,
    EXPORTER_DBUNIT: _read_dbunit,
    EXPORTER_FIXED_WIDTH: _read_fixed_width,
}


def test_every_registered_buffered_exporter_round_trips():
    # Self-extending: a new registry entry must add a matrix reader
    assert set(_READERS) == set(_BUFFERED_EXPORTERS), "matrix reader missing for a registered exporter"

    shutil.rmtree(_DIR / "output", ignore_errors=True)
    try:
        DataMimicTest(test_dir=_DIR, filename="matrix.xml").test_with_timer()
        for name, reader in _READERS.items():
            ids = reader()
            assert sorted(ids) == list(range(1, _COUNT + 1)), f"{name}: wrong ids {sorted(ids)}"
    finally:
        shutil.rmtree(_DIR / "output", ignore_errors=True)


def test_write_read_roundtrip_through_every_pagination_mode():
    """Write a JSON file, read it back as a source with cyclic/pageSize/distribution/unique.
    All asserts are seed-independent (wraparound order, permutation blocks, distinctness)."""
    shutil.rmtree(_DIR / "output", ignore_errors=True)
    try:
        engine = DataMimicTest(test_dir=_DIR, filename="roundtrip.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()

        src = list(range(1, 7))  # 6 source rows

        # ordered + cyclic: exact wraparound sequence across the 4 pages
        assert [r["id"] for r in result["ordered_cyclic"]] == src * 2 + [1, 2, 3]

        # random + cyclic: each source-length block of the global sequence is a permutation
        rand = [r["id"] for r in result["random_cyclic"]]
        assert len(rand) == 15
        assert sorted(rand[0:6]) == src and sorted(rand[6:12]) == src
        assert len(set(rand[12:15])) == 3

        # unique across pages: every source row exactly once
        assert sorted(r["id"] for r in result["unique_pages"]) == src

        # not cyclic: more requested than available -> stops at the 6 source rows, in order
        assert [r["id"] for r in result["exhausted"]] == src
    finally:
        shutil.rmtree(_DIR / "output", ignore_errors=True)
