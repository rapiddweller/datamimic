"""The Memstore raw API is strict and returns live rows; IO owns cyclic copies."""

import pytest

from datamimic_ce.engine.io.contracts import DataSourcePagination
from datamimic_ce.engine.io.data_sources.router import read_generate_memstore_source
from datamimic_ce.engine.io.api import Memstore


def test_raw_getter_returns_live_list_and_distinguishes_empty_from_missing() -> None:
    memstore = Memstore("mem")
    memstore.consume(("rows", [{"id": 1}]))
    memstore.consume(("empty", []))

    raw_rows = memstore.get_data_by_type("rows")
    raw_rows.append({"id": 2})

    assert memstore.get_data_by_type("rows") == [{"id": 1}, {"id": 2}]
    assert memstore.get_data_by_type("empty") == []
    assert memstore.get_all_data_by_type("missing") == []
    with pytest.raises(KeyError, match="Data naming 'missing' is empty in memstore"):
        memstore.get_data_by_type("missing")


def test_raw_getter_rejects_removed_paging_arguments() -> None:
    memstore = Memstore("mem")
    memstore.consume(("rows", [{"id": 1}]))

    with pytest.raises(TypeError):
        memstore.get_data_by_type("rows", DataSourcePagination(skip=0, limit=1), True)


def test_cyclic_source_rows_are_deep_copied_from_raw_memstore() -> None:
    memstore = Memstore("mem")
    memstore.consume(
        (
            "rows",
            [
                {"id": 1, "nested": {"tags": ["original"]}},
                {"id": 2, "nested": {"tags": ["second"]}},
            ],
        )
    )

    selected = read_generate_memstore_source(
        memstore, "rows", DataSourcePagination(skip=0, limit=3), cyclic=True
    )
    selected[0]["nested"]["tags"].append("changed")

    assert [row["id"] for row in selected] == [1, 2, 1]
    assert selected[2]["nested"]["tags"] == ["original"]
    assert memstore.get_data_by_type("rows")[0]["nested"]["tags"] == ["original"]


def test_noncyclic_source_selection_copies_only_the_outer_list() -> None:
    memstore = Memstore("mem")
    memstore.consume(("rows", [{"id": 1}]))
    raw_rows = memstore.get_data_by_type("rows")

    selected = read_generate_memstore_source(memstore, "rows", None, cyclic=False)

    assert selected is not raw_rows
    assert selected[0] is raw_rows[0]
