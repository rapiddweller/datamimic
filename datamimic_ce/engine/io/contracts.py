"""Typed requests accepted by the IO boundary."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Protocol, TypeAlias, TypedDict


class Exporter:
    pass


class ColumnKind(StrEnum):
    """Column type of a table that ``createTable`` creates; the RDBMS client maps each kind to a SQLAlchemy type."""

    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    BINARY = "binary"
    DATE = "date"
    DATETIME = "datetime"


# bool before int and datetime before date: each is a subclass of the type after it.
_VALUE_KINDS: tuple[tuple[type, ColumnKind], ...] = (
    (bool, ColumnKind.BOOLEAN),
    (int, ColumnKind.INTEGER),
    (float, ColumnKind.FLOAT),
    (Decimal, ColumnKind.DECIMAL),
    (datetime, ColumnKind.DATETIME),
    (date, ColumnKind.DATE),
    (str, ColumnKind.TEXT),
)


def column_kind_of_type(python_type: type) -> ColumnKind | None:
    """The column kind of a Python value type; None for a type no kind covers (NoneType included)."""
    return next((kind for covered, kind in _VALUE_KINDS if issubclass(python_type, covered)), None)


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


MemstoreRow: TypeAlias = dict[str, object]


class MemstoreSource(Protocol):
    """The read-only memstore surface consumed by data-source routing.

    A returned row list is live at the time of the read. A write or
    reconciliation may replace the stored list.
    """

    def get_all_data_by_type(self, product_type: str) -> list[MemstoreRow]: ...

    def get_data_by_type(self, product_type: str | None) -> list[MemstoreRow]: ...

    def get_data_len_by_type(self, entity_name: str | None) -> int: ...


class SqlScriptClient(Protocol):
    """Client capability required to execute a SQL script."""

    def execute_sql_script(self, query: str, /) -> None: ...


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
    "ColumnKind",
    "column_kind_of_type",
    "Exporter",
    "DataSourcePagination",
    "EntityValue",
    "ExportMetadata",
    "MemstoreRow",
    "MemstoreSource",
    "SqlScriptClient",
    "SmokeExportRequest",
]
