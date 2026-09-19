# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""<generate source="x.wgt.csv"> (the value|weight format) only raises when the file is
HEADERLESS - the plain CSV reader has no coherent way to read that at all, it would treat the
first data row as a header, producing nonsense column names and one fewer row than the file has.
A HEADERED ".wgt.csv" (FileUtil.read_weight_csv now accepts either, see feat/wgt-csv-header-
optional) falls through to the plain CSV reader instead: reading it plainly (ignoring the weight,
no resampling) is coherent, just unweighted - the same tolerance ".wgt.ent.csv" already gets.

Full weighted-entity support at <generate>-level needs pagination-core work (see PR #194
discussion); until that lands, fail loudly instead of silently producing garbage, but only where
there is no coherent fallback.

".wgt.ent.csv" is a normal headered CSV that happens to carry an extra "weight" column, so reading
it plainly (ignoring the weight, no resampling) is coherent - just unweighted. An existing test
(test_source_script/test_iterate_source_scripted.xml) already relies on exactly that, so this must
keep working."""

from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_dir = Path(__file__).resolve().parent


def test_generate_source_wgt_csv_headerless_raises():
    engine = DataMimicTest(_dir, "generate_wgt_plain.xml", capture_test_result=True)
    with pytest.raises(ValueError, match=r"\.wgt\.csv"):
        engine.test_with_timer()


def test_generate_source_wgt_csv_with_header_reads_as_plain_csv():
    """A headered '.wgt.csv' is NOT weighted (no resampling, no bias toward the higher-weight
    row) - just an ordinary headered CSV read, weight column included as literal data. Must NOT
    raise, unlike the headerless case."""
    engine = DataMimicTest(_dir, "generate_wgt_with_header.xml", capture_test_result=True)
    engine.test_with_timer()
    rows = engine.capture_result()["rows"]
    assert {row["value"] for row in rows} <= {"true", "false"}
    assert all("weight" in row for row in rows)


def test_generate_source_wgt_ent_csv_reads_as_plain_csv():
    """Not weighted (no resampling, no bias toward the higher-weight row) - just an ordinary
    headered CSV read, weight column included as literal data. Must NOT raise."""
    engine = DataMimicTest(_dir, "generate_wgt_ent.xml", capture_test_result=True)
    engine.test_with_timer()
    rows = engine.capture_result()["rows"]
    assert {row["name"] for row in rows} <= {"Cheap", "Expensive"}
    assert all("weight" in row for row in rows)
