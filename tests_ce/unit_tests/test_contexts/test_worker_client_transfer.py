from __future__ import annotations

import copy
import gc
import weakref
from pathlib import Path
from unittest.mock import patch

import pytest

from datamimic_ce.domains.api import RunSeed
from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
from datamimic_ce.engine.io.api import Client
from datamimic_ce.engine.io.clients.operations import clone_client_for_include
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.contexts.geniter_context import GenIterContext
from datamimic_ce.engine.runtime.contexts import context as context_module
from datamimic_ce.engine.dsl.model.setup.include_model import IncludeModel
from datamimic_ce.engine.dsl.model.setup.setup_model import SetupModel
from datamimic_ce.engine.dsl.model.generation.generate_model import GenerateModel
from datamimic_ce.engine.dsl.statements.base.statement import Statement
from datamimic_ce.engine.dsl.statements.generation.generate_statement import GenerateStatement
from datamimic_ce.engine.dsl.statements.setup.include_statement import IncludeStatement
from datamimic_ce.engine.dsl.statements.setup.setup_statement import SetupStatement
from datamimic_ce.engine.runtime.storage.memstore_manager import MemstoreManager
from datamimic_ce.engine.runtime.tasks.generate.workers.generate_worker import GenerateWorker
from datamimic_ce.engine.runtime.tasks.generate.workers import generate_worker as generate_worker_module
from datamimic_ce.engine.runtime.tasks.generate.task import GenerateTask
from datamimic_ce.engine.runtime.tasks.setup.include_task import IncludeTask
from datamimic_ce.engine.runtime.tasks.setup import setup_task as setup_task_module


class UnpickleableResource:
    def __deepcopy__(self, memo: dict[int, object]) -> object:
        raise TypeError("resource cannot be copied")

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("resource cannot be reduced")


class DescriptorClient(Client):
    def __init__(self) -> None:
        self.engine = UnpickleableResource()
        self.cache = UnpickleableResource()
        self.close_count = 0

    def __deepcopy__(self, memo: dict[int, object]) -> DescriptorClient:
        raise TypeError("client cannot be copied")

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("client cannot be reduced")


class CachedGenerator:
    def __init__(self, client: Client) -> None:
        self.client = client


class DecodeFailure:
    def __init__(self) -> None:
        self.value = True

    def __setstate__(self, state: dict[str, object]) -> None:
        raise RuntimeError("decode failure after client reference")

    def __deepcopy__(self, memo: dict[int, object]) -> DecodeFailure:
        copied = DecodeFailure()
        memo[id(self)] = copied
        return copied


def _context(
    client: Client, failure_graph: str | None = None, task_id: str = "worker-client-transfer"
) -> SetupContext:
    def make_closure(value: DescriptorClient):
        def helper() -> DescriptorClient:
            return value

        return helper

    default = lambda value=client: value
    closure = make_closure(client)
    properties: dict[str, object] = {"client": client}
    namespace: dict[str, object] = {"probe": client, "alias": client, "default": default, "closure": closure}
    generators = {"cached": CachedGenerator(client)}
    if failure_graph == "context":
        properties["decode_failure"] = DecodeFailure()
    elif failure_graph == "namespace_functions":
        def failing_helper(value=client, sentinel=DecodeFailure()):
            return value

        namespace["failing_helper"] = failing_helper
    elif failure_graph == "generators":
        generators["decode_failure"] = DecodeFailure()
    return SetupContext(
        memstore_manager=MemstoreManager(),
        task_id=task_id,
        test_mode=True,
        test_result_exporter=TestResultExporter(),
        default_separator="|",
        default_locale="en",
        default_dataset="US",
        use_mp=True,
        descriptor_dir=Path("."),
        num_process=2,
        default_variable_prefix="__",
        default_variable_suffix="__",
        default_line_separator="\n",
        clients={"db": client},
        properties=properties,
        namespace=namespace,
        generators=generators,
        run_seed=RunSeed.create(7),
    )


def _config() -> RdbmsConnectionConfig:
    return RdbmsConnectionConfig(
        dbms=Dbms.SQLITE,
        host=None,
        port=None,
        user=None,
        password=None,
        database="worker-transfer",
        db_schema=None,
    )


def test_worker_payload_replaces_descriptor_clients_in_all_three_graphs() -> None:
    sender = DescriptorClient()
    context = _context(sender)
    context.record_descriptor_client("db", sender, _config())

    payload = GenerateWorker.serialize_worker_context(context)
    receivers: list[DescriptorClient] = []

    def create(config: RdbmsConnectionConfig, task_id: str) -> DescriptorClient:
        receivers.append(DescriptorClient())
        return receivers[-1]

    with patch.object(generate_worker_module, "create_rdbms_client", side_effect=create) as create_client:
        received = GenerateWorker.deserialize_worker_context(payload)

    assert sender.close_count == 0
    assert received.clients["db"] is received.namespace["probe"]
    assert received.namespace["probe"] is received.namespace["alias"]
    assert received.properties["client"] is received.namespace["probe"]
    assert received.namespace["default"]() is received.namespace["closure"]()
    assert received.namespace["default"]() is not received.namespace["probe"]
    assert received.generators["cached"].client is not received.namespace["probe"]
    assert create_client.call_count == 3
    assert {call.args[1] for call in create_client.call_args_list} == {"worker-client-transfer"}


def test_overwritten_client_keeps_original_config_for_retired_capture() -> None:
    old_client = DescriptorClient()
    new_client = DescriptorClient()
    old_config = _config()
    new_config = old_config.model_copy(update={"database": "replacement"})
    context = _context(old_client)
    context.record_descriptor_client("db", old_client, old_config)
    context.record_descriptor_client("db", new_client, new_config)

    payload = GenerateWorker.serialize_worker_context(context)
    constructed: list[DescriptorClient] = []

    def create(_config: RdbmsConnectionConfig, _task_id: str) -> DescriptorClient:
        client = DescriptorClient()
        client.config_database = _config.database
        constructed.append(client)
        return client

    with patch.object(generate_worker_module, "create_rdbms_client", side_effect=create):
        received = GenerateWorker.deserialize_worker_context(payload)

    retired = received.namespace["probe"]
    assert received.clients["db"] is received.namespace["db"]
    assert retired is received.properties["client"]
    assert received.namespace["default"]() is received.namespace["closure"]()
    assert retired.config_database == old_config.database
    assert received.namespace["default"]().config_database == old_config.database
    assert received.clients["db"].config_database == new_config.database
    assert retired is not received.clients["db"]
    assert payload.client_configs == {0: old_config, 1: new_config}
    assert len(constructed) == 4


def test_worker_bindings_follow_current_client_map_aliases_and_removals() -> None:
    sender = DescriptorClient()
    context = _context(sender)
    context.record_descriptor_client("db", sender, _config())
    context.clients["alias"] = sender

    assert GenerateWorker.serialize_worker_context(context).client_bindings == {"db": 0, "alias": 0}

    del context.clients["db"]
    assert GenerateWorker.serialize_worker_context(context).client_bindings == {"alias": 0}

    context.clients["db"] = DescriptorClient()
    assert GenerateWorker.serialize_worker_context(context).client_bindings == {"alias": 0}


def test_worker_projection_resets_capture_but_keeps_memstore_state() -> None:
    context = _context(DescriptorClient())
    context.test_result_exporter.consume(("rows", [{"id": 1}]))
    context.memstore_manager.add_memstore("rows")

    projected = context.worker_projection()

    assert context.test_result_exporter.get_result() == {"rows": [{"id": 1}]}
    assert projected.test_result_exporter.get_result() == {}
    assert projected.memstore_manager.contain("rows")


def test_generate_task_execute_serializes_payload_before_two_worker_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = DescriptorClient()
    context = _context(client)
    context._test_mode = False
    context.record_descriptor_client("db", client, _config())
    statement = GenerateStatement(GenerateModel(name="rows", count="2"), parent_stmt=None)
    statement.sub_statements = []
    dispatched: list[object] = []

    monkeypatch.setattr(GenerateTask, "_determine_count", lambda *_args: 2)
    monkeypatch.setattr(GenerateTask, "_determine_num_workers", lambda *_args: 2)
    monkeypatch.setattr(GenerateTask, "_calculate_default_page_size", lambda *_args: 1)
    monkeypatch.setattr(GenerateTask, "pre_execute", lambda *_args: None)
    monkeypatch.setattr(GenerateTask, "export_memstore", lambda *_args: None)
    monkeypatch.setattr(GenerateTask, "finalize_temp_files_chunks", lambda *_args: None)
    monkeypatch.setattr(GenerateTask, "export_artifact_files", lambda *_args: None)
    monkeypatch.setattr("datamimic_ce.engine.runtime.tasks.generate.task.cleanup_exporter_chunks", lambda *_args: None)

    def dispatch(_self, payload, _statement, chunks, _page_size):
        dispatched.append((payload, chunks))
        return {statement.full_name: []}

    monkeypatch.setattr(
        "datamimic_ce.engine.runtime.tasks.generate.workers.multiprocessing_generate_worker."
        "MultiprocessingGenerateWorker.mp_process",
        dispatch,
    )

    result = GenerateTask(statement).execute(context)

    assert result == {"rows": []}
    assert len(dispatched) == 1
    payload, chunks = dispatched[0]
    assert isinstance(payload, context_module.WorkerContextPayload)
    assert payload.task_id == context.task_id
    assert chunks == [(0, 1), (1, 2)]


def test_worker_context_copy_does_not_dispose_sender_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    sender = DescriptorClient()
    context = _context(sender)
    disposed: list[Client] = []
    monkeypatch.setattr(context_module, "dispose_client_engine", disposed.append, raising=False)

    copied = copy.deepcopy(context)

    assert disposed == []
    assert copied.clients["db"] is copied.properties["client"] is sender


@pytest.mark.parametrize("graph", ["context", "namespace_functions", "generators"])
def test_partial_worker_graph_decode_keeps_receiver_clients_available_for_cleanup(graph: str) -> None:
    sender = DescriptorClient()
    context = _context(sender, graph)
    context.record_descriptor_client("db", sender, _config())
    payload = GenerateWorker.serialize_worker_context(context)
    constructed: list[DescriptorClient] = []

    def create(config: RdbmsConnectionConfig, task_id: str) -> DescriptorClient:
        constructed.append(DescriptorClient())
        return constructed[-1]

    def dispose(client: Client) -> None:
        assert isinstance(client, DescriptorClient)
        client.close_count += 1

    with patch.object(generate_worker_module, "create_rdbms_client", side_effect=create), patch.object(
        generate_worker_module, "dispose_client_engine", side_effect=dispose
    ):
        with pytest.raises(RuntimeError, match="decode failure after client reference"):
            GenerateWorker.deserialize_worker_context(payload)

    assert constructed
    assert all(client.close_count == 1 for client in constructed)


def test_geniter_include_history_does_not_retain_cleaned_client_clones(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = _context(RdbmsClient(_config(), task_id="include-lifetime"))
    parent_client = context.clients["db"]
    assert isinstance(parent_client, RdbmsClient)
    context.record_descriptor_client("db", parent_client, _config())
    parent_ref = weakref.ref(parent_client)

    class Engine:
        def __init__(self, token: int) -> None:
            self.token = token

        def dispose(self) -> None:
            close_events.append(self.token)

    clone_refs: list[weakref.ReferenceType[RdbmsClient]] = []
    close_events: list[int] = []

    def clone_with_disposable_engine(client: Client) -> Client:
        clone = clone_client_for_include(client)
        assert isinstance(clone, RdbmsClient)
        token = len(clone_refs)
        clone.engine = Engine(token)
        clone_refs.append(weakref.ref(clone))
        return clone

    monkeypatch.setattr(setup_task_module, "clone_client_for_include", clone_with_disposable_engine)
    def parse_include(*_args: object, **_kwargs: object) -> SetupStatement:
        statement = SetupStatement(SetupModel())
        statement.sub_statements = []
        return statement

    monkeypatch.setattr("datamimic_ce.engine.runtime.tasks.setup.include_task.DescriptorParser.parse", parse_include)
    include = IncludeTask(IncludeStatement(IncludeModel(uri="nested.xml")))

    for _ in range(50):
        geniter = GenIterContext(context, "rows")
        include.execute(geniter)
        del geniter
        gc.collect()

    assert parent_ref() is parent_client
    assert parent_client.engine is None
    assert len(clone_refs) == len(close_events)
    assert all(reference() is None for reference in clone_refs)


def test_geniter_include_error_cleans_and_releases_client_clone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = _context(RdbmsClient(_config(), task_id="include-error"))
    parent_client = context.clients["db"]
    assert isinstance(parent_client, RdbmsClient)
    context.record_descriptor_client("db", parent_client, _config())
    close_events: list[int] = []
    clone_refs: list[weakref.ReferenceType[RdbmsClient]] = []

    class Engine:
        def dispose(self) -> None:
            close_events.append(1)

    def clone_with_disposable_engine(client: Client) -> Client:
        clone = clone_client_for_include(client)
        assert isinstance(clone, RdbmsClient)
        clone.engine = Engine()
        clone_refs.append(weakref.ref(clone))
        return clone

    def parse_include(*_args: object, **_kwargs: object) -> SetupStatement:
        statement = SetupStatement(SetupModel())
        statement.sub_statements = [Statement(None, None)]
        return statement

    def fail_task(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("include setup failure")

    monkeypatch.setattr(setup_task_module, "clone_client_for_include", clone_with_disposable_engine)
    monkeypatch.setattr("datamimic_ce.engine.runtime.tasks.setup.include_task.DescriptorParser.parse", parse_include)
    monkeypatch.setattr(setup_task_module, "create_task", fail_task)
    include = IncludeTask(IncludeStatement(IncludeModel(uri="nested.xml")))

    with pytest.raises(RuntimeError, match="include setup failure"):
        include.execute(GenIterContext(context, "rows"))
    gc.collect()

    assert close_events == [1]
    assert len(clone_refs) == 1
    assert clone_refs[0]() is None
    assert context.clients["db"] is parent_client


def test_sqlite_worker_client_uses_unmodified_payload_task_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    context = _context(
        RdbmsClient(_config(), task_id="task-id-used-by-worker"), task_id="task-id-used-by-worker"
    )
    context.record_descriptor_client("db", context.clients["db"], _config())
    payload = GenerateWorker.serialize_worker_context(context)

    monkeypatch.chdir(tmp_path)
    received = GenerateWorker.deserialize_worker_context(payload)
    client = received.clients["db"]
    assert isinstance(client, RdbmsClient)
    assert client._task_id == "task-id-used-by-worker"
    assert client._create_engine().url.database == "db/worker-transfer.sqlite"
    GenerateWorker.cleanup_worker_context(received)

    with pytest.raises(ValueError, match="Task ID is required to create SQLite db in task folder"):
        RdbmsClient(_config(), task_id="")._create_engine()
