"""Typed requests accepted by the IO boundary."""

import copy
import itertools
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, TypedDict, TypeVar


class ExportMetadata(TypedDict, total=False):
    target_entity: str
    selector: str
    type: str


class EntityValue(ABC):
    @abstractmethod
    def to_dict(self) -> Mapping[str, object]: ...


class DataSourcePagination:
    """Page window for source reads."""

    def __init__(self, skip: int, limit: int):
        self._skip = skip
        self._limit = limit

    @property
    def skip(self) -> int:
        return self._skip

    @property
    def limit(self) -> int:
        return self._limit


class MemstoreSource(Protocol):
    """The read-only memstore surface consumed by data-source routing."""

    def get_all_data_by_type(self, product_type: str) -> list[dict[str, object]]: ...

    def get_data_by_type(
        self, product_type: str | None, pagination: DataSourcePagination | None, cyclic: bool
    ) -> list[dict[str, object]]: ...

    def get_data_len_by_type(self, entity_name: str | None) -> int: ...


_Row = TypeVar("_Row")


def select_rows(
    data: Iterable[_Row], pagination: DataSourcePagination | None, cyclic: bool = False, offset: int = 0
) -> list[_Row]:
    """Apply one IO-owned page window, including cyclic wrap after an offset."""
    if offset:
        data = list(data)[offset:]
    start = 0 if pagination is None else pagination.skip
    end = len(list(data)) if pagination is None else pagination.skip + pagination.limit
    source: Iterable[_Row] = itertools.cycle(data) if cyclic else data
    rows = itertools.islice(source, start, end)
    return [copy.deepcopy(row) for row in rows] if cyclic else list(rows)


def select_row_iterator(
    data: Iterable[_Row], pagination: DataSourcePagination | None, cyclic: bool = False
) -> Iterator[_Row]:
    """Return the selected page as an iterator, repeating only that page when cyclic."""
    start = 0 if pagination is None else pagination.skip
    end = len(list(data)) if pagination is None else pagination.skip + pagination.limit
    source: Iterable[_Row] = itertools.cycle(data) if cyclic else data
    selected = itertools.islice(source, start, end)
    return itertools.cycle(list(selected)[: end - start]) if cyclic else selected


@dataclass(frozen=True)
class SmokeExportRequest:
    descriptor_dir: Path
    task_id: str
    basename: str
    full_name: str
    rows: list[dict[str, object]]
    exporter_name: str
    params: dict[str, object]
    default_separator: str
    default_line_separator: str


__all__ = [
    "DataSourcePagination",
    "EntityValue",
    "ExportMetadata",
    "MemstoreSource",
    "SmokeExportRequest",
    "select_row_iterator",
    "select_rows",
]
