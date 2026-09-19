# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""MongoDB collection-routing matrix, end to end against a live mongo: every CRUD write
(consume/update/upsert/delete) resolves its collection targetEntity -> type -> name, and a
selector's own collection is never shadowed by a mismatched statement name - the regression
fixed alongside PR #189. The source (read) side resolves selector -> sourceEntity -> type,
deliberately with no name fallback."""

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run() -> dict:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename="routing_matrix.xml", capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_insert_routing_precedence():
    result = _run()
    assert [row["tag"] for row in result["check_ins_name"]] == ["a", "a"]  # name-only fallback
    assert [row["tag"] for row in result["check_ins_type"]] == ["b", "b"]  # type wins over name
    assert [row["tag"] for row in result["check_ins_te"]] == ["c", "c"]  # targetEntity wins over type


def test_update_name_only_fallback():
    # a memstore-sourced update (no type/targetEntity/selector) still routes by the statement's
    # own name - the actual reported gap ("<iterate source='db' ... target='db.update'>")
    result = _run()
    assert sorted(row["tag"] for row in result["check_upd_name"]) == ["updated", "updated"]


def test_update_selector_not_overridden_by_statement_name():
    result = _run()
    assert sorted(row["tag"] for row in result["check_upd_selector"]) == ["updated", "updated"]


def test_upsert_selector_not_overridden_by_statement_name():
    result = _run()
    rows = result["check_ups_selector"]
    # the filter matched nothing, so upsert inserted a new doc - into the SELECTOR's collection
    assert len(rows) == 1
    assert rows[0]["tag"] == "upserted"


def test_delete_selector_not_overridden_by_statement_name():
    result = _run()
    # all 3 seeded docs were deleted from the selector's own collection, not from a
    # 'del_step_named_differently' collection
    assert result["check_del_selector"] == []


def test_read_source_side_precedence():
    result = _run()
    for product in ("read_by_source_entity", "read_by_type", "read_by_selector"):
        rows = result[product]
        assert len(rows) == 3, product
        assert all(row["tag"] == "x" for row in rows), product
