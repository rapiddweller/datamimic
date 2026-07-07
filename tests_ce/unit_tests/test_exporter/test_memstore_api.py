# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Memstore query API - Benerator parity (memstore/memstore.ben.xml uses
mem.sumEntityColumn/mem.entityCount/mem.removeNotExistingIds). No DSL entry point exists for these
yet (that's the separate execute-namespace-binding fix) - unit-tested directly against the class."""

from datamimic_ce.exporters.memstore import Memstore


class _FakeClient:
    """Stands in for RdbmsClient.get_random_rows_by_columns - returns 1-tuples of existing ids."""

    def __init__(self, existing_ids: list):
        self._existing_ids = existing_ids

    def get_random_rows_by_columns(self, table_name: str, column_names: list[str]):
        assert column_names == ["id"]
        return [(i,) for i in self._existing_ids]


def test_sum_entity_column_coerces_string_values():
    mem = Memstore("mem")
    mem.consume(("t", [{"count": "5"}, {"count": "3"}, {"count": "7"}]))
    assert mem.sumEntityColumn("t", "count") == 15


def test_sum_entity_column_missing_type_is_zero():
    mem = Memstore("mem")
    assert mem.sumEntityColumn("missing", "count") == 0


def test_entity_count_is_an_alias_of_get_data_len_by_type():
    mem = Memstore("mem")
    mem.consume(("t", [{"id": 1}, {"id": 2}]))
    assert mem.entityCount("t") == 2 == mem.get_data_len_by_type("t")


def test_remove_not_existing_ids_keeps_only_matches():
    mem = Memstore("mem")
    mem.consume(("t", [{"id": "1", "v": "a"}, {"id": "2", "v": "b"}, {"id": "3", "v": "c"}]))
    client = _FakeClient(existing_ids=[1, 3])  # DB-typed int, memstore rows are CSV-typed str

    mem.removeNotExistingIds("t", "id", "ref", client)

    assert {r["id"] for r in mem.get_all_data_by_type("t")} == {"1", "3"}


def test_remove_not_existing_ids_removes_everything_when_none_match():
    mem = Memstore("mem")
    mem.consume(("t", [{"id": "1"}, {"id": "2"}]))
    client = _FakeClient(existing_ids=[99])

    mem.removeNotExistingIds("t", "id", "ref", client)

    assert mem.get_all_data_by_type("t") == []
