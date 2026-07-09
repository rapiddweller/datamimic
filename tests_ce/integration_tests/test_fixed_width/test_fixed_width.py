# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Fixed-width (.fcw) column file support - migration parity with the migrated
fixed-width demo descriptors. Self-describing: the file's first line is a '# name[width],...'
column spec comment, so a plain <generate source="x.fcw"> needs no extra DSL attribute to read."""

import shutil
from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest
from datamimic_ce.utils.file_util import FileUtil

_dir = Path(__file__).resolve().parent


def test_fixed_width_read():
    engine = DataMimicTest(_dir, "test_fixed_width_read.xml", capture_test_result=True)
    engine.test_with_timer()
    rows = engine.capture_result()["rows"]
    assert len(rows) == 2
    row = next(r for r in rows if r["ean_code"] == "8000353006393")
    assert row["name"] == "Limoncello Liqueur"
    assert row["category_id"] == "DRNK/ALCO"
    assert row["price"] == "9.85"
    assert row["manufacturer"] == "Luxardo"


def test_fixed_width_missing_header_raises():
    engine = DataMimicTest(_dir, "test_fixed_width_malformed.xml", capture_test_result=True)
    with pytest.raises(ValueError, match="Fixed-width"):
        engine.test_with_timer()


def test_fixed_width_write_round_trip():
    output_dir = _dir / "output"
    shutil.rmtree(output_dir, ignore_errors=True)
    try:
        engine = DataMimicTest(_dir, "test_fixed_width_write.xml", capture_test_result=True)
        engine.test_with_timer()

        written = list(output_dir.rglob("*.fcw"))
        assert len(written) == 1, f"expected exactly one .fcw output file, found {written}"

        content = written[0].read_text()
        assert content.startswith("# id[8r0],name[10]\n"), content.splitlines()[0]

        rows = FileUtil.read_fixed_width_to_dict_list(written[0])
        assert len(rows) == 3
        assert {r["name"] for r in rows} <= {"Ann", "Bo", "Cy"}  # random pick, may repeat
        assert {r["id"] for r in rows} == {"1", "2", "3"}
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)
