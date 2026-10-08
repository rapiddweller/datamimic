# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Memstore query API migration parity.

MemstoreTask binds the store into the DSL script namespace; these unit tests exercise the class directly.
"""

import logging
import math

import pytest

from datamimic_ce.engine.io.api import Memstore


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
    total = mem.sumEntityColumn("t", "count")
    assert total == 15
    assert type(total) is int


@pytest.mark.parametrize(
    ("values", "expected"),
    [(["1.25", "2"], 3.25), (["inf"], math.inf), (["nan"], math.nan)],
)
def test_sum_entity_column_returns_float_for_fractional_and_non_finite_totals(values, expected):
    mem = Memstore("mem")
    mem.consume(("t", [{"count": value} for value in values]))

    total = mem.sumEntityColumn("t", "count")

    assert type(total) is float
    if math.isnan(expected):
        assert math.isnan(total)
    else:
        assert total == expected


def test_sum_entity_column_missing_type_is_zero():
    mem = Memstore("mem")
    assert mem.sumEntityColumn("missing", "count") == 0


def test_sum_entity_column_skips_non_numeric_cells():
    # legacy-lenient: a stray placeholder must not abort the aggregation
    mem = Memstore("mem")
    mem.consume(("t", [{"count": "5"}, {"count": "n/a"}, {"count": None}, {"count": "7"}]))
    assert mem.sumEntityColumn("t", "count") == 12


def test_sum_entity_column_missing_column_stays_fatal():
    # leniency is per-CELL only; a wrong column NAME is a caller bug and must not sum to 0
    mem = Memstore("mem")
    mem.consume(("t", [{"count": "5"}]))
    with pytest.raises(KeyError):
        mem.sumEntityColumn("t", "amuont")


def test_entity_count_is_an_alias_of_get_data_len_by_type():
    mem = Memstore("mem")
    mem.consume(("t", [{"id": 1}, {"id": 2}]))
    assert mem.entityCount("t") == 2 == mem.get_data_len_by_type("t")


def test_missing_optional_entity_remains_strict_for_rows_and_lenient_for_length(caplog, monkeypatch):
    mem = Memstore("mem")
    monkeypatch.setattr(logging.getLogger("DATAMIMIC"), "propagate", True)

    with caplog.at_level(logging.ERROR, logger="DATAMIMIC"), pytest.raises(
        KeyError, match="Data naming 'None' is empty in memstore"
    ):
        mem.get_data_by_type(None)
    assert "Data naming 'None' is empty in memstore" in caplog.messages[0]

    caplog.clear()
    with caplog.at_level(logging.ERROR, logger="DATAMIMIC"):
        assert mem.get_data_len_by_type(None) == 0
    assert caplog.messages == ["Data having entity 'None' is empty in memstore"]


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


def test_remove_not_existing_ids_dispatches_for_missing_and_empty_products():
    class Client:
        def __init__(self):
            self.calls = []

        def get_random_rows_by_columns(self, table_name, column_names):
            self.calls.append((table_name, column_names))
            return []

    for product_type in ("missing", "empty"):
        mem = Memstore("mem")
        mem.consume(("empty", []))
        previous_empty = mem.get_data_by_type("empty")
        client = Client()

        assert mem.removeNotExistingIds(product_type, "customer_id", "Reference", client) is None

        assert client.calls == [("Reference", ["customer_id"])]
        assert mem.get_data_by_type(product_type) == []
        if product_type == "empty":
            assert mem.get_data_by_type("empty") is not previous_empty


def test_remove_not_existing_ids_replaces_list_and_preserves_survivor_aliases():
    mem = Memstore("mem")
    repeated = {"id": "2"}
    first = {"id": 1}
    # Incidental legacy quirk: missing, None and literal None IDs compare as the string None.
    missing = {}
    null = {"id": None}
    literal_null = {"id": "None"}
    rows = [repeated, {"id": "9"}, first, repeated, missing, null, literal_null]
    mem.consume(("t", rows))
    previous = mem.get_data_by_type("t")

    mem.removeNotExistingIds("t", "id", "ref", _FakeClient([None, 1, 2, 2]))

    current = mem.get_data_by_type("t")
    expected = [repeated, first, repeated, missing, null, literal_null]
    assert current is not previous
    assert current == expected
    assert all(actual is original for actual, original in zip(current, expected))
    assert previous == rows
    assert all(actual is original for actual, original in zip(previous, rows))
    assert current[0] is current[2]


def test_remove_not_existing_ids_preserves_storage_on_native_failures():
    sentinel = RuntimeError("lookup/conversion sentinel")

    class LookupFailure:
        def get_random_rows_by_columns(self, table_name, column_names):
            raise sentinel

    class ResultFailure:
        def get_random_rows_by_columns(self, table_name, column_names):
            yield (1,)
            raise sentinel

    class StringFailure:
        def __str__(self):
            raise sentinel

    scenarios = [
        (LookupFailure(), [{"id": 1}], RuntimeError),
        (ResultFailure(), [{"id": 1}], RuntimeError),
        (_FakeClient([StringFailure()]), [{"id": 1}], RuntimeError),
        (_FakeClient([1]), [{"id": 1}, {"id": StringFailure()}], RuntimeError),
        # Preserve existing native malformed-row failure; this does not validate a supported payload.
        (_FakeClient([1]), [{"id": 1}, object()], AttributeError),
    ]
    for client, rows, error_type in scenarios:
        mem = Memstore("mem")
        mem.consume(("t", rows))
        previous = mem.get_data_by_type("t")

        with pytest.raises(error_type) as caught:
            mem.removeNotExistingIds("t", "id", "ref", client)

        if error_type is RuntimeError:
            assert caught.value is sentinel
        assert mem.get_data_by_type("t") is previous
        assert previous == rows
