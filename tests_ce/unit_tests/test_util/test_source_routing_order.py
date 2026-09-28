"""Event-order contracts at the source-routing boundary."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from datamimic_ce.engine.dsl.statements.values.variables.variable_statement import VariableStatement
from datamimic_ce.engine.dsl.vocabulary.enums.distribution_enums import SourceDistribution
from datamimic_ce.engine.io.contracts import DataSourcePagination
from datamimic_ce.engine.io.data_sources import chunk_reader
from datamimic_ce.engine.io.data_sources import variable as io_variable_sources
from datamimic_ce.engine.io.exporters.core import routing as io_exporter_routing
from datamimic_ce.engine.io.data_sources.data_source_registry import DataSourceRegistry
from datamimic_ce.engine.runtime.tasks.sources import chunk_source_reader
from datamimic_ce.engine.runtime.tasks.sources import router as source_router
from datamimic_ce.engine.runtime.tasks.sources import variable as variable_sources
from datamimic_ce.engine.runtime.tasks.sources.chunk_source_reader import ChunkSourceReader


def _variable_statement(source: str, *, full_name: str, source_entity: str = "rows") -> VariableStatement:
    statement = object.__new__(VariableStatement)
    statement._full_name = full_name
    statement._name = full_name
    statement._source = source
    statement._source_entity = source_entity
    statement._type = None
    statement._separator = None
    return statement


def test_length_cache_keeps_same_named_sources_separate() -> None:
    root = Mock()
    root.data_source_len = {}
    root.descriptor_dir = Path("/descriptor")
    root.default_separator = "|"
    first, second = Mock(), Mock()
    first.get_data_len_by_type.return_value = 2
    second.get_data_len_by_type.return_value = 5
    root.memstore_manager.contain.side_effect = lambda source: source in {"first", "second"}
    root.memstore_manager.get_memstore.side_effect = {"first": first, "second": second}.get
    root.get_client_by_id.return_value = None
    context = SimpleNamespace(root=root)

    source_router.set_data_source_length(context, _variable_statement("first", full_name="consumer"))
    source_router.set_data_source_length(context, _variable_statement("second", full_name="consumer"))

    assert root.data_source_len == {("consumer", "first"): 2, ("consumer", "second"): 5}
    first.get_data_len_by_type.assert_called_once_with("rows")
    second.get_data_len_by_type.assert_called_once_with("rows")


def test_variable_selector_is_eager_but_iteration_selector_is_row_deferred(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = object()
    context = SimpleNamespace(
        default_separator="|",
        default_variable_prefix="{{",
        default_variable_suffix="}}",
        get_client_by_id=Mock(return_value=client),
        data_source_len={("variable", None): 1},
        root=Mock(),
    )
    pagination = DataSourcePagination(skip=0, limit=1)
    interpolate = Mock(return_value="SELECT rendered")
    query = Mock(return_value=[{"id": 1}])
    monkeypatch.setattr(variable_sources, "is_database_client", lambda _: True)
    monkeypatch.setattr(variable_sources, "interpolate_variables", interpolate)
    monkeypatch.setattr(io_variable_sources, "database_get_by_page_with_query", query)

    selector = SimpleNamespace(
        source="db",
        selector="SELECT {{setup_value}}",
        iteration_selector=None,
        separator=None,
        variable_prefix=None,
        variable_suffix=None,
        distribution=SourceDistribution.ORDERED,
        unique=False,
        cyclic=False,
        is_global_variable=False,
        full_name="variable",
    )
    plan = variable_sources.plan_variable_source(context, selector, pagination, force_full_pool=False)

    assert plan.kind is variable_sources.VariableSourcePlanKind.ITERATOR
    interpolate.assert_called_once_with(context, "SELECT {{setup_value}}", "{{", "}}")
    query.assert_called_once_with(client, "SELECT rendered", pagination)

    interpolate.reset_mock()
    query.reset_mock()
    iteration = SimpleNamespace(**{**selector.__dict__, "selector": None, "iteration_selector": "SELECT {{row_id}}"})
    plan = variable_sources.plan_variable_source(context, iteration, pagination, force_full_pool=False)

    assert plan.kind is variable_sources.VariableSourcePlanKind.ITERATION_SELECTOR
    interpolate.assert_not_called()
    query.assert_not_called()

    row_context = object()
    rows = variable_sources.load_variable_iteration_selector(
        row_context, client, plan.selector, plan.prefix, plan.suffix
    )
    assert list(rows) == [{"id": 1}]
    interpolate.assert_called_once_with(row_context, "SELECT {{row_id}}", "{{", "}}")
    query.assert_called_once_with(client, "SELECT rendered")


def test_invalid_variable_selector_rejects_before_interpolation_or_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    interpolate = Mock()
    query = Mock()
    context = SimpleNamespace(
        default_separator="|",
        default_variable_prefix="{{",
        default_variable_suffix="}}",
        get_client_by_id=Mock(return_value=object()),
    )
    statement = SimpleNamespace(
        source="not-a-client",
        selector="SELECT {{value}}",
        iteration_selector=None,
        separator=None,
        variable_prefix=None,
        variable_suffix=None,
        distribution=SourceDistribution.ORDERED,
        unique=False,
        cyclic=False,
        is_global_variable=False,
        full_name="variable",
        name="variable",
    )
    monkeypatch.setattr(variable_sources, "is_database_client", lambda _: False)
    monkeypatch.setattr(variable_sources, "interpolate_variables", interpolate)
    monkeypatch.setattr(io_variable_sources, "database_get_by_page_with_query", query)

    with pytest.raises(ValueError, match="selector.*source.*database"):
        variable_sources.plan_variable_source(
            context, statement, DataSourcePagination(skip=0, limit=1), force_full_pool=False
        )

    interpolate.assert_not_called()
    query.assert_not_called()


def test_variable_source_keeps_empty_and_materialized_pools_distinct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = object()
    context = SimpleNamespace(
        default_separator="|",
        get_client_by_id=Mock(return_value=client),
        data_source_len={},
        root=SimpleNamespace(descriptor_dir=Path("/descriptor"), stable_distribution_seed=Mock(return_value=7)),
    )
    statement = SimpleNamespace(
        source="db",
        selector=None,
        iteration_selector=None,
        separator=None,
        distribution=SourceDistribution.ORDERED,
        unique=False,
        cyclic=False,
        source_entity="rows",
        type=None,
        name="variable",
        full_name="variable",
        is_global_variable=False,
    )
    monkeypatch.setattr(io_variable_sources, "is_database_client", lambda _: True)
    read = Mock(return_value=[])
    monkeypatch.setattr(io_variable_sources, "database_get_by_page_with_type", read)
    empty = variable_sources.plan_variable_source(
        context, statement, DataSourcePagination(skip=0, limit=2), force_full_pool=False
    )
    assert empty.kind is variable_sources.VariableSourcePlanKind.ITERATOR
    assert empty.data == []
    read.assert_called_once()
    assert read.call_args.args[:2] == (client, "rows")
    assert (read.call_args.args[2].skip, read.call_args.args[2].limit) == (0, 2)

    read.reset_mock()
    materialized = variable_sources.plan_variable_source(
        context, statement, DataSourcePagination(skip=4, limit=2), force_full_pool=True
    )
    assert materialized.kind is variable_sources.VariableSourcePlanKind.STORAGE
    assert materialized.data == []
    read.assert_called_once_with(client, "rows")


def test_variable_cyclic_source_reads_pool_once_and_selects_wrapped_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = object()
    pagination = DataSourcePagination(skip=2, limit=3)
    context = SimpleNamespace(
        default_separator="|",
        get_client_by_id=Mock(return_value=client),
        data_source_len={},
        root=SimpleNamespace(descriptor_dir=Path("/descriptor"), stable_distribution_seed=Mock(return_value=7)),
    )
    statement = SimpleNamespace(
        source="db",
        selector=None,
        iteration_selector=None,
        separator=None,
        distribution=SourceDistribution.ORDERED,
        unique=False,
        cyclic=True,
        source_entity="rows",
        type=None,
        name="variable",
        full_name="variable",
        is_global_variable=False,
    )
    rows = [{"id": 0}, {"id": 1}, {"id": 2}]
    read = Mock(return_value=rows)
    monkeypatch.setattr(io_variable_sources, "is_database_client", lambda _: True)
    monkeypatch.setattr(io_variable_sources, "database_get_by_page_with_type", read)

    plan = variable_sources.plan_variable_source(context, statement, pagination, force_full_pool=False)

    assert list(plan.data or []) == [{"id": 2}, {"id": 0}, {"id": 1}]
    read.assert_called_once_with(client, "rows")


def test_generate_csv_reads_one_chunk_then_templates_against_root(monkeypatch: pytest.MonkeyPatch) -> None:
    root = SimpleNamespace(
        descriptor_dir=Path("/descriptor"), default_variable_prefix="<<", default_variable_suffix=">>"
    )
    context = SimpleNamespace(root=root)
    statement = SimpleNamespace(
        variable_prefix=None,
        variable_suffix=None,
        cyclic=False,
        offset=3,
        full_name="products",
    )
    load_csv = Mock(return_value=[{"code": "<<value>>"}])
    template = Mock(return_value=[{"code": "expanded"}])
    monkeypatch.setattr(DataSourceRegistry, "load_csv_file", load_csv)
    monkeypatch.setattr(source_router, "evaluate_source_template", template)

    rows, build_from_source = source_router.load_generate_source(
        context,
        statement,
        "rows.csv",
        "|",
        True,
        5,
        10,
        DataSourcePagination(skip=5, limit=5),
    )

    assert rows == [{"code": "expanded"}]
    assert build_from_source is True
    load_csv.assert_called_once_with(
        file_path=Path("/descriptor/rows.csv"),
        separator="|",
        cyclic=False,
        start_idx=5,
        end_idx=10,
        offset=3,
    )
    template.assert_called_once_with(root, [{"code": "<<value>>"}], "<<", ">>")


def test_nested_key_requires_a_string_source_expression_before_reading(monkeypatch: pytest.MonkeyPatch) -> None:
    context = SimpleNamespace(evaluate_python_expression=Mock(return_value=7), root=SimpleNamespace())
    statement = SimpleNamespace(source="{source_id}", name="items", type="list")
    source_format = Mock()
    monkeypatch.setattr(source_router, "source_file_format_for", source_format)

    with pytest.raises(ValueError, match="Source expression of <nestedKey> 'items' must evaluate to a string"):
        source_router.load_nested_key_source(context, statement)

    context.evaluate_python_expression.assert_called_once_with("source_id")
    source_format.assert_not_called()


@pytest.mark.parametrize(
    "source",
    ["items.csv", "items.json"],
)
def test_nested_key_file_sources_bypass_memstore(monkeypatch: pytest.MonkeyPatch, source: str) -> None:
    root = SimpleNamespace(descriptor_dir=Path("/descriptor"), default_separator="|", memstore_manager=Mock())
    root.memstore_manager.contain.side_effect = AssertionError("file sources must bypass memstore")
    context = SimpleNamespace(root=root)
    statement = SimpleNamespace(
        source=source,
        type="list",
        source_entity="items",
        name="items",
        separator=None,
        cyclic=False,
    )
    read = Mock(return_value=[])
    monkeypatch.setattr(source_router, "read_nested_key_source", read)

    assert source_router.load_nested_key_source(context, statement) == []
    read.assert_called_once()


def test_nested_key_dict_with_unknown_source_never_inspects_memstore() -> None:
    root = SimpleNamespace(descriptor_dir=Path("/descriptor"), default_separator="|", memstore_manager=Mock())
    root.memstore_manager.contain.side_effect = AssertionError("dict sources must bypass memstore")
    context = SimpleNamespace(root=root)
    statement = SimpleNamespace(
        source="items.unknown",
        type="dict",
        source_entity="items",
        name="items",
        separator=None,
        cyclic=False,
    )

    with pytest.raises(ValueError, match="dict.*does not support format"):
        source_router.load_nested_key_source(context, statement)


def test_nested_key_templates_before_distribution_seed_and_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    timeline = Mock()
    root = SimpleNamespace(
        default_source_scripted=False,
        default_variable_prefix="{{",
        default_variable_suffix="}}",
        get_distribution_seed=timeline.seed,
    )
    context = SimpleNamespace(root=root)
    statement = SimpleNamespace(
        source_script=True,
        variable_prefix=None,
        variable_suffix=None,
        name="items",
        cyclic=False,
        distribution=SourceDistribution.RANDOM,
    )
    rows = [{"v": "{{value}}"}]
    templated = [{"v": "expanded"}]
    selected = [{"v": "selected"}]
    timeline.template.return_value = templated
    timeline.distribute.return_value = selected
    monkeypatch.setattr(source_router, "evaluate_source_template", timeline.template)
    monkeypatch.setattr(source_router, "get_distributed_data", timeline.distribute)

    assert source_router.finalize_nested_key_source(context, statement, rows) == selected
    assert timeline.mock_calls == [
        call.template(context, rows, "{{", "}}"),
        call.seed(),
        call.distribute(templated, None, False, timeline.seed.return_value, SourceDistribution.RANDOM),
    ]


def test_chunk_random_source_loads_once_per_chunk_with_one_stable_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    root = SimpleNamespace(
        default_source_scripted=False,
        default_separator="|",
        stable_distribution_seed=Mock(return_value=17),
    )
    context = SimpleNamespace(root=root)
    statement = SimpleNamespace(
        source="rows.csv",
        source_script=None,
        separator=None,
        distribution=SourceDistribution.RANDOM,
        unique=False,
        full_name="products",
        name="products",
        cyclic=False,
    )
    load = Mock(return_value=([{"id": index} for index in range(8)], True))
    distribute = Mock(return_value=[{"id": index} for index in range(10, 14)])
    monkeypatch.setattr(chunk_source_reader, "load_generate_source", load)
    monkeypatch.setattr(chunk_reader, "get_distributed_data", distribute)

    reader = ChunkSourceReader(context, statement, chunk_start=10, chunk_end=14)
    assert reader.read_page(10, 12) == ([{"id": 10}, {"id": 11}], True)
    assert reader.read_page(12, 14) == ([{"id": 12}, {"id": 13}], True)

    load.assert_called_once_with(context, statement, "rows.csv", "|", False, None, None, None)
    root.stable_distribution_seed.assert_called_once_with("products")
    distribute.assert_called_once()

    ChunkSourceReader(context, statement, chunk_start=14, chunk_end=16).read_page(14, 16)
    assert load.call_count == 2
    assert root.stable_distribution_seed.call_count == 2


def test_chunk_ordered_source_reads_each_page_without_stable_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    root = SimpleNamespace(
        default_source_scripted=False,
        default_separator="|",
        stable_distribution_seed=Mock(),
    )
    context = SimpleNamespace(root=root)
    statement = SimpleNamespace(
        source="rows.csv",
        source_script=None,
        separator=None,
        distribution=SourceDistribution.ORDERED,
        unique=False,
        full_name="products",
        name="products",
        cyclic=False,
    )
    load = Mock(side_effect=[([{"id": 0}], True), ([{"id": 1}], True)])
    monkeypatch.setattr(chunk_source_reader, "load_generate_source", load)

    reader = ChunkSourceReader(context, statement, chunk_start=0, chunk_end=2)
    assert reader.read_page(0, 1) == ([{"id": 0}], True)
    assert reader.read_page(1, 2) == ([{"id": 1}], True)

    assert [call.args[5:7] for call in load.call_args_list] == [(0, 1), (1, 2)]
    root.stable_distribution_seed.assert_not_called()


def test_chunk_cumulated_source_loads_once_and_slices_the_chunk_window(monkeypatch: pytest.MonkeyPatch) -> None:
    root = SimpleNamespace(
        default_source_scripted=False,
        default_separator="|",
        stable_distribution_seed=Mock(return_value=23),
    )
    context = SimpleNamespace(root=root)
    statement = SimpleNamespace(
        source="rows.csv",
        source_script=None,
        separator=None,
        distribution=SourceDistribution.CUMULATED,
        unique=False,
        full_name="products",
        name="products",
        cyclic=True,
    )
    pool = [{"id": index} for index in range(5)]
    selected = [{"id": index} for index in range(4)]
    load = Mock(return_value=(pool, True))
    distribute = Mock(return_value=selected)
    monkeypatch.setattr(chunk_source_reader, "load_generate_source", load)
    monkeypatch.setattr(chunk_reader, "get_distributed_data", distribute)

    reader = ChunkSourceReader(context, statement, chunk_start=6, chunk_end=10)
    assert reader.read_page(6, 8) == (selected[:2], True)
    assert reader.read_page(8, 10) == (selected[2:], True)

    load.assert_called_once_with(context, statement, "rows.csv", "|", False, None, None, None)
    root.stable_distribution_seed.assert_called_once_with("products")
    distribute.assert_called_once()
    selected_pool, pagination, cyclic, seed, distribution = distribute.call_args.args
    assert selected_pool is pool
    assert (pagination.skip, pagination.limit) == (6, 4)
    assert (cyclic, seed, distribution) == (True, 23, SourceDistribution.CUMULATED)


def test_chunk_unique_selection_overrides_distribution_and_retains_build_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = SimpleNamespace(
        default_source_scripted=False,
        default_separator="|",
        stable_distribution_seed=Mock(return_value=5),
    )
    context = SimpleNamespace(root=root)
    statement = SimpleNamespace(
        source="rows.csv",
        source_script=None,
        separator=None,
        distribution=SourceDistribution.RANDOM,
        unique=True,
        full_name="products",
        name="products",
        cyclic=False,
    )
    pool = [{"id": index} for index in range(4)]
    load = Mock(return_value=(pool, False))
    distribute = Mock()
    monkeypatch.setattr(chunk_source_reader, "load_generate_source", load)
    monkeypatch.setattr(chunk_reader, "get_distributed_data", distribute)

    reader = ChunkSourceReader(context, statement, chunk_start=1, chunk_end=3)
    first = reader.read_page(1, 2)
    second = reader.read_page(2, 3)

    assert first == ([{"id": 1}], False)
    assert second == ([{"id": 3}], False)
    load.assert_called_once()
    root.stable_distribution_seed.assert_called_once_with("products")
    distribute.assert_not_called()


def test_chunk_unique_selection_fails_when_distinct_pool_is_too_small(monkeypatch: pytest.MonkeyPatch) -> None:
    root = SimpleNamespace(
        default_source_scripted=False,
        default_separator="|",
        stable_distribution_seed=Mock(return_value=5),
    )
    context = SimpleNamespace(root=root)
    statement = SimpleNamespace(
        source="rows.csv",
        source_script=None,
        separator=None,
        distribution=SourceDistribution.RANDOM,
        unique=True,
        full_name="products",
        name="products",
        cyclic=False,
    )
    monkeypatch.setattr(chunk_source_reader, "load_generate_source", Mock(return_value=([{"id": 1}], True)))

    reader = ChunkSourceReader(context, statement, chunk_start=0, chunk_end=2)
    with pytest.raises(ValueError, match="Cannot generate 2 unique values.*only 1 distinct available"):
        reader.read_page(0, 2)


def test_generate_prefers_memstore_while_variable_prefers_client_for_same_source_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_id = "shared"
    memstore = Mock()
    memstore.get_data_by_type.return_value = [{"id": "memstore"}]
    client = object()
    root = SimpleNamespace(
        descriptor_dir=Path("/descriptor"),
        default_variable_prefix="{{",
        default_variable_suffix="}}",
        memstore_manager=Mock(),
        clients={source_id: client},
        get_client_by_id=Mock(return_value=client),
    )
    root.memstore_manager.contain.return_value = True
    root.memstore_manager.get_memstore.return_value = memstore
    generate_context = SimpleNamespace(root=root)
    generate = SimpleNamespace(
        variable_prefix=None,
        variable_suffix=None,
        cyclic=False,
        offset=0,
        full_name="products",
        name="products",
        source_entity="rows",
        type=None,
        selector=None,
        targets=set(),
    )

    rows, _ = source_router.load_generate_source(
        generate_context, generate, source_id, "|", False, 0, 1, DataSourcePagination(skip=0, limit=1)
    )
    assert rows == [{"id": "memstore"}]
    memstore.get_data_by_type.assert_called_once()
    product_type, pagination, cyclic = memstore.get_data_by_type.call_args.args
    assert (product_type, pagination.skip, pagination.limit, cyclic) == ("rows", 0, 1, False)

    database_rows = Mock(return_value=[{"id": "client"}])
    monkeypatch.setattr(variable_sources, "is_database_client", lambda value: value is client)
    monkeypatch.setattr(io_variable_sources, "is_database_client", lambda value: value is client)
    monkeypatch.setattr(io_variable_sources, "database_get_by_page_with_type", database_rows)
    variable_context = SimpleNamespace(
        default_separator="|",
        get_client_by_id=root.get_client_by_id,
        memstore_manager=root.memstore_manager,
        root=root,
    )
    variable = SimpleNamespace(
        source=source_id,
        selector=None,
        iteration_selector=None,
        separator=None,
        distribution=SourceDistribution.ORDERED,
        unique=False,
        cyclic=False,
        source_entity="rows",
        type=None,
        name="variable",
    )

    plan = variable_sources.plan_variable_source(
        variable_context, variable, DataSourcePagination(skip=0, limit=1), force_full_pool=False
    )
    assert plan.kind is variable_sources.VariableSourcePlanKind.ITERATOR
    assert list(plan.data or []) == [{"id": "client"}]
    database_rows.assert_called_once()
    queried_client, product_type, pagination = database_rows.call_args.args
    assert (queried_client, product_type, pagination.skip, pagination.limit) == (client, "rows", 0, 1)
    root.memstore_manager.get_memstore.assert_called_once()


@pytest.mark.parametrize(
    ("targets", "expected"),
    [({"mongo.upsert"}, [{}]), ({"mongo.delete"}, [])],
)
def test_empty_mongodb_generate_source_only_falls_back_for_upsert(
    monkeypatch: pytest.MonkeyPatch, targets: set[str], expected: list[dict]
) -> None:
    mongo = object()
    root = SimpleNamespace(
        descriptor_dir=Path("/descriptor"),
        default_variable_prefix="{{",
        default_variable_suffix="}}",
        memstore_manager=Mock(),
        clients={"mongo": mongo},
        get_client_by_id=Mock(return_value=mongo),
    )
    root.memstore_manager.contain.return_value = False
    statement = SimpleNamespace(
        variable_prefix=None,
        variable_suffix=None,
        cyclic=False,
        offset=0,
        full_name="products",
        name="products",
        source_entity=None,
        type=None,
        selector="{}",
        targets=targets,
    )
    query = Mock(return_value=[])
    monkeypatch.setattr(source_router, "is_mongodb_client", lambda value: value is mongo)
    monkeypatch.setattr(io_exporter_routing, "is_mongodb_client", lambda value: value is mongo)
    monkeypatch.setattr(source_router, "interpolate_variables", Mock(return_value="{}"))
    monkeypatch.setattr(source_router, "database_get_by_page_with_query", query)

    rows, build_from_source = source_router.load_generate_source(
        SimpleNamespace(root=root), statement, "mongo", "|", False, 0, 1, DataSourcePagination(skip=0, limit=1)
    )

    assert rows == expected
    assert build_from_source is True
    query.assert_called_once()
    queried_client, selector, pagination = query.call_args.args
    assert (queried_client, selector, pagination.skip, pagination.limit) == (mongo, "{}", 0, 1)
