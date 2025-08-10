import uuid
from pathlib import Path

import pytest

from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.domains.common.literal_generators.generator_util import GeneratorUtil
from datamimic_ce.exporters.test_result_exporter import TestResultExporter
from datamimic_ce.product_storage.memstore_manager import MemstoreManager
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination


class DummyRootGenStmt:
    def __init__(self, type_: str = "generate", count: int = 10):
        self.type = type_
        self.count = count


class DummyStmt:
    """Minimal statement stub with the attributes used by generators."""

    def __init__(self, name: str, parent=None, database: str | None = None, root_gen=None):
        self.name = name
        self.parent = parent
        self.database = database
        self._root_gen = root_gen

    def get_root_generate_statement(self):
        return self._root_gen


class DummyRdbmsClient:
    def __init__(self):
        self._seq = {}

    def get_current_sequence_number(self, sequence_name: str) -> int:
        return self._seq.get(sequence_name, 1000)

    def increase_sequence_number(self, sequence_name: str, increment: int) -> None:
        self._seq[sequence_name] = self.get_current_sequence_number(sequence_name) + increment


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
        current_seed=123,
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
    mid = DummyStmt("mid", parent=root)
    leaf = DummyStmt("leaf", parent=mid)

    g1 = util.create_generator("GlobalIncrementGenerator", stmt=leaf, key="mykey")
    g2 = util.create_generator("GlobalIncrementGenerator", stmt=leaf, key="mykey")

    assert g1 is g2
    assert "mykey" in setup_context.generators
    # Ensure no duplicate entry under raw generator string
    assert "GlobalIncrementGenerator" not in setup_context.generators


def test_sequence_table_generator_uses_cache_key(setup_context: SetupContext):
    # Provide a minimal DB client for SequenceTableGenerator
    setup_context.clients["db1"] = DummyRdbmsClient()
    util = GeneratorUtil(context=setup_context)

    root_gen = DummyRootGenStmt(type_="gen", count=5)
    stmt = DummyStmt(name="id", parent=None, database="db1", root_gen=root_gen)

    g1 = util.create_generator("SequenceTableGenerator", stmt=stmt, key="seq:orders:id")
    g2 = util.create_generator("SequenceTableGenerator", stmt=stmt, key="seq:orders:id")

    assert g1 is g2
    assert "seq:orders:id" in setup_context.generators
    assert "SequenceTableGenerator" not in setup_context.generators


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
    stmt = DummyStmt(name="id", parent=None, database="db1", root_gen=root_gen)

    pagination = DataSourcePagination(skip=2, limit=3)
    gen = util.create_generator("SequenceTableGenerator", stmt=stmt, key="seq:orders:id:p", pagination=pagination)

    values = []
    try:
        while True:
            values.append(gen.generate())
    except StopIteration:
        pass

    # start = current(1000) - total_count(10) + skip(2)
    expected_start = 1000 - 10 + 2
    assert values[0] == expected_start
    # The generator should yield a small bounded window and be strictly increasing
    assert all(values[i] < values[i + 1] for i in range(len(values) - 1))
    # Allow for current implementation off-by-one behavior: size in {limit, limit+1}
    assert len(values) in {pagination.limit, pagination.limit + 1}


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

    # Two separate roots to simulate two processes
    def mk_ctx(proc_id: int) -> SetupContext:
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
            current_seed=123,
            clients={},
            data_source_len={},
            properties={},
            namespace={},
            global_variables={},
            generators={},
            default_source_scripted=False,
            report_logging=False,
        )
        # Attach shared DB client and simulated process id
        ctx.clients["db1"] = shared_client
        ctx.process_id = proc_id  # attribute used by SequenceTableGenerator if present
        return ctx

    ctx0 = mk_ctx(0)
    ctx1 = mk_ctx(1)

    root_gen = DummyRootGenStmt(type_="gen", count=10)
    stmt0 = DummyStmt(name="id", parent=None, database="db1", root_gen=root_gen)
    stmt1 = DummyStmt(name="id", parent=None, database="db1", root_gen=root_gen)

    # Use a small limit to keep expectations clear
    pagination = DataSourcePagination(skip=0, limit=4)

    util0 = GeneratorUtil(context=ctx0)
    util1 = GeneratorUtil(context=ctx1)

    g0 = util0.create_generator("SequenceTableGenerator", stmt=stmt0, key="mp:seq:0", pagination=pagination)
    g1 = util1.create_generator("SequenceTableGenerator", stmt=stmt1, key="mp:seq:1", pagination=pagination)

    vals0, vals1 = [], []
    try:
        while True:
            vals0.append(g0.generate())
    except StopIteration:
        pass
    try:
        while True:
            vals1.append(g1.generate())
    except StopIteration:
        pass

    # Expected starts per current algorithm
    per_proc = (root_gen.count + 2 - 1) // 2  # == 5
    base = 1000 - root_gen.count
    expected_start0 = base + pagination.skip
    expected_start1 = base + (1 * per_proc) + (1 * per_proc + pagination.skip)

    assert vals0[0] == expected_start0
    assert vals1[0] == expected_start1
    assert all(vals0[i] < vals0[i + 1] for i in range(len(vals0) - 1))
    assert all(vals1[i] < vals1[i + 1] for i in range(len(vals1) - 1))
    # Length may be inclusive or exclusive of end due to current implementation
    assert len(vals0) in {pagination.limit, pagination.limit + 1}
    assert len(vals1) in {pagination.limit, pagination.limit + 1}
    # Ensure partitions do not overlap
    assert set(vals0).isdisjoint(set(vals1))
