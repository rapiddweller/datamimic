# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# See LICENSE file for the full text of the license.

"""Nested <generate> page-export order: a child row must reach the db AFTER its parent for
insert/update/upsert (FK: child -> parent), and BEFORE its parent for delete (FK still points at
the still-existing parent, so the child must go first). Proven with real SQLite FK-emulating
triggers via the actual engine (TaskUtil.export_product_by_page /
generate_worker.GenerateWorker.generate_and_export_data_by_chunk) - a wrong write order aborts the
run instead of merely producing a wrong assertion, so a broken ordering fails LOUDLY.
"""

from __future__ import annotations

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str) -> dict:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def _assert_users_and_orders(result: dict) -> None:
    users = result["check_users"]
    orders = result["check_orders"]
    assert [u["id"] for u in users] == list(range(1, 9))
    assert len(orders) == 16
    user_ids = {u["id"] for u in users}
    # Every order's FK actually resolves - not just "no trigger fired", but the right rows exist.
    assert all(o["user_id"] in user_ids for o in orders)
    # Deterministic id scheme (user_id * 10 + seq): also pins down insertion order.
    assert [o["id"] for o in orders] == [
        uid * 10 + seq for uid in range(1, 9) for seq in (1, 2)
    ]


def test_insert_order_parent_before_child():
    """Plain nesting: <generate name="orders"> directly inside <generate name="users">."""
    _assert_users_and_orders(_run("insert_order.xml"))


def test_insert_order_parent_before_child_through_condition():
    """Same proof with the nested <generate> wrapped in <condition><if condition="True">:
    exercises the CompositeStatement walk in TaskUtil._export_nested_products_by_page."""
    _assert_users_and_orders(_run("insert_order_condition.xml"))


def test_delete_order_children_before_parent():
    # Phase 1: seed users/orders (same db file phase 2 below reuses).
    phase1 = _run("delete_order_phase1.xml")
    assert len(phase1["check_users"]) == 8
    assert len(phase1["check_orders"]) == 16

    # Phase 2: delete both tables through target="db.delete" - del_users' own target is a
    # delete, so its nested del_orders must be exported (and thus deleted) first.
    phase2 = _run("delete_order_phase2.xml")
    assert phase2["check_users_after"] == []
    assert phase2["check_orders_after"] == []
