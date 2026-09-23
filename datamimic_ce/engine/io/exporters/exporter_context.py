from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from datamimic_ce.engine.io.clients.client import Client
from datamimic_ce.engine.io.exporters.exporter import Exporter
from datamimic_ce.engine.io.exporters.test_result_exporter import TestResultExporter


class MemstoreProvider(Protocol):
    def contain(self, memstore_id: str) -> bool: ...

    def get_memstore(self, memstore_id: str) -> Exporter: ...

    def get_memstores_list(self) -> list[str]: ...


class ExporterContext(Protocol):
    @property
    def clients(self) -> Mapping[str, Client]: ...

    @property
    def memstore_manager(self) -> MemstoreProvider: ...

    @property
    def test_result_exporter(self) -> TestResultExporter: ...

    @property
    def default_encoding(self) -> str: ...

    @property
    def default_line_separator(self) -> str: ...

    @property
    def default_separator(self) -> str: ...

    @property
    def descriptor_dir(self) -> Path: ...

    @property
    def task_id(self) -> str: ...

    @property
    def use_mp(self) -> bool | None: ...

    def get_client_by_id(self, client_id: str) -> Client | None: ...
