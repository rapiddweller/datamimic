# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""<reference> against RDBMS sources (Postgres/MSSQL/Oracle): real FK values drawn from
rows with the same seeded selection semantics as the MongoDB reference (random-with-
replacement default, ordered+cyclic wrap, unique). Composite <field> mapping shares the
same tuple path - see test_mongodb_reference for the MongoDB counterpart of this matrix."""

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent
_POOL = set(range(1, 13))  # seeded customer_ids 1..12 (crosses the single/double-digit boundary)


def _run(filename: str) -> dict:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def _assert_reference_semantics(result: dict) -> None:
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


def _assert_composite_semantics(result: dict) -> None:
    rows = result["check_composite"]
    assert len(rows) == 12
    for row in rows:
        expected_region = "north" if row["cust_id"] % 2 == 1 else "south"
        assert row["region"] == expected_region, row
    # unique="true": all 12 seeded customers drawn exactly once, pool exhausted
    assert {row["cust_id"] for row in rows} == set(range(1, 13))


class TestRdbmsReferencePostgresql:
    def test_postgresql_reference_semantics(self):
        _assert_reference_semantics(_run("reference_postgresql.xml"))

    def test_postgresql_reference_composite_fields(self):
        _assert_composite_semantics(_run("reference_postgresql.xml"))

    def test_postgresql_reference_is_deterministic(self):
        first = _run("reference_postgresql.xml")
        second = _run("reference_postgresql.xml")
        for product in ("check_random", "check_cyclic", "check_unique"):
            assert [r["customer_id"] for r in first[product]] == [r["customer_id"] for r in second[product]], product


class TestRdbmsReferenceMssql:
    def test_mssql_reference_semantics(self):
        _assert_reference_semantics(_run("reference_mssql.xml"))

    def test_mssql_reference_composite_fields(self):
        _assert_composite_semantics(_run("reference_mssql.xml"))


class TestRdbmsReferenceOracle:
    def test_oracle_reference_semantics(self):
        _assert_reference_semantics(_run("reference_oracle.xml"))

    def test_oracle_reference_composite_fields(self):
        _assert_composite_semantics(_run("reference_oracle.xml"))
