"""Scalar requests for IO-owned source operations."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from datamimic_ce.engine.dsl.vocabulary.source_capabilities import SourceFileFormat

# A where= condition over one file-source row; the runtime builds it, so IO does not import the runtime.
RowPredicate = Callable[[Mapping[str, object]], bool]


@dataclass(frozen=True)
class GenerateFileSourceRequest:
    source: str
    descriptor_dir: Path
    name: str
    separator: str
    cyclic: bool | None
    start_idx: int | None
    end_idx: int | None
    offset: int
    source_entity: str | None
    where: RowPredicate | None = None
    columns: tuple[str, ...] | None = None


@dataclass(frozen=True)
class GenerateFileSource:
    file_format: SourceFileFormat
    rows: list[dict]


@dataclass(frozen=True)
class CountSourceRequest:
    source: str
    source_id: tuple[str | None, str | None]
    descriptor_dir: Path
    element: str
    source_type: str | None
    source_entity: str | None
    name: str
    separator: str | None
    default_separator: str
    selector: str | None
    iteration_selector: str | None
    where: RowPredicate | None = None
    columns: tuple[str, ...] | None = None


@dataclass(frozen=True)
class VariableSourceRequest:
    source: str
    descriptor_dir: Path
    separator: str
    source_entity: str | None
    source_type: str | None
    name: str
    materialize_full_pool: bool
    cyclic: bool


__all__ = [
    "CountSourceRequest",
    "GenerateFileSource",
    "GenerateFileSourceRequest",
    "RowPredicate",
    "VariableSourceRequest",
]
