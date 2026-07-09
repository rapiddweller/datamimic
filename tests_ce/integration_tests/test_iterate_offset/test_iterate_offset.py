# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""offset= on <iterate>/<generate> (Benerator parity): skip the first N source rows. The
offset shrinks the available window - the count default, cyclic wrap-around, and page windows
all operate on the post-offset region (a cyclic wrap must never re-include skipped rows)."""

import shutil
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


def test_offset_stays_aligned_across_mp_worker_chunks():
    """numProcess=2 splits count=4 into two worker chunks; both must shift by the SAME offset
    (a per-worker re-application or omission would duplicate or drop rows at the chunk seam)."""
    assert _ids("test_offset_mp.xml") == ["2", "3", "4", "5"]


def test_offset_cyclic_mp_wraps_as_one_global_sequence():
    """cyclic across 2 worker chunks: the global wrap sequence over the post-offset region
    (3,4,5,3,4,5,3,4) must reassemble seamlessly from the per-chunk windows."""
    assert _ids("test_offset_mp_cyclic.xml") == ["3", "4", "5", "3", "4", "5", "3", "4"]


def test_offset_random_pool_mp_is_complete_and_duplicate_free():
    """default (random) distribution across 2 worker chunks: the shuffled pool excludes the
    skipped rows, and the disjoint chunk windows together are a permutation of the remainder."""
    assert sorted(_ids("test_offset_mp_random.xml")) == ["3", "4", "5"]


def test_offset_beyond_source_yields_zero_rows():
    engine = DataMimicTest(_dir, "test_offset_beyond_source.xml", capture_test_result=True)
    engine.test_with_timer()
    assert engine.capture_result()["rows"] == []


def test_offset_without_source_is_rejected():
    engine = DataMimicTest(_dir, "test_offset_without_source.xml", capture_test_result=True)
    with pytest.raises(ValueError, match="offset"):
        engine.test_with_timer()


def test_offset_negative_is_rejected():
    engine = DataMimicTest(_dir, "test_offset_negative.xml", capture_test_result=True)
    with pytest.raises(ValueError, match="offset"):
        engine.test_with_timer()


def test_offset_applies_to_every_file_format():
    """json/xml/fcw/xlsx/dbunit all funnel offset into the same windowing helper - one iterate
    per format over the same 5-row fixture proves each loader's pass-through."""
    engine = DataMimicTest(_dir, "test_offset_formats.xml", capture_test_result=True)
    engine.test_with_timer()
    result = engine.capture_result()
    for product in ("rows_json", "rows_xml", "rows_fcw", "rows_xlsx", "rows_dbunit"):
        assert [r["id"] for r in result[product]] == ["3", "4", "5"], product


def test_offset_on_memstore_source_is_rejected():
    engine = DataMimicTest(_dir, "test_offset_memstore_rejected.xml", capture_test_result=True)
    with pytest.raises(ValueError, match="file sources"):
        engine.test_with_timer()


def test_offset_on_db_client_source_is_rejected():
    output_dir = _dir / "output"
    db_dirs = (_dir / "db", _dir.parents[2] / "db")
    for d in (output_dir, *db_dirs):
        shutil.rmtree(d, ignore_errors=True)
    try:
        engine = DataMimicTest(_dir, "test_offset_client_rejected.xml", capture_test_result=True)
        with pytest.raises(ValueError, match="file sources"):
            engine.test_with_timer()
    finally:
        for d in (output_dir, *db_dirs):
            shutil.rmtree(d, ignore_errors=True)
