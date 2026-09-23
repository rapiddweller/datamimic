"""Typed requests accepted by the IO boundary."""

from dataclasses import dataclass
from pathlib import Path

from pydantic import RootModel


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


__all__ = ["SmokeExportParameters", "SmokeExportRequest", "SmokeExportRows"]
