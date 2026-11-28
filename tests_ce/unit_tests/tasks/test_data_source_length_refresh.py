# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A source length is read again each time its statement runs (#641). Build refuses two products with one name, so
; the cache key (name, source, where) is then shared by both reads."""

import shutil
from pathlib import Path

import pytest

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_DESCRIPTORS = Path(__file__).parent / "data_source_length"


def _run(tmp_path: Path, name: str) -> dict[str, list[dict]]:
    shutil.copy(_DESCRIPTORS / f"{name}.xml", tmp_path / "rows.xml")
    engine = DataMimicTest(test_dir=tmp_path, filename="rows.xml", capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


@pytest.mark.parametrize(
    ("descriptor", "rows_read"),
    [
        ("other_entity", 2 + 5),
        ("grown_store", 2 + 5),
        ("unchanged_store", 2 + 2),
    ],
)
def test_a_repeated_read_sees_the_store_as_it_is_when_it_runs(tmp_path: Path, descriptor: str, rows_read: int) -> None:
    result = _run(tmp_path, descriptor)

    # the capture concatenates the products of one name: the first read gives 2 rows, the second its own length
    assert len(result["rd"]) == rows_read


def test_distinct_names_read_their_own_length(tmp_path: Path) -> None:
    result = _run(tmp_path, "distinct_names")

    assert (len(result["rd_a"]), len(result["rd_b"])) == (2, 5)


def test_an_inner_read_sees_the_table_its_parent_filled_page_by_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    shutil.copy(_DESCRIPTORS / "items.scr.sql", tmp_path / "items.scr.sql")

    result = _run(tmp_path, "inner_table_grows")

    # 2 parent rows per page: page 1 reads the 2 seeded rows, page 2 the 4 rows after page 1
    assert len(result["rd"]) == 2 * 2 + 2 * 4
