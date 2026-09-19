# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""<variable storage=...> spot-checks across the remaining source entry points not covered by
test_variable_storage_postgres.py's full matrix: postgres selector=, mongo type=/selector=, a
file source (a deliberate CE extension beyond EE - EE's own storage= is non-functional for file
sources), memstore, and an empty pool. Each confirms the SAME storage logic (already matrix-
verified against postgres type=) is reached correctly from that entry point - not re-proving the
distribution/cyclic math itself."""

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str) -> dict:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_storage_iterator_via_postgres_selector():
    result = _run("test_storage_postgres_selector.xml")
    ids = [r["row_id"] for r in result["iterator_cyclic_selector"]]
    assert len(ids) == 20
    assert set(ids) <= set(range(1, 16))
    assert len(set(ids)) < 20  # cyclic wrap, count > pool


class TestVariableStorageMongo:
    def test_storage_data_full_pool_via_type(self):
        result = _run("test_storage_mongo.xml")
        rows = result["data_type"]
        assert len(rows) == 5
        assert all(r["pool_len"] == 15 for r in rows)

    def test_storage_value_fixed_via_type(self):
        result = _run("test_storage_mongo.xml")
        rows = result["value_type"]
        assert len(rows) == 5
        assert len({r["row_id"] for r in rows}) == 1

    def test_storage_iterator_cyclic_exact_sequence_via_type(self):
        result = _run("test_storage_mongo.xml")
        ids = [r["row_id"] for r in result["iterator_cyclic_type"]]
        assert ids == [*range(1, 16), *range(1, 6)], ids

    def test_storage_iterator_cyclic_via_selector(self):
        result = _run("test_storage_mongo.xml")
        ids = [r["row_id"] for r in result["iterator_cyclic_selector"]]
        assert len(ids) == 20
        assert set(ids) <= set(range(1, 16))
        assert len(set(ids)) < 20


class TestVariableStorageFile:
    """storage= on a file source is a deliberate CE extension beyond EE (EE's own storage= is
    non-functional for file sources - see the plan's EE-semantics section)."""

    def test_storage_data_full_pool(self):
        result = _run("test_storage_file.xml")
        rows = result["data_file"]
        assert len(rows) == 3
        assert all(r["pool_len"] == 11 for r in rows)

    def test_storage_value_fixed(self):
        result = _run("test_storage_file.xml")
        rows = result["value_file"]
        assert len(rows) == 3
        assert len({r["ean_code"] for r in rows}) == 1
        assert rows[0]["ean_code"] == 1  # distribution="ordered": first loaded row

    def test_storage_iterator_cyclic_exact_sequence(self):
        result = _run("test_storage_file.xml")
        codes = [r["ean_code"] for r in result["iterator_cyclic_file"]]
        # stable order 1..11, wrapped: 1..11 then 1..4 (count=15, pool=11)
        assert codes == [*range(1, 12), *range(1, 5)], codes

    def test_storage_iterator_non_cyclic_exhausts_to_none(self):
        result = _run("test_storage_file.xml")
        codes = [r["ean_code"] for r in result["iterator_non_cyclic_file"]]
        assert codes[:11] == list(range(1, 12))
        assert codes[11:] == [None] * 4


def test_storage_iterator_via_memstore():
    result = _run("test_storage_memstore.xml")
    ids = [r["row_id"] for r in result["iterator_cyclic_mem"]]
    # stable order 1..15, wrapped: 1..15 then 1..5 (count=20, pool=15)
    assert ids == [*range(1, 16), *range(1, 6)], ids


class TestVariableStorageEmptyPool:
    def test_storage_value_on_empty_pool_is_none(self):
        result = _run("test_storage_empty_pool.xml")
        rows = result["value_empty"]
        assert len(rows) == 3
        assert all(r["row_id"] is None for r in rows)

    def test_storage_iterator_on_empty_pool_is_none(self):
        result = _run("test_storage_empty_pool.xml")
        rows = result["iterator_empty"]
        assert len(rows) == 3
        assert all(r["row_id"] is None for r in rows)
