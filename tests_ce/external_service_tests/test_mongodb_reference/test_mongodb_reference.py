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
_POOL = set(range(1, 13))  # seeded customer_ids 1..12 (crosses the single/double-digit boundary)


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
    # with replacement over 30 draws from 12 keys, repeats are certain
    assert len({row["customer_id"] for row in random_rows}) < 30

    cyclic_rows = result["check_cyclic"]
    # stable key order 1..12, wrapped: 1..12 then 1..3. Only holds under a numeric sort - a
    # lexicographic sort would put 10/11/12 right after 1, before 2.
    assert [row["customer_id"] for row in cyclic_rows] == [*range(1, 13), 1, 2, 3]

    unique_rows = result["check_unique"]
    assert {row["customer_id"] for row in unique_rows} == _POOL  # all distinct, pool exhausted


def test_mongodb_reference_is_deterministic():
    first = _run()
    second = _run()
    for product in ("check_random", "check_cyclic", "check_unique", "check_nested"):
        key = "customer_id" if product != "check_nested" else "address_id"
        assert [r[key] for r in first[product]] == [r[key] for r in second[product]], product


def test_mongodb_reference_nested_path():
    """A dotted sourceKey ('addresses.address_id') resolves a <reference> to an entity nested
    inside a collection document (a converted Benerator <part>), unwinding the embedded list."""
    result = _run()
    nested_rows = result["check_nested"]
    # 3 customers x 2 addresses = 6 real nested address ids; cyclic wraps the stable order exactly
    # once since count == pool size.
    assert [row["address_id"] for row in nested_rows] == [11, 12, 21, 22, 31, 32]
