# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Paged RDBMS source reads follow a unique total order (#228): without one, OFFSET pages can
repeat or skip rows across pages and workers, and seeded runs are not reproducible."""

from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent
# the seeded rows (see script/setup_*.scr.sql), sorted by (grp, id)
_ROWS_BY_ALL_COLUMNS = [
    *[(1, 2), (1, 5), (1, 8), (1, 11)],
    *[(2, 3), (2, 6), (2, 9), (2, 12)],
    *[(3, 1), (3, 4), (3, 7), (3, 10)],
]


@pytest.mark.parametrize("filename", ["paging_postgresql.xml", "paging_mssql.xml", "paging_oracle.xml"])
def test_paged_reads_follow_a_unique_order(filename: str) -> None:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    result = engine.capture_result()

    def rows(product: str) -> list[tuple[int, int]]:
        return [(row["grp"], row["id"]) for row in result[product]]

    assert rows("by_type") == _ROWS_BY_ALL_COLUMNS
    assert [row_id for _, row_id in rows("by_type_pk")] == list(range(1, 13))
    assert rows("by_selector") == _ROWS_BY_ALL_COLUMNS
    assert sorted(rows("by_type_mp")) == _ROWS_BY_ALL_COLUMNS
    assert sorted(rows("by_selector_mp")) == _ROWS_BY_ALL_COLUMNS
