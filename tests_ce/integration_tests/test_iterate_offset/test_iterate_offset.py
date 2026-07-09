# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""offset= on <iterate>/<generate> (Benerator parity): skip the first N source rows. The
offset shrinks the available window - the count default, cyclic wrap-around, and page windows
all operate on the post-offset region (a cyclic wrap must never re-include skipped rows)."""

from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_dir = Path(__file__).resolve().parent
# data/rows.csv: ids 1..5


def _ids(filename: str) -> list[str]:
    engine = DataMimicTest(_dir, filename, capture_test_result=True)
    engine.test_with_timer()
    return [r["id"] for r in engine.capture_result()["rows"]]


def test_offset_skips_rows_and_shrinks_count_default():
    # no count= -> count defaults to the REMAINING rows (5 - 2), not the file length
    assert _ids("test_offset_no_count.xml") == ["3", "4", "5"]


def test_offset_cyclic_wraps_within_post_offset_region():
    # wrap-around must cycle rows 3..5 only - re-including skipped rows 1..2 is the failure mode
    assert _ids("test_offset_cyclic.xml") == ["3", "4", "5", "3", "4", "5", "3"]


def test_offset_stays_aligned_across_pages():
    # pageSize=2 with count=4 forces two pages; both windows shift by the same offset
    assert _ids("test_offset_paged.xml") == ["2", "3", "4", "5"]


def test_offset_excludes_skipped_rows_from_the_random_pool():
    # default (random) distribution loads the full pool then shuffles - the skipped rows must
    # be excluded from the pool itself, and the count default still shrinks to 3
    assert sorted(_ids("test_offset_random_pool.xml")) == ["3", "4", "5"]


def test_offset_beyond_source_yields_zero_rows():
    engine = DataMimicTest(_dir, "test_offset_beyond_source.xml", capture_test_result=True)
    engine.test_with_timer()
    assert engine.capture_result()["rows"] == []


def test_offset_without_source_is_rejected():
    engine = DataMimicTest(_dir, "test_offset_without_source.xml", capture_test_result=True)
    with pytest.raises(ValueError, match="offset"):
        engine.test_with_timer()
