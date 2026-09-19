# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# See LICENSE file for the full text of the license.

"""SQL dot-notation targets: target="db.update|upsert|delete" keyed on the table's primary key —
the SQL counterpart of the existing mongodb.update/upsert/delete targets."""

from __future__ import annotations

from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str) -> dict:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_db_update_changes_rows_count_constant():
    check = _run("sql_update.xml")["check"]
    assert len(check) == 3  # UPDATE, not insert: row count unchanged
    assert [r["tier"] for r in check] == ["gold", "gold", "gold"]
    assert [r["name"] for r in check] == ["a", "b", "c"]  # untouched column preserved


def test_db_upsert_updates_existing_and_inserts_new():
    check = _run("sql_upsert.xml")["check"]
    assert [r["id"] for r in check] == [1, 2, 3, 4, 5]
    assert all(r["tier"] == "upserted" for r in check)
    assert [r["name"] for r in check] == ["n1", "n2", "n3", "n4", "n5"]


def test_db_delete_removes_rows_by_pk():
    check = _run("sql_delete.xml")["check"]
    assert [r["id"] for r in check] == [3, 4, 5]  # bronze rows (1, 2) deleted


def test_db_update_without_primary_key_raises():
    with pytest.raises(Exception, match=r"no primary key"):
        _run("sql_update_no_pk.xml")
