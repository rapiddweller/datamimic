# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""<reference> on a MongoDB source: real FK values drawn from documents with the same
seeded selection semantics as the RDBMS reference (random-with-replacement default,
ordered+cyclic wrap, unique). Single-key references cover the shop-demo need
(customer_id/order_id/...); composite <field> mapping shares the same tuple path."""

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent
_POOL = set(range(1, 8))  # seeded customer_ids 1..7


def _run() -> dict:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename="reference_mongodb.xml", capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_mongodb_reference_semantics():
    result = _run()

    random_rows = result["check_random"]
    assert len(random_rows) == 30
    # every FK is a REAL seeded key (not invented, not None)
    assert all(row["customer_id"] in _POOL for row in random_rows)
    # with replacement over 30 draws from 7 keys, repeats are certain
    assert len({row["customer_id"] for row in random_rows}) < 30

    cyclic_rows = result["check_cyclic"]
    # stable key order 1..7, wrapped: 1..7 then 1..3
    assert [row["customer_id"] for row in cyclic_rows] == [1, 2, 3, 4, 5, 6, 7, 1, 2, 3]

    unique_rows = result["check_unique"]
    assert {row["customer_id"] for row in unique_rows} == _POOL  # all distinct, pool exhausted


def test_mongodb_reference_is_deterministic():
    first = _run()
    second = _run()
    for product in ("check_random", "check_cyclic", "check_unique"):
        assert [r["customer_id"] for r in first[product]] == [r["customer_id"] for r in second[product]], product
