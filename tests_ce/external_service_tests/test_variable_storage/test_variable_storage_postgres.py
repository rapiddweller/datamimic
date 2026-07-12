# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""<variable type=... storage="value"/"data"/"iterator"> against a real Postgres table (15-row
pool). Mirrors DATAMIMIC EE's storage= semantics: "value" is the pool's first row FIXED every
generated row (not the unset-storage default, which advances one row per execute() call); "data"
is the whole materialized pool, same list every row; "iterator" is a position-indexed proxy,
cyclic wraps / non-cyclic exhausts to None. pageSize < count throughout so a pagination-override
bug (storage= must ignore pageSize and load the whole table) would be caught."""

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent
_POOL = set(range(1, 16))  # seeded row_ids 1..15


def _run(filename: str) -> dict:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


class TestVariableStoragePostgres:
    def test_storage_data_exposes_full_pool_ignoring_page_size(self):
        result = _run("test_storage_postgres.xml")
        for key in ("data_ordered", "data_random"):
            rows = result[key]
            assert len(rows) == 5
            # every generated row sees the SAME full 15-row pool, not a pageSize-limited slice
            assert all(r["pool_len"] == 15 for r in rows), rows
            # same first element across all 5 generated rows - one materialized pool, not
            # re-loaded/re-shuffled per row
            assert len({r["first_id"] for r in rows}) == 1

    def test_storage_value_is_fixed_first_row_not_advancing(self):
        result = _run("test_storage_postgres.xml")
        for key in ("value_ordered", "value_random"):
            rows = result[key]
            assert len(rows) == 5
            # every one of the 5 generated rows gets the SAME row_id - distinct from the unset
            # default (which would advance/shuffle a new row_id each time)
            assert len({r["row_id"] for r in rows}) == 1
            assert rows[0]["row_id"] in _POOL

    def test_storage_iterator_ordered_cyclic_wraps_exact_sequence(self):
        result = _run("test_storage_postgres.xml")
        ids = [r["row_id"] for r in result["iterator_cyclic_ordered"]]
        # stable order 1..15, wrapped: 1..15 then 1..5 (count=20, pool=15)
        assert ids == [*range(1, 16), *range(1, 6)], ids

    def test_storage_iterator_random_cyclic_wraps_with_repeats(self):
        result = _run("test_storage_postgres.xml")
        ids = [r["row_id"] for r in result["iterator_cyclic_random"]]
        assert len(ids) == 20
        assert set(ids) <= _POOL
        # count (20) > pool (15) with cyclic=true: repeats required
        assert len(set(ids)) < 20
        # the wrap repeats the SAME shuffled order: positions 0..4 must equal positions 15..19
        assert ids[0:5] == ids[15:20]

    def test_storage_iterator_non_cyclic_exhausts_to_none(self):
        result = _run("test_storage_postgres.xml")
        ids = [r["row_id"] for r in result["iterator_non_cyclic"]]
        assert len(ids) == 20
        assert ids[:15] == list(range(1, 16))
        assert ids[15:] == [None] * 5

    def test_storage_sp_mp_determinism(self):
        """SP==MP determinism: the same seeded fixture at numProcess=1 and numProcess=2 must
        produce byte-identical per-row sequences for storage="iterator" - proof that
        pagination.skip (the page's true global row offset) gives correct global-position
        semantics across workers, not just within one."""
        sp = _run("test_storage_postgres.xml")
        mp = _run("test_storage_postgres_mp.xml")
        for key in ("iterator_cyclic_ordered", "iterator_cyclic_random", "iterator_non_cyclic"):
            sp_ids = [r["row_id"] for r in sp[key]]
            mp_ids = [r["row_id"] for r in mp[key]]
            assert sp_ids == mp_ids, f"{key}: SP {sp_ids} != MP {mp_ids}"
