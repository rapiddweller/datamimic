"""Memstore is raw storage; IO owns source windows and Runtime owns orchestration."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from datamimic_ce.engine.io.contracts import DataSourcePagination
from datamimic_ce.engine.io.data_sources import router as io_source_router
from datamimic_ce.engine.io.data_sources import variable as io_variable_sources
from datamimic_ce.engine.io.data_sources.boundary.models import VariableSourceRequest
from datamimic_ce.engine.io.exporters.memory.memstore import Memstore
from datamimic_ce.engine.runtime.tasks.sources import generate as generate_source_router

ROWS = [{"id": 1}, {"id": 2}, {"id": 3}]


class _RawMemstore:
    """Expose only raw reads, so source operations cannot delegate selection to Memstore."""

    def __init__(self, rows: list[dict[str, object]] | None = None) -> None:
        self.rows = {} if rows is None else {"rows": rows}

    def get_all_data_by_type(self, product_type: str) -> list[dict[str, object]]:
        return self.rows.get(product_type, [])

    def get_data_by_type(self, product_type: str) -> list[dict[str, object]]:
        try:
            return self.rows[product_type]
        except KeyError as error:
            raise KeyError(f"Data naming '{product_type}' is empty in memstore") from error


def test_generate_memstore_source_selects_window_and_wraps_cyclically() -> None:
    read = io_source_router.read_generate_memstore_source
    memstore = _RawMemstore(ROWS)

    assert read(memstore, "rows", DataSourcePagination(skip=1, limit=2), False) == [
        {"id": 2},
        {"id": 3},
    ]
    assert read(memstore, "rows", DataSourcePagination(skip=2, limit=4), True) == [
        {"id": 3},
        {"id": 1},
        {"id": 2},
        {"id": 3},
    ]


def test_variable_memstore_source_selects_page_and_cycle_from_raw_rows() -> None:
    request = VariableSourceRequest(
        source="mem",
        descriptor_dir=Path("/descriptor"),
        separator="|",
        source_entity="rows",
        source_type=None,
        name="rows",
        materialize_full_pool=False,
        cyclic=True,
    )

    rows = io_variable_sources.read_variable_source(
        request,
        None,
        _RawMemstore(ROWS),
        DataSourcePagination(skip=2, limit=4),
    )

    assert list(rows or []) == [{"id": 3}, {"id": 1}, {"id": 2}, {"id": 3}]


def test_variable_full_pool_missing_is_empty_but_paged_missing_is_strict() -> None:
    raw_memstore = _RawMemstore()
    full_pool_request = VariableSourceRequest(
        source="mem",
        descriptor_dir=Path("/descriptor"),
        separator="|",
        source_entity="missing",
        source_type=None,
        name="missing",
        materialize_full_pool=True,
        cyclic=False,
    )
    paged_request = VariableSourceRequest(
        source="mem",
        descriptor_dir=Path("/descriptor"),
        separator="|",
        source_entity="missing",
        source_type=None,
        name="missing",
        materialize_full_pool=False,
        cyclic=False,
    )

    assert io_variable_sources.read_variable_source(full_pool_request, None, raw_memstore, None) == []
    with pytest.raises(KeyError, match="Data naming 'missing' is empty in memstore"):
        io_variable_sources.read_variable_source(
            paged_request, None, raw_memstore, DataSourcePagination(skip=0, limit=1)
        )


def test_nested_key_memstore_source_reads_raw_rows_for_io_owned_windowing() -> None:
    rows = io_source_router.read_nested_key_source(
        Path("/descriptor"),
        "mem",
        "mem",
        "list",
        "rows",
        "rows",
        None,
        "|",
        True,
        _RawMemstore(ROWS),
    )

    assert rows == ROWS


def test_runtime_generate_routes_memstore_reads_through_io_facade(monkeypatch: pytest.MonkeyPatch) -> None:
    memstore = _RawMemstore(ROWS)
    source_read = Mock(return_value=[{"id": 2}])
    monkeypatch.setattr(generate_source_router, "read_generate_memstore_source", source_read, raising=False)
    root = SimpleNamespace(
        descriptor_dir=Path("/descriptor"),
        default_variable_prefix="{{",
        default_variable_suffix="}}",
        memstore_manager=SimpleNamespace(contain=lambda source: source == "mem", get_memstore=lambda _: memstore),
        clients={},
    )
    context = SimpleNamespace(root=root)
    statement = SimpleNamespace(
        variable_prefix=None,
        variable_suffix=None,
        cyclic=True,
        offset=0,
        full_name="products",
        name="products",
        source_entity="rows",
        type=None,
        selector=None,
        targets=set(),
    )
    pagination = DataSourcePagination(skip=1, limit=1)

    rows, build_from_source = generate_source_router.load_generate_source(
        context, statement, "mem", "|", False, None, None, pagination
    )

    assert rows == [{"id": 2}]
    assert build_from_source is True
    source_read.assert_called_once_with(memstore, "rows", pagination, True)


def test_memstore_row_lookup_distinguishes_missing_from_present_empty() -> None:
    memstore = Memstore("mem")
    memstore.consume(("empty", []))

    with pytest.raises(KeyError, match="Data naming 'missing' is empty in memstore"):
        memstore.get_data_by_type("missing")

    assert memstore.get_data_by_type("empty") == []
    assert memstore.get_data_len_by_type("missing") == 0
    assert memstore.get_data_len_by_type("empty") == 0
