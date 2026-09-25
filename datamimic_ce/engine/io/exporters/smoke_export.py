"""Buffered file-export execution used by bounded authoring smoke checks."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from datamimic_ce.engine.io.clients.client import Client
from datamimic_ce.engine.io.contracts import SmokeExportRequest
from datamimic_ce.engine.io.exporters.exporter import Exporter
from datamimic_ce.engine.io.exporters.exporter_config import ExporterConfig
from datamimic_ce.engine.io.exporters.exporter_context import ExporterContext, MemstoreProvider
from datamimic_ce.engine.io.exporters.exporter_state_manager import ExporterStateManager
from datamimic_ce.engine.io.exporters.exporter_util import _BUFFERED_EXPORTERS
from datamimic_ce.engine.io.exporters.test_result_exporter import TestResultExporter


@dataclass
class _SmokeExporterContext:
    descriptor_dir: Path
    task_id: str
    test_result_exporter: TestResultExporter = field(default_factory=TestResultExporter)

    @property
    def clients(self) -> Mapping[str, Client]:
        return {}

    @property
    def memstore_manager(self) -> MemstoreProvider:
        return self

    @property
    def default_encoding(self) -> str:
        return "utf-8"

    @property
    def default_line_separator(self) -> str:
        return "\n"

    @property
    def default_separator(self) -> str:
        return ","

    @property
    def use_mp(self) -> bool:
        return False

    def get_client_by_id(self, client_id: str) -> Client | None:
        return None

    def contain(self, memstore_id: str) -> bool:
        return False

    def get_memstore(self, memstore_id: str) -> Exporter:
        raise KeyError(memstore_id)

    def get_memstores_list(self) -> list[str]:
        return []


def smoke_export(request: SmokeExportRequest) -> int:
    params = request.params.root
    rows = request.rows.root
    chunk_size = params.get("chunk_size")
    if chunk_size is not None and not isinstance(chunk_size, int):
        raise TypeError("chunk_size target option must be an integer")
    encoding = params.get("encoding")
    if encoding is not None and not isinstance(encoding, str):
        raise TypeError("encoding target option must be a string")

    context: ExporterContext = _SmokeExporterContext(
        descriptor_dir=request.descriptor_dir,
        task_id=request.task_id,
    )
    config = ExporterConfig(
        setup_context=context,
        product_name=request.basename,
        chunk_size=chunk_size,
        encoding=encoding,
        export_uri=None,
        track_serialized_rows=True,
    )
    exporter = _BUFFERED_EXPORTERS[request.exporter_name](config, dict(params))
    state_manager = ExporterStateManager(worker_id=1)
    exporter.consume((request.basename, rows), request.full_name, state_manager)
    exporter.finalize_chunks(1)
    return exporter.count_buffered_rows(1)
