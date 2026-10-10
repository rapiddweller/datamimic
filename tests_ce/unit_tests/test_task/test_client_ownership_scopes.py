from collections.abc import Callable
from types import SimpleNamespace

import pytest

from datamimic_ce.engine.dsl.api import DatabaseStatement, IncludeStatement, MemstoreStatement, SetupStatement
from datamimic_ce.engine.dsl.model.setup.database_model import DatabaseModel
from datamimic_ce.engine.dsl.model.setup.include_model import IncludeModel
from datamimic_ce.engine.dsl.model.setup.memstore_model import MemstoreModel
from datamimic_ce.engine.dsl.model.setup.setup_model import SetupModel
from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
from datamimic_ce.engine.io.api import RdbmsConnectionConfig
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.contexts.geniter_context import GenIterContext
from datamimic_ce.engine.runtime.tasks.base.task import CommonSubTask
from datamimic_ce.engine.runtime.tasks.generate.workers import generate_worker as worker_module
from datamimic_ce.engine.runtime.tasks.generate.workers.generate_worker import GenerateWorker
from datamimic_ce.engine.runtime.tasks.generate.workers.multiprocessing_generate_worker import (
    MultiprocessingGenerateWorker,
)
from datamimic_ce.engine.runtime.tasks.setup import setup_task as setup_task_module
from datamimic_ce.engine.runtime.tasks.setup.include_task import IncludeTask
from datamimic_ce.engine.runtime.tasks.setup.setup_task import SetupTask
from tests_ce.unit_tests.test_contexts.test_setup_context import _context


class Engine:
    def __init__(self, name: str, events: list[str], failure: BaseException | None = None):
        self.name, self.events, self.failure = name, events, failure

    def dispose(self) -> None:
        self.events.append(self.name)
        if self.failure is not None:
            raise self.failure


class Consumer(CommonSubTask):
    def __init__(self, statement: MemstoreStatement, action: Callable[[SetupContext], None]):
        self._statement, self.action = statement, action

    @property
    def statement(self) -> MemstoreStatement:
        return self._statement

    def execute(self, ctx: SetupContext | GenIterContext) -> None:
        self.action(ctx.root)


def database(name: str, database_name: str) -> DatabaseStatement:
    return DatabaseStatement(DatabaseModel(id=name, dbms=Dbms.SQLITE, database=database_name))


def setup(*statements) -> SetupStatement:
    result = SetupStatement(SetupModel())
    result.sub_statements = list(statements)
    return result


@pytest.mark.parametrize("declarations_only", [True, False])
def test_setup_binds_in_order_before_consumer_construction(monkeypatch, declarations_only):
    context = _context()
    events: list[str] = []
    consumer = MemstoreStatement(MemstoreModel(id="memory"))
    original_dispatch = setup_task_module.create_task

    def factory(config, task_id):
        events.append("factory-" + config.database)
        client = RdbmsClient(config, task_id)
        client.engine = Engine("close-" + config.database, events)
        return client

    def dispatch(stmt, ctx):
        if stmt is consumer:
            assert list(ctx.clients) == ["a", "b"]
            assert ctx.namespace["a"] is ctx.clients["a"]
            events.append("consumer-construction")
        return original_dispatch(stmt, ctx)

    monkeypatch.setattr(setup_task_module, "create_rdbms_client", factory)
    monkeypatch.setattr(setup_task_module, "create_task", dispatch)
    statements = [database("a", "first"), database("b", "second")]
    if not declarations_only:
        statements.append(consumer)
    SetupTask.execute_statements(setup(*statements), context)
    assert events == (
        []
        if declarations_only
        else ["factory-first", "factory-second", "consumer-construction", "close-first", "close-second"]
    )
    if declarations_only:
        assert context.clients == {}


@pytest.mark.parametrize("failure_point", ["second_factory", "task"])
def test_setup_failure_keeps_original_error_and_attempts_owned_cleanup(monkeypatch, failure_point):
    context = _context()
    closed: list[str] = []
    original_error = ValueError("original task failure")
    cleanup_error = RuntimeError("cleanup failure")
    injected = RdbmsClient(RdbmsConnectionConfig(**database("injected", "external").model.model_dump()), "test")
    injected.engine = Engine("injected", closed)
    context.add_client("injected", injected)
    consumer = MemstoreStatement(MemstoreModel(id="memory"))
    original_dispatch = setup_task_module.create_task

    def factory(config, task_id):
        if config.database == "second" and failure_point == "second_factory":
            raise original_error
        client = RdbmsClient(config, task_id)
        client.engine = Engine(config.database, closed, cleanup_error)
        return client

    def fail(_ctx):
        raise original_error

    def dispatch(stmt, ctx):
        return Consumer(consumer, fail) if stmt is consumer else original_dispatch(stmt, ctx)

    monkeypatch.setattr(setup_task_module, "create_rdbms_client", factory)
    monkeypatch.setattr(setup_task_module, "create_task", dispatch)
    with pytest.raises(ValueError) as caught:
        SetupTask.execute_statements(setup(database("a", "first"), database("b", "second"), consumer), context)
    assert caught.value is original_error
    assert closed == (["first"] if failure_point == "second_factory" else ["first", "second"])
    assert context.clients["injected"] is injected
    SetupTask._cleanup_owned_clients(context)
    assert "injected" not in closed


@pytest.mark.parametrize("scope", ["setup", "geniter"])
@pytest.mark.parametrize("fail", [False, True])
def test_include_shadowing_preserves_parent_clients_and_captures(monkeypatch, scope, fail):
    parent = _context()
    closed: list[str] = []
    config = RdbmsConnectionConfig(**database("db", "parent").model.model_dump())
    parent_client = RdbmsClient(config, parent.task_id)
    parent_engine = Engine("parent", closed)
    parent_client.engine = parent_engine
    parent.record_descriptor_client("db", parent_client, config)
    injected = RdbmsClient(config, parent.task_id)
    injected_engine = Engine("injected", closed)
    injected.engine = injected_engine
    parent.add_client("injected", injected)
    parent.namespace["alias"] = parent_client
    parent.namespace["default"] = lambda value=parent_client: value

    def closure():
        return parent_client

    parent.namespace["closure"] = closure
    consumer = MemstoreStatement(MemstoreModel(id="memory"))
    sub_setup = setup(database("db", "child"), consumer)
    original_dispatch = setup_task_module.create_task
    task_error = ValueError("include task failure")
    visited: list[bool] = []

    def factory(recipe, task_id):
        client = RdbmsClient(recipe, task_id)
        client.engine = Engine("child", closed)
        return client

    def consume(child):
        assert child.clients["db"].credential.database == "child"
        assert child.namespace["db"] is child.clients["db"]
        clone = child.namespace["alias"]
        assert clone is not parent_client and clone.engine is None
        assert child.namespace["default"]() is child.namespace["closure"]() is parent_client
        assert child.clients["injected"] is child.namespace["injected"] is injected
        clone.engine = Engine("clone", closed)
        visited.append(True)
        if fail:
            raise task_error

    def dispatch(stmt, ctx):
        return Consumer(consumer, consume) if stmt is consumer else original_dispatch(stmt, ctx)

    monkeypatch.setattr(setup_task_module, "create_rdbms_client", factory)
    monkeypatch.setattr(setup_task_module, "create_task", dispatch)
    monkeypatch.setattr(
        "datamimic_ce.engine.runtime.tasks.setup.include_task.DescriptorParser.parse", lambda *args, **kwargs: sub_setup
    )
    include = IncludeTask(IncludeStatement(IncludeModel(uri="child.xml")))
    ctx = parent if scope == "setup" else GenIterContext(parent, "rows")
    if fail:
        with pytest.raises(ValueError) as caught:
            include.execute(ctx)
        assert caught.value is task_error
    else:
        include.execute(ctx)
    assert visited == [True]
    assert closed == ["clone", "child"]
    assert parent.clients["db"] is parent.namespace["alias"] is parent_client
    assert parent_client.engine is parent_engine
    assert injected.engine is injected_engine


def test_worker_error_survives_multiple_cleanup_failures(monkeypatch):
    context = _context()
    closed: list[str] = []
    config = RdbmsConnectionConfig(**database("db", "worker").model.model_dump())
    for name in ["a", "b"]:
        client = RdbmsClient(config, context.task_id)
        client.engine = Engine(name, closed, RuntimeError("cleanup"))
        context.record_descriptor_client(name, client, config)
    injected = RdbmsClient(config, context.task_id)
    injected.engine = Engine("injected", closed)
    context.add_client("injected", injected)
    original_error = ValueError("row failure")

    def fail(*args):
        raise original_error

    monkeypatch.setattr(GenerateWorker, "deserialize_worker_context", lambda payload: context)
    monkeypatch.setattr(GenerateWorker, "mp_preprocess", lambda ctx, worker_id: None)
    monkeypatch.setattr(GenerateWorker, "generate_and_export_data_by_chunk", fail)
    with pytest.raises(ValueError) as caught:
        MultiprocessingGenerateWorker.mp_wrapper((None, SimpleNamespace(full_name="rows"), 1, 0, 1, 1))
    assert caught.value is original_error
    assert closed == ["a", "b"]
    GenerateWorker.cleanup_worker_context(context)
    assert closed == ["a", "b"]


def test_same_map_assignment_and_rebound_namespace_survive_decode(monkeypatch):
    context = _context()
    config = RdbmsConnectionConfig(**database("db", "worker").model.model_dump())
    client = RdbmsClient(config, context.task_id)
    context.record_descriptor_client("db", client, config)
    bindings = dict(context._descriptor_client_bindings)
    original_map = context.clients
    context.clients = original_map
    assert context.clients is original_map and context._descriptor_client_bindings == bindings
    context.namespace["db"] = "script rebound value"
    monkeypatch.setattr(worker_module, "create_rdbms_client", RdbmsClient)
    received = GenerateWorker.deserialize_worker_context(GenerateWorker.serialize_worker_context(context))
    assert received.namespace["db"] == "script rebound value"
    assert received.clients["db"].credential.database == "worker"


@pytest.mark.parametrize("cleanup", [SetupTask._cleanup_owned_clients, GenerateWorker.cleanup_worker_context])
def test_cleanup_without_task_error_attempts_all_and_raises_first_exception(cleanup):
    context = _context()
    closed: list[str] = []
    config = RdbmsConnectionConfig(**database("db", "worker").model.model_dump())
    first_error = RuntimeError("first cleanup failure")
    second_error = ValueError("second cleanup failure")
    for name, error in [("first", first_error), ("second", second_error)]:
        client = RdbmsClient(config, context.task_id)
        client.engine = Engine(name, closed, error)
        context.record_descriptor_client(name, client, config)
    with pytest.raises(RuntimeError) as caught:
        cleanup(context)
    assert caught.value is first_error
    assert closed == ["first", "second"]
    cleanup(context)
    assert closed == ["first", "second"]
