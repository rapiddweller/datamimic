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
    # customer_id comes from IncrementGenerator (already distinct by construction): proves
    # unique= is a harmless no-op here, NOT that dedup collapses anything real - see
    # check_unique_dupes below.
    assert {row["customer_id"] for row in unique_rows} == _POOL  # all distinct, pool exhausted

    # unique against tier (only 2 distinct values across the 12 seeded docs): a passing test
    # here proves dedup genuinely collapses real repeats.
    dupes_rows = result["check_unique_dupes"]
    assert len(dupes_rows) == 2
    assert {row["tier"] for row in dupes_rows} == {"retail", "business"}, dupes_rows


def test_mongodb_reference_is_deterministic():
    first = _run()
    second = _run()
    for product in ("check_random", "check_cyclic", "check_unique", "check_nested"):
        key = "customer_id" if product != "check_nested" else "address_id"
        assert [r[key] for r in first[product]] == [r[key] for r in second[product]], product

    composite_first = [(r["cust_id"], r["region"]) for r in first["check_composite"]]
    composite_second = [(r["cust_id"], r["region"]) for r in second["check_composite"]]
    assert composite_first == composite_second


def test_mongodb_reference_composite_fields():
    """Multiple <field> children on one <reference> pull correlated columns from the SAME
    source row as a tuple, not independent per-column samples - region is deterministic from
    cust_id (odd -> north, even -> south) in the fixture, so any row pairing them inconsistently
    would mean the composite fetch lost row identity (e.g. zipped mismatched columns)."""
    result = _run()
    rows = result["check_composite"]
    assert len(rows) == 12

    for row in rows:
        expected_region = "north" if row["cust_id"] % 2 == 1 else "south"
        assert row["region"] == expected_region, row

    # unique="true": all 12 seeded customers drawn exactly once, pool exhausted
    assert {row["cust_id"] for row in rows} == set(range(1, 13))


def test_mongodb_reference_dotted_composite_rejected():
    """Error case: a dotted (nested-document) sourceKey only supports a single sourceKey -
    unwinding several independent nested paths has no meaningful row pairing
    (mongodb_client.py:get_random_rows_by_columns). Combining a dotted path with a second
    composite <field> must raise, not silently mis-pair rows."""
    import pytest

    from datamimic_ce.clients.mongodb_client import MongoDBClient
    from datamimic_ce.connection_config.mongodb_connection_config import MongoDBConnectionConfig

    client = MongoDBClient(
        credential=MongoDBConnectionConfig(host="unreachable.invalid", port=27017, database="x")
    )
    with pytest.raises(ValueError, match="dotted"):
        client.get_random_rows_by_columns("some_collection", ["addresses.address_id", "region"])


def test_mongodb_reference_nested_path():
    """A dotted sourceKey ('addresses.address_id') resolves a <reference> to an entity nested
    inside a collection document (a converted legacy-DSL <part>), unwinding the embedded list."""
    result = _run()
    nested_rows = result["check_nested"]
    # 3 customers x 2 addresses = 6 real nested address ids; cyclic wraps the stable order exactly
    # once since count == pool size.
    assert [row["address_id"] for row in nested_rows] == [11, 12, 21, 22, 31, 32]
