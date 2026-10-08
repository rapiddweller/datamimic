from inspect import Parameter, signature
from pathlib import Path
from types import SimpleNamespace
from typing import get_type_hints

import pytest

from datamimic_ce.engine.io.clients.client import Client, ClientLookup, RegisteredClient
from datamimic_ce.engine.io.contracts import DataSourcePagination
from datamimic_ce.engine.io.data_sources import router as io_source_router
from datamimic_ce.engine.io.exporters.core import routing
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.storage.memstore_manager import MemstoreManager
from datamimic_ce.engine.runtime.tasks.generate import task as generate_task_module
from datamimic_ce.engine.runtime.tasks.generate.task import GenerateTask
from datamimic_ce.engine.runtime.tasks.sources import generate as generate_source_module


def _context(clients: dict[str, Client]) -> SetupContext:
    return SetupContext(
        memstore_manager=MemstoreManager(),
        task_id="lookup-test",
        test_mode=True,
        test_result_exporter=TestResultExporter(),
        default_separator="|",
        default_locale="en",
        default_dataset="US",
        use_mp=False,
        descriptor_dir=Path("."),
        num_process=1,
        default_variable_prefix="{{",
        default_variable_suffix="}}",
        default_line_separator="\n",
        clients=clients,
    )


def test_client_lookup_protocol_is_structural_and_positional_only() -> None:
    assert ClientLookup._is_protocol
    assert get_type_hints(routing.has_mongodb_upsert_target)["clients"] is ClientLookup
    parameters = signature(ClientLookup.get).parameters
    assert parameters["key"].kind is Parameter.POSITIONAL_ONLY
    hints = get_type_hints(ClientLookup.get)
    assert hints == {"key": str, "return": RegisteredClient | None}


def test_mapping_lookup_is_lazy_and_uses_first_dot_then_short_circuits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mongo = Client()

    class Clients(dict[str, Client]):
        calls: list[str]

        def __init__(self, **clients: Client) -> None:
            super().__init__(clients)
            self.calls = []

        def get(self, key: str, /) -> Client | None:
            self.calls.append(key)
            return super().get(key)

    class OrderedTargets(set[str]):
        def __iter__(self):
            yield "mongo.upsert"
            yield "later.upsert"
            yield "malformed.upsert.extra"
            yield "nested.child.upsert"

    clients = Clients(mongo=mongo)
    monkeypatch.setattr(routing, "is_mongodb_client", lambda client: client is mongo)

    assert not routing.has_mongodb_upsert_target(
        {"plain", "mongo.delete", "malformed.upsert.extra", "nested.child.upsert"}, clients
    )
    assert clients.calls == []
    assert routing.has_mongodb_upsert_target(OrderedTargets(), clients)
    assert clients.calls == ["mongo"]


def test_mapping_lookup_and_client_predicate_exceptions_propagate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class LookupFailure(RuntimeError):
        pass

    class FailingLookup(dict[str, Client]):
        def get(self, key: str, /) -> Client | None:
            raise LookupFailure(key)

    with pytest.raises(LookupFailure, match="mongo"):
        routing.has_mongodb_upsert_target({"mongo.upsert"}, FailingLookup())

    def fail_predicate(_client: Client) -> bool:
        raise LookupFailure("predicate")

    monkeypatch.setattr(routing, "is_mongodb_client", fail_predicate)
    with pytest.raises(LookupFailure, match="predicate"):
        routing.has_mongodb_upsert_target({"mongo.upsert"}, {"mongo": Client()})


def test_generate_task_only_changes_zero_count_for_mongodb_upsert(monkeypatch: pytest.MonkeyPatch) -> None:
    mongo = Client()
    monkeypatch.setattr(routing, "is_mongodb_client", lambda client: client is mongo)
    monkeypatch.setattr(generate_task_module, "set_data_source_length", lambda *_: None)

    def determine(target: str, client: Client) -> int:
        context = _context({"mongo": client})
        statement = SimpleNamespace(
            count="0",
            min_count=None,
            max_count=None,
            source=None,
            selector=None,
            targets={target},
            name="rows",
            full_name="rows",
            cyclic=False,
            distribution=None,
            sub_statements=[],
            get_time_series_config=lambda: None,
        )
        return GenerateTask(statement)._determine_count(context)

    assert determine("mongo.delete", mongo) == 0
    assert determine("mongo.upsert", Client()) == 0
    assert determine("mongo.upsert", mongo) == 1


@pytest.mark.parametrize(("target", "expected"), [("mongo.upsert", [{}]), ("mongo.delete", [])])
def test_source_loader_preserves_empty_mongodb_read_behavior(
    monkeypatch: pytest.MonkeyPatch, target: str, expected: list[dict[str, object]]
) -> None:
    mongo = Client()
    context = _context({"mongo": mongo})
    monkeypatch.setattr(routing, "is_mongodb_client", lambda client: client is mongo)
    monkeypatch.setattr(io_source_router, "is_mongodb_client", lambda client: client is mongo)
    monkeypatch.setattr(io_source_router, "database_get_by_page_with_type", lambda *_: [])
    monkeypatch.setattr(generate_source_module, "read_generate_file_source", lambda *_: None)

    statement = SimpleNamespace(
        variable_prefix=None,
        variable_suffix=None,
        cyclic=False,
        offset=0,
        full_name="rows",
        name="rows",
        source_entity="rows",
        type=None,
        selector=None,
        targets={target},
    )
    rows, _ = generate_source_module.load_generate_source(
        context, statement, "mongo", "|", False, None, None, DataSourcePagination(skip=0, limit=1)
    )
    assert rows == expected
