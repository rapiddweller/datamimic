import copy
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event, Lock
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.dialects import mysql, postgresql

from datamimic_ce.engine.dsl.api import GenerateStatement, KeyStatement
from datamimic_ce.engine.dsl.model.generation.generate_model import GenerateModel
from datamimic_ce.engine.dsl.model.values.scalar.key_model import KeyModel
from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.contracts import DataSourcePagination
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.runtime.api import create_run_session
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.contexts.geniter_context import GenIterContext
from datamimic_ce.engine.runtime.contracts import RunRequest
from datamimic_ce.engine.runtime.storage.memstore_manager import MemstoreManager
from datamimic_ce.engine.runtime.tasks.values.construction.factory import GeneratorUtil
from datamimic_ce.engine.runtime.tasks.values.construction.global_increment import GlobalIncrementGenerator
from datamimic_ce.engine.runtime.tasks.values.scalar.key_task import KeyTask


class DummyRootGenStmt(GenerateStatement):
    def __init__(self, type_: str = "generate", count: int = 10, num_process: int | None = None):
        self._type = type_
        self._count = count
        self._num_process = num_process
        self.generation_plan = None


class DummyStmt:
    """Minimal statement stub with the attributes used by generators."""

    def __init__(self, name: str, parent_stmt=None, database: str | None = None, root_gen=None):
        self.name = name
        self.parent_stmt = parent_stmt if parent_stmt is not None else root_gen
        self.database = database


class DummyCredential:
    def __init__(self, dbms: Dbms = Dbms.POSTGRESQL):
        self.dbms = dbms


class DummyRdbmsClient(RdbmsClient):
    """An RdbmsClient with in-memory sequences instead of a database."""

    def __init__(self, dbms: Dbms = Dbms.POSTGRESQL):
        self._seq: dict[str, int] = {}
        self._credential = DummyCredential(dbms)

    def reserve_sequence_block(
        self, sequence_name: str, count: int, table_name: str | None = None, column_name: str | None = None
    ) -> int:
        start = self._seq.get(sequence_name, 1000)
        self._seq[sequence_name] = start + count
        return start


@pytest.fixture()
def setup_context() -> SetupContext:
    return SetupContext(
        memstore_manager=MemstoreManager(),
        task_id=str(uuid.uuid4()),
        test_mode=True,
        test_result_exporter=TestResultExporter(),
        default_separator=",",
        default_locale="en_US",
        default_dataset="default",
        use_mp=False,
        descriptor_dir=Path("."),
        num_process=1,
        default_variable_prefix="${",
        default_variable_suffix="}",
        default_line_separator="\n",
        clients={},
        data_source_len={},
        properties={},
        namespace={},
        global_variables={},
        generators={},
        default_source_scripted=False,
        report_logging=False,
    )


def test_global_increment_generator_uses_cache_key(setup_context: SetupContext):
    util = GeneratorUtil(context=setup_context)

    # Build a simple parent chain to exercise qualified key logic
    root = DummyStmt("root")
    mid = DummyStmt("mid", parent_stmt=root)
    leaf = DummyStmt("leaf", parent_stmt=mid)

    g1 = util.create_generator("GlobalIncrementGenerator", stmt=leaf, key="mykey")
    g2 = util.create_generator("GlobalIncrementGenerator", stmt=leaf, key="mykey")

    assert g1 is g2
    assert [g1.generate(), g2.generate()] == [1, 2]
    assert "mykey" in setup_context.generators
    # Ensure no duplicate entry under raw generator string
    assert "GlobalIncrementGenerator" not in setup_context.generators


def test_global_increment_registry_preserves_key_scope_and_registered_start(setup_context: SetupContext):
    first = GlobalIncrementGenerator("parent.id", setup_context)
    same_key = GlobalIncrementGenerator("parent.id", setup_context)
    distinct_key = GlobalIncrementGenerator("parent.code", setup_context)

    assert [first.generate(), first.generate(), same_key.generate()] == [1, 2, 3]
    assert distinct_key.generate() == 1

    registry = setup_context.global_increment_registry
    assert registry is not None
    registry.register("configured", start=17)
    assert GlobalIncrementGenerator("configured", setup_context).generate() == 17


def test_deepcopy_of_cached_global_increment_preserves_legacy_copy_graph(
    setup_context: SetupContext,
) -> None:
    generator = GlobalIncrementGenerator("parent.id", setup_context)
    setup_context.generators["parent.id"] = generator
    client = object()
    setup_context.clients["client"] = client
    assert generator.generate() == 1
    copied = copy.deepcopy(setup_context)
    copied_generator = copied.generators["parent.id"]

    assert copied.clients["client"] is not client
    assert copied.global_increment_registry is None
    assert not hasattr(copied_generator, "_context")
    assert copied_generator.generate() == 2
    assert generator.generate() == 2
    assert GlobalIncrementGenerator("parent.id", setup_context).generate() == 3


def test_sequence_table_generator_uses_cache_key(setup_context: SetupContext):
    # Provide a minimal DB client for SequenceTableGenerator
    setup_context.clients["db1"] = DummyRdbmsClient()
    util = GeneratorUtil(context=setup_context)

    root_gen = DummyRootGenStmt(type_="gen", count=5)
    stmt = DummyStmt(name="id", parent_stmt=None, database="db1", root_gen=root_gen)

    pagination = DataSourcePagination(skip=0, limit=5)
    g1 = util.create_generator("SequenceTableGenerator", stmt=stmt, key="seq:orders:id", pagination=pagination)
    g2 = util.create_generator("SequenceTableGenerator", stmt=stmt, key="seq:orders:id", pagination=pagination)

    assert g1 is g2
    assert "seq:orders:id" in setup_context.generators
    assert "SequenceTableGenerator" not in setup_context.generators


@pytest.mark.parametrize("recover", [False, True])
def test_sequence_key_task_reconstruction_preserves_paginated_generation(setup_context: SetupContext, recover: bool):
    class RecoveringClient(DummyRdbmsClient):
        attempts = 0

        def reserve_sequence_block(self, sequence_name, count, table_name=None, column_name=None):
            self.attempts += 1
            if recover and self.attempts == 1:
                raise RuntimeError("sequence temporarily unavailable")
            return super().reserve_sequence_block(sequence_name, count, table_name, column_name)

    client = RecoveringClient()
    setup_context.clients["db1"] = client
    generate = GenerateStatement(GenerateModel(name="orders", count="5", type="orders"), None)
    key = KeyStatement(KeyModel(name="id", type="int", generator="SequenceTableGenerator", database="db1"), generate)
    generate.sub_statements = [key]
    key.sub_statements = []
    task = KeyTask(setup_context, key, DataSourcePagination(skip=0, limit=5))
    context = GenIterContext(setup_context, "orders")

    values = []
    for _ in range(5):
        task.execute(context)
        values.append(context.current_product["id"])

    assert values == list(range(1000, 1005))
    assert client.attempts == (2 if recover else 1)
    assert client._seq == {"orders_id_seq": 1005}


def test_sequence_table_generator_unpaginated_instance_is_repositioned_by_the_first_page(
    setup_context: SetupContext,
):
    """GenerateTask.pre_execute builds sub-tasks with pagination=None and reserves the block on
    that instance; the cached instance must serve the first page from its start, not be exhausted."""
    setup_context.clients["db1"] = DummyRdbmsClient()
    util = GeneratorUtil(context=setup_context)

    root_gen = DummyRootGenStmt(type_="gen", count=5)
    stmt = DummyStmt(name="id", parent_stmt=None, database="db1", root_gen=root_gen)

    unpaginated = util.create_generator("SequenceTableGenerator", stmt=stmt, key="seq:t:id")
    unpaginated.pre_execute(setup_context)
    assert setup_context.generators["seq:t:id"] is unpaginated

    paginated = util.create_generator(
        "SequenceTableGenerator", stmt=stmt, key="seq:t:id", pagination=DataSourcePagination(skip=0, limit=5)
    )
    assert paginated is unpaginated
    assert [paginated.generate() for _ in range(5)] == list(range(1000, 1005))

    same_page = util.create_generator(
        "SequenceTableGenerator", stmt=stmt, key="seq:t:id", pagination=DataSourcePagination(skip=0, limit=5)
    )
    assert same_page is paginated  # re-applying the page in use keeps the position


def test_datetime_generator_ast_path_uses_cache_key(setup_context: SetupContext):
    util = GeneratorUtil(context=setup_context)
    stmt = DummyStmt(name="date_field")
    gen_str = "DateTimeGenerator(min='2010-08-01', max='2020-08-31', input_format='%Y-%m-%d')"

    g1 = util.create_generator(gen_str, stmt=stmt, key="dt:test")
    g2 = util.create_generator(gen_str, stmt=stmt, key="dt:test")

    assert g1 is g2
    assert "dt:test" in setup_context.generators
    # Raw string should not be used as cache key when `key` is provided
    assert gen_str not in setup_context.generators


def test_dynamic_generator_instantiated_once_with_cache(setup_context: SetupContext):
    inst_count = {"n": 0}

    class CustomHeavyGenerator:
        cache_in_root = True

        def __init__(self):
            inst_count["n"] += 1

    # Register dynamic class in the context namespace
    setup_context.namespace["CustomHeavyGenerator"] = CustomHeavyGenerator

    util = GeneratorUtil(context=setup_context)
    stmt = DummyStmt(name="x")

    # Repeated calls with the same key must reuse the single instance
    for _ in range(1000):
        util.create_generator("CustomHeavyGenerator", stmt=stmt, key="heavy:1")

    assert inst_count["n"] == 1

    # Different cache keys should create separate instances
    util.create_generator("CustomHeavyGenerator", stmt=stmt, key="heavy:2")
    assert inst_count["n"] == 2


def test_sequence_table_generator_pagination_monotonic_and_bounded(setup_context: SetupContext):
    setup_context.clients["db1"] = DummyRdbmsClient()
    util = GeneratorUtil(context=setup_context)

    root_gen = DummyRootGenStmt(type_="gen", count=10)
    stmt = DummyStmt(name="id", parent_stmt=None, database="db1", root_gen=root_gen)

    pagination = DataSourcePagination(skip=2, limit=3)
    gen = util.create_generator("SequenceTableGenerator", stmt=stmt, key="seq:orders:id:p", pagination=pagination)

    values = []
    try:
        while True:
            values.append(gen.generate())
    except StopIteration:
        pass

    assert values == [1002, 1003, 1004]


def test_no_cache_when_generator_opt_out(setup_context: SetupContext):
    class CustomNoCacheGenerator:
        cache_in_root = False

    setup_context.namespace["CustomNoCacheGenerator"] = CustomNoCacheGenerator
    util = GeneratorUtil(context=setup_context)
    stmt = DummyStmt(name="x")

    g1 = util.create_generator("CustomNoCacheGenerator", stmt=stmt, key="nocache:1")
    g2 = util.create_generator("CustomNoCacheGenerator", stmt=stmt, key="nocache:1")

    # Should not be cached; different instances expected
    assert g1 is not g2
    assert "nocache:1" not in setup_context.generators


def test_sequence_table_generator_multi_process_partitions_non_overlapping():
    shared_client = DummyRdbmsClient()

    # Copy the parent-prepared generator to simulate worker context serialization.
    def mk_ctx() -> SetupContext:
        ctx = SetupContext(
            memstore_manager=MemstoreManager(),
            task_id=str(uuid.uuid4()),
            test_mode=True,
            test_result_exporter=TestResultExporter(),
            default_separator=",",
            default_locale="en_US",
            default_dataset="default",
            use_mp=True,
            descriptor_dir=Path("."),
            num_process=2,
            default_variable_prefix="${",
            default_variable_suffix="}",
            default_line_separator="\n",
            clients={},
            data_source_len={},
            properties={},
            namespace={},
            global_variables={},
            generators={},
            default_source_scripted=False,
            report_logging=False,
        )
        # Attach shared DB client
        ctx.clients["db1"] = shared_client
        return ctx

    ctx0 = mk_ctx()
    ctx1 = mk_ctx()

    root_gen = DummyRootGenStmt(type_="gen", count=10)
    root_gen.generation_plan = ("parent-plan", 10)
    stmt0 = DummyStmt(name="id", parent_stmt=None, database="db1", root_gen=root_gen)
    # Each process pages with its chunk's global skip (chunks are (0, 5) and (5, 10))
    pagination0 = DataSourcePagination(skip=0, limit=4)
    pagination1 = DataSourcePagination(skip=5, limit=4)
    util0 = GeneratorUtil(context=ctx0)
    util1 = GeneratorUtil(context=ctx1)

    parent = util0.create_generator("SequenceTableGenerator", stmt=stmt0, key="mp:seq")
    parent.pre_execute(ctx0)
    ctx1.generators["mp:seq"] = copy.deepcopy(parent)
    g0 = util0.create_generator("SequenceTableGenerator", stmt=stmt0, key="mp:seq", pagination=pagination0)
    worker_stmt = copy.deepcopy(stmt0)  # Worker statements and cached generators travel separately.
    g1 = util1.create_generator("SequenceTableGenerator", stmt=worker_stmt, key="mp:seq", pagination=pagination1)
    assert list(iter(g0.generate, None)) == list(range(1000, 1004))
    assert list(iter(g1.generate, None)) == list(range(1005, 1009))
    assert shared_client._seq == {"gen_id_seq": 1010}


def test_sequence_table_generator_rejects_mysql_multiprocessing(setup_context: SetupContext):
    setup_context.num_process = 2
    setup_context.clients["db1"] = DummyRdbmsClient(dbms=Dbms.MYSQL)
    stmt = DummyStmt(
        name="id",
        database="db1",
        root_gen=DummyRootGenStmt(type_="orders", count=5),
    )

    with pytest.raises(ValueError, match="MySQL source is single-process only"):
        GeneratorUtil(context=setup_context).create_generator(
            "SequenceTableGenerator",
            stmt=stmt,
            key="mysql:sequence",
        )


def _sequence_key_task(setup_context: SetupContext, pagination: DataSourcePagination, count: str = "10") -> KeyTask:
    generate = GenerateStatement(GenerateModel(name="orders", count=count, type="orders"), None)
    key = KeyStatement(KeyModel(name="id", type="int", generator="SequenceTableGenerator", database="db1"), generate)
    generate.sub_statements = [key]
    key.sub_statements = []
    return KeyTask(setup_context, key, pagination)


def _run_page(task: KeyTask, setup_context: SetupContext, rows: int) -> list[int]:
    context = GenIterContext(setup_context, "orders")
    values = []
    for _ in range(rows):
        task.execute(context)
        values.append(context.current_product["id"])
    return values


def test_sequence_key_task_later_pages_continue_the_sequence(setup_context: SetupContext):
    setup_context.clients["db1"] = DummyRdbmsClient()

    first = _run_page(_sequence_key_task(setup_context, DataSourcePagination(skip=0, limit=5)), setup_context, 5)
    second = _run_page(_sequence_key_task(setup_context, DataSourcePagination(skip=5, limit=5)), setup_context, 5)

    assert first + second == list(range(1000, 1010))


def test_sequence_key_task_process_chunk_uses_global_skip_once(setup_context: SetupContext):
    """numProcess=2, count=10: process 1 owns chunk (5, 10) and its pages carry the global skip."""
    setup_context.clients["db1"] = DummyRdbmsClient()
    setup_context.num_process = 2

    first = _run_page(_sequence_key_task(setup_context, DataSourcePagination(skip=5, limit=2)), setup_context, 2)
    second = _run_page(_sequence_key_task(setup_context, DataSourcePagination(skip=7, limit=3)), setup_context, 3)

    assert first + second == list(range(1005, 1010))


def test_sequence_page_cannot_emit_values_past_its_reservation(setup_context: SetupContext):
    client = DummyRdbmsClient()
    setup_context.clients["db1"] = client
    task = _sequence_key_task(setup_context, DataSourcePagination(skip=0, limit=2), count="1")
    context = GenIterContext(setup_context, "orders")
    task.execute(context)
    assert context.current_product["id"] == 1000
    with pytest.raises(StopIteration):
        task.execute(context)
    assert client._seq == {"orders_id_seq": 1001}


def test_sequence_key_task_repeated_invocation_of_the_same_page_reserves_a_new_block(setup_context: SetupContext):
    """A nested generate runs again with the same page: GenerateTask.pre_execute reserves a new
    block, and the page must start at that block, not stay on the exhausted cursor."""
    setup_context.clients["db1"] = DummyRdbmsClient()
    page = DataSourcePagination(skip=0, limit=5)
    runs = []
    for _ in range(2):
        _sequence_key_task(setup_context, None, count="5").pre_execute(setup_context)
        runs.append(_run_page(_sequence_key_task(setup_context, page, count="5"), setup_context, 5))

    assert runs[0] == [1000, 1001, 1002, 1003, 1004]
    assert runs[1] == [1005, 1006, 1007, 1008, 1009]


@pytest.mark.parametrize("prepare", [True, False])
@pytest.mark.parametrize("honor_lock", [True, False], ids=["serialized", "negative-control"])
@pytest.mark.parametrize(("dbms", "start_at"), [(Dbms.POSTGRESQL, 1020), (Dbms.MYSQL, 1020), (Dbms.MYSQL, 1)])
def test_sequence_reservation_under_forced_interleaving(
    setup_context, monkeypatch, prepare, honor_lock, dbms, start_at
):
    second_context = copy.deepcopy(setup_context)
    first_read = Event()
    second_attempt = Event()
    lock = Lock()
    # One backend has already requested nextval() on a CACHE 20 sequence starting at 1000.
    # Its local cache is below the shared high-water mark, which is the only value we read.
    next_value = start_at

    def run(context, first):
        client = object.__new__(RdbmsClient)
        client._credential = SimpleNamespace(dbms=dbms, db_schema="test", read_only=False)
        dialect = postgresql.dialect() if dbms is Dbms.POSTGRESQL else mysql.dialect()
        connection = MagicMock(dialect=dialect)
        connection.execution_options.return_value = connection
        engine = MagicMock()
        engine.connect.return_value.__enter__.return_value = connection
        engine.begin.return_value.__enter__.return_value = connection
        monkeypatch.setattr(client, "_create_engine", lambda: engine)
        context.clients["db1"] = client
        holds_lock = False

        def execute(query, params=None):
            nonlocal next_value, holds_lock
            sql = str(query)
            result = MagicMock()
            if "pg_advisory_xact_lock" in sql or "GET_LOCK" in sql:
                if honor_lock:
                    if not first:
                        second_attempt.set()
                    assert lock.acquire(timeout=5)
                    holds_lock = True
                result.scalar.return_value = 1
            elif "RELEASE_LOCK" in sql:
                end_transaction()
                result.scalar.return_value = 1
            elif "seqincrement" in sql:
                result.scalar_one_or_none.return_value = 1
            elif "SELECT last_value, is_called" in sql or "FROM information_schema.TABLES" in sql:
                snapshot = next_value
                if first and not first_read.is_set():
                    first_read.set()
                    assert second_attempt.wait(5)
                result.one.return_value = (snapshot - 1, True)
                if snapshot == 1 and "FROM information_schema.TABLES" in sql:
                    assert "EXTRA = 'auto_increment'" in sql and "AND NOT EXISTS" in sql
                result.scalar_one_or_none.return_value = snapshot
            elif "setval" in sql:
                next_value = params["last_value"] + 1
            elif "ALTER TABLE" in sql:
                next_value = int(sql.rsplit(" ", 1)[-1])
            elif "SET SESSION information_schema_stats_expiry" in sql:
                pass
            else:
                pytest.fail(f"Unexpected sequence SQL: {sql}")
            return result

        def end_transaction(*_exc):
            if holds_lock:
                lock.release()

        connection.execute.side_effect = execute
        connection.begin.return_value.__exit__.side_effect = end_transaction
        try:
            if prepare:
                _sequence_key_task(context, None, count="5").pre_execute(context)
                page = DataSourcePagination(skip=0, limit=5)
            else:
                page = None  # Like a key under <if>, with no GenerateTask.pre_execute visit.
            return _run_page(_sequence_key_task(context, page, count="5"), context, 5)
        finally:
            if not first:
                second_attempt.set()

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(run, setup_context, True)
        assert first_read.wait(5)
        second = executor.submit(run, second_context, False)
        assert first.result() == list(range(start_at, start_at + 5))
        second_start = start_at + 5 if honor_lock else start_at
        assert second.result() == list(range(second_start, second_start + 5))


@pytest.mark.parametrize("prepare", [True, False])
def test_legacy_split_reservation_boundary_can_overlap(prepare):
    count = 5
    boundary = 1000
    if prepare:
        # A and B advance by count before either takes its boundary.
        boundary += 2 * (count + 1)  # two calls to setval(nextval() + count)
    # Both the split pre_execute and the unprepared path subtracted count from nextval().
    first = range(boundary - count, boundary)
    second = range(boundary - count + 1, boundary + 1)
    assert len(set(first) & set(second)) == count - 1


@pytest.fixture()
def run_with_sequence_counter(monkeypatch):
    reservations = []
    counter = DummyRdbmsClient()

    def reserve(_client, sequence, count, table, column):
        reservations.append(count)
        return counter.reserve_sequence_block(sequence, count, table, column)

    monkeypatch.setattr(RdbmsClient, "reserve_sequence_block", reserve)

    def run(filename):
        request = RunRequest(Path(__file__).with_name(filename), test_mode=True, profile_loader=lambda *_: {})
        return create_run_session(request).execute().captured, reservations

    return run


def test_sequence_reserves_expanded_time_series_count(run_with_sequence_counter):
    captured, reservations = run_with_sequence_counter("sequence_table_timeseries.xml")
    assert reservations == [6]
    assert [row["id"] for row in captured["readings"]] == list(range(1000, 1006))


def test_lazy_sequence_reserves_once_per_nested_generate_invocation(run_with_sequence_counter):
    captured, reservations = run_with_sequence_counter("sequence_table_nested.xml")
    assert reservations == [3, 3]
    assert captured["children"] == [
        {"owner": owner, "id": identifier}
        for owner, start in ((1, 1000), (2, 1003))
        for identifier in range(start, start + 3)
    ]


@pytest.mark.parametrize("filename", ["sequence_table_nested_list.xml", "sequence_table_conditional_nested_list.xml"])
def test_sequence_reserves_each_nested_lists_own_cardinality(run_with_sequence_counter, filename):
    captured, reservations = run_with_sequence_counter(filename)
    assert reservations == [3, 3]
    assert [[item["id"] for item in row["items"]] for row in captured["parents"]] == [
        [1000, 1001, 1002],
        [1003, 1004, 1005],
    ]
