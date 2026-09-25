"""Typed requests accepted by the IO boundary."""

import copy
import itertools
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from pydantic import RootModel


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


class SmokeExportRows(RootModel[list[dict[str, object]]]):
    pass


class SmokeExportParameters(RootModel[dict[str, object]]):
    pass


@dataclass(frozen=True)
class SmokeExportRequest:
    descriptor_dir: Path
    task_id: str
    basename: str
    full_name: str
    rows: SmokeExportRows
    exporter_name: str
    params: SmokeExportParameters


__all__ = [
    "DataSourcePagination",
    "SmokeExportParameters",
    "SmokeExportRequest",
    "SmokeExportRows",
    "select_row_iterator",
    "select_rows",
]
