"""Scalar requests for IO-owned source operations."""

from dataclasses import dataclass
from pathlib import Path


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


__all__ = ["CountSourceRequest", "VariableSourceRequest"]
