"""Typed requests accepted by the IO boundary."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, TypedDict


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

    def get_data_by_type(self, product_type: str | None) -> list[dict[str, object]]: ...

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
    "DataSourcePagination",
    "EntityValue",
    "ExportMetadata",
    "MemstoreSource",
    "SqlScriptClient",
    "SmokeExportRequest",
]
