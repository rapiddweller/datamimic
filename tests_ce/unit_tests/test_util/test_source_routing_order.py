"""Event-order contracts at the source-routing boundary."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from datamimic_ce.engine.dsl.statements.values.variables.variable_statement import VariableStatement
from datamimic_ce.engine.dsl.vocabulary.enums.distribution_enums import SourceDistribution
from datamimic_ce.engine.dsl.vocabulary.source_capabilities import SourceFileFormat
from datamimic_ce.engine.io.contracts import DataSourcePagination
from datamimic_ce.engine.io.data_sources import chunk_reader
from datamimic_ce.engine.io.data_sources import router as io_source_router
from datamimic_ce.engine.io.data_sources import variable as io_variable_sources
from datamimic_ce.engine.io.data_sources.boundary.models import GenerateFileSource, GenerateFileSourceRequest
from datamimic_ce.engine.io.data_sources.data_source_registry import DataSourceRegistry
from datamimic_ce.engine.io.data_sources.router import (
    read_generate_file_source,
    select_reference_rows,
    window_nested_key_rows,
)
from datamimic_ce.engine.io.exporters.core import routing as io_exporter_routing
from datamimic_ce.engine.runtime.tasks.sources import chunk_source_reader
from datamimic_ce.engine.runtime.tasks.sources import generate as generate_source_router
from datamimic_ce.engine.runtime.tasks.sources import length as length_source_router
from datamimic_ce.engine.runtime.tasks.sources import nested as nested_source_router
from datamimic_ce.engine.runtime.tasks.sources import variable as variable_sources
from datamimic_ce.engine.runtime.tasks.sources.chunk_source_reader import ChunkSourceReader


def test_nested_key_window_preserves_order_and_noncyclic_bounds() -> None:
    rows = [{"id": 1}, {"id": 2}]

    assert window_nested_key_rows(rows, 2, False) == rows
    assert window_nested_key_rows(rows, 0, False) == []
    selected = window_nested_key_rows(rows, 5, False)
    assert selected == rows
    assert selected[0] is rows[0]


def test_nested_key_cyclic_window_wraps_with_independent_deep_copies() -> None:
    rows = [{"id": 1, "nested": {"value": "original"}}, {"id": 2, "nested": {"value": "second"}}]

    selected = window_nested_key_rows(rows, 3, True)

    assert [row["id"] for row in selected] == [1, 2, 1]
    assert selected[0] is not rows[0]
    assert selected[2] is not selected[0]
    selected[2]["nested"]["value"] = "changed"
    assert selected[0]["nested"]["value"] == "original"
    assert rows[0]["nested"]["value"] == "original"


def test_random_reference_requires_rng_only_for_positive_windows() -> None:
    rows = [{"id": 1}]
    pagination = DataSourcePagination(skip=0, limit=1)

    with pytest.raises(TypeError, match="Random source is required"):
        select_reference_rows(
            rows,
            pagination,
            False,
            SourceDistribution.RANDOM,
            False,
            False,
            1,
            "<reference> 'items'",
            None,
            False,
        )

    assert select_reference_rows(
        rows,
        DataSourcePagination(skip=0, limit=0),
        False,
        SourceDistribution.RANDOM,
        False,
        False,
        1,
        "<reference> 'items'",
        None,
        False,
    ) == []


def test_ordered_reference_rejects_window_past_source() -> None:
    with pytest.raises(ValueError, match="distribution='ordered' needs 3 rows"):
        select_reference_rows(
            [{"id": 1}, {"id": 2}],
            DataSourcePagination(skip=0, limit=3),
            False,
            SourceDistribution.ORDERED,
            True,
            False,
            1,
            "<reference> 'items'",
            None,
            False,
        )


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

    length_source_router.set_data_source_length(context, _variable_statement("first", full_name="consumer"))
    length_source_router.set_data_source_length(context, _variable_statement("second", full_name="consumer"))

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
        name="products",
        type=None,
        source_entity=None,
    )
    load_csv = Mock(return_value=[{"code": "<<value>>"}])
    template = Mock(return_value=[{"code": "expanded"}])
    monkeypatch.setattr(DataSourceRegistry, "load_csv_file", load_csv)
    monkeypatch.setattr(generate_source_router, "evaluate_source_template", template)

    rows, build_from_source = generate_source_router.load_generate_source(
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


def test_generate_file_io_preserves_weighted_suffix_fallbacks(tmp_path: Path) -> None:
    headered_weight = tmp_path / "values.wgt.csv"
    headered_weight.write_text("value|weight\ntrue|80\nfalse|20\n", encoding="utf-8")
    weighted_entity = tmp_path / "entities.wgt.ent.csv"
    weighted_entity.write_text("id,name,weight\n1,Cheap,80\n2,Expensive,20\n", encoding="utf-8")
    headerless_weight = tmp_path / "headerless.wgt.csv"
    headerless_weight.write_text("true|80\nfalse|20\n", encoding="utf-8")

    weighted_rows = read_generate_file_source(
        GenerateFileSourceRequest(headered_weight.name, tmp_path, "values", "|", False, None, None, 0, None)
    )
    entity_rows = read_generate_file_source(
        GenerateFileSourceRequest(weighted_entity.name, tmp_path, "entities", ",", False, None, None, 0, None)
    )

    assert weighted_rows is not None
    assert weighted_rows.rows == [{"value": "true", "weight": "80"}, {"value": "false", "weight": "20"}]
    assert entity_rows is not None
    assert entity_rows.rows == [
        {"id": "1", "name": "Cheap", "weight": "80"},
        {"id": "2", "name": "Expensive", "weight": "20"},
    ]
    with pytest.raises(ValueError, match="headerless weighted"):
        read_generate_file_source(
            GenerateFileSourceRequest(headerless_weight.name, tmp_path, "headerless", "|", False, None, None, 0, None)
        )


def test_generate_dbunit_file_uses_name_fallback_and_offset(tmp_path: Path) -> None:
    descriptor = tmp_path / "rows.dbunit.xml"
    descriptor.write_text("<dataset><rows id='1'/><rows id='2'/><rows id='3'/></dataset>", encoding="utf-8")

    result = read_generate_file_source(
        GenerateFileSourceRequest(descriptor.name, tmp_path, "rows", "|", False, None, None, 1, None)
    )

    assert result is not None
    assert result.rows == [{"id": "2"}, {"id": "3"}]


def test_generate_file_reader_declines_memstore_and_client_ids(tmp_path: Path) -> None:
    for source in ("memstore", "client"):
        assert (
            read_generate_file_source(
                GenerateFileSourceRequest(source, tmp_path, "rows", "|", False, None, None, 0, None)
            )
            is None
        )


def test_generate_file_source_precedes_memstore(monkeypatch: pytest.MonkeyPatch) -> None:
    root = SimpleNamespace(
        descriptor_dir=Path("/descriptor"),
        default_variable_prefix="{{",
        default_variable_suffix="}}",
        memstore_manager=Mock(),
        clients={},
    )
    file_source = Mock(return_value=GenerateFileSource(SourceFileFormat.JSON, [{"id": 1}]))
    monkeypatch.setattr(generate_source_router, "read_generate_file_source", file_source)

    rows, build_from_source = generate_source_router.load_generate_source(
        SimpleNamespace(root=root),
        _generate_source_statement(),
        "rows.json",
        "|",
        False,
        None,
        None,
        None,
    )

    assert rows == [{"id": 1}]
    assert build_from_source is True
    root.memstore_manager.contain.assert_not_called()


def test_generate_json_template_failure_keeps_loaded_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    root = SimpleNamespace(
        descriptor_dir=Path("/descriptor"), default_variable_prefix="{{", default_variable_suffix="}}"
    )
    context = SimpleNamespace(root=root)
    statement = SimpleNamespace(
        variable_prefix=None,
        variable_suffix=None,
        full_name="products",
        name="products",
        type=None,
        source_entity=None,
        cyclic=False,
        offset=0,
    )
    rows = [{"name": "{{ missing }}"}]
    monkeypatch.setattr(
        generate_source_router,
        "read_generate_file_source",
        Mock(return_value=GenerateFileSource(SourceFileFormat.JSON, rows)),
    )
    template = Mock(side_effect=[[{"name": "Ada"}], ValueError("missing template value")])
    monkeypatch.setattr(generate_source_router, "evaluate_source_template", template)

    result, build_from_source = generate_source_router.load_generate_source(
        context, statement, "rows.json", "|", True, None, None, None
    )
    failed_result, failed_build = generate_source_router.load_generate_source(
        context, statement, "rows.json", "|", True, None, None, None
    )

    assert result == [{"name": "Ada"}]
    assert build_from_source is True
    assert failed_result == rows
    assert failed_build is True
    assert template.call_args_list == [call(root, rows, "{{", "}}"), call(root, rows, "{{", "}}")]


def test_generate_xml_template_evaluates_against_context(monkeypatch: pytest.MonkeyPatch) -> None:
    root = SimpleNamespace(
        descriptor_dir=Path("/descriptor"), default_variable_prefix="{{", default_variable_suffix="}}"
    )
    context = SimpleNamespace(root=root)
    statement = SimpleNamespace(
        variable_prefix=None,
        variable_suffix=None,
        full_name="products",
        name="products",
        type=None,
        source_entity=None,
        cyclic=False,
        offset=0,
    )
    rows = [{"name": "{{ product_name }}"}]
    monkeypatch.setattr(
        generate_source_router,
        "read_generate_file_source",
        Mock(return_value=GenerateFileSource(SourceFileFormat.XML, rows)),
    )
    template = Mock(return_value={"name": "Example"})
    monkeypatch.setattr(generate_source_router, "evaluate_source_template", template)

    result, build_from_source = generate_source_router.load_generate_source(
        context, statement, "rows.xml", "|", True, None, None, None
    )

    assert result == [{"name": "Example"}]
    assert build_from_source is True
    template.assert_called_once_with(context, rows, "{{", "}}")


def test_nested_key_requires_a_string_source_expression_before_reading(monkeypatch: pytest.MonkeyPatch) -> None:
    context = SimpleNamespace(evaluate_python_expression=Mock(return_value=7), root=SimpleNamespace())
    statement = SimpleNamespace(source="{source_id}", name="items", type="list")
    source_format = Mock()
    monkeypatch.setattr(nested_source_router, "source_file_format_for", source_format)

    with pytest.raises(ValueError, match="Source expression of <nestedKey> 'items' must evaluate to a string"):
        nested_source_router.load_nested_key_source(context, statement)

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
    monkeypatch.setattr(nested_source_router, "read_nested_key_source", read)

    assert nested_source_router.load_nested_key_source(context, statement) == []
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
        nested_source_router.load_nested_key_source(context, statement)


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
    monkeypatch.setattr(nested_source_router, "evaluate_source_template", timeline.template)
    monkeypatch.setattr(nested_source_router, "get_distributed_data", timeline.distribute)

    assert nested_source_router.finalize_nested_key_source(context, statement, rows) == selected
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

    class RawMemstore:
        def get_data_by_type(self, product_type: str) -> list[dict[str, str]]:
            assert product_type == "rows"
            return [{"id": "memstore"}]

    memstore = RawMemstore()
    io_memstore_read = Mock(return_value=[{"id": "memstore"}])
    monkeypatch.setattr(
        generate_source_router,
        "read_generate_memstore_source",
        io_memstore_read,
        raising=False,
    )
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

    pagination = DataSourcePagination(skip=0, limit=1)
    rows, _ = generate_source_router.load_generate_source(
        generate_context, generate, source_id, "|", False, 0, 1, pagination
    )
    assert rows == [{"id": "memstore"}]
    io_memstore_read.assert_called_once_with(memstore, "rows", pagination, False)

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
    query = Mock(return_value=[])
    monkeypatch.setattr(io_source_router, "is_mongodb_client", lambda value: value is mongo)
    monkeypatch.setattr(io_source_router, "database_get_by_page_with_query", query)

    rows = io_source_router.read_generate_database_source(
        mongo, "{}", "products", None, DataSourcePagination(skip=0, limit=1), "mongo.upsert" in targets
    )

    assert rows == expected
    query.assert_called_once()
    queried_client, selector, pagination = query.call_args.args
    assert (queried_client, selector, pagination.skip, pagination.limit) == (mongo, "{}", 0, 1)


@pytest.mark.parametrize(
    ("is_mongo", "selector", "entity", "collection", "expected_query", "expected_entity"),
    [
        (False, "select * from rows", "rows", None, "select * from rows", None),
        (False, None, "rows", None, None, "rows"),
        (True, "{}", "rows", "rows", "{}", None),
        (True, None, "rows", "rows", None, "rows"),
    ],
)
def test_generate_database_io_uses_resolved_selector_or_entity_and_page(
    monkeypatch: pytest.MonkeyPatch,
    is_mongo: bool,
    selector: str | None,
    entity: str,
    collection: str | None,
    expected_query: str | None,
    expected_entity: str | None,
) -> None:
    client = object()
    query = Mock(return_value=[{"id": 1}])
    entity_read = Mock(return_value=[{"id": 1}])
    monkeypatch.setattr(io_source_router, "is_mongodb_client", lambda _: is_mongo)
    monkeypatch.setattr(io_source_router, "is_rdbms_client", lambda _: not is_mongo)
    monkeypatch.setattr(io_source_router, "database_get_by_page_with_query", query)
    monkeypatch.setattr(io_source_router, "database_get_by_page_with_type", entity_read)
    pagination = DataSourcePagination(skip=3, limit=2)

    rows = io_source_router.read_generate_database_source(
        client, selector, entity, collection, pagination, False
    )

    assert rows == [{"id": 1}]
    if expected_query is not None:
        query.assert_called_once_with(client, expected_query, pagination)
        entity_read.assert_not_called()
    else:
        query.assert_not_called()
        entity_read.assert_called_once_with(client, expected_entity, pagination)


def _generate_source_statement(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "variable_prefix": None,
        "variable_suffix": None,
        "cyclic": False,
        "offset": 0,
        "full_name": "products",
        "name": "products",
        "source_entity": None,
        "type": None,
        "selector": None,
        "targets": set(),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _generate_source_context(source: str, client: object | None, memstore: Mock | None = None) -> SimpleNamespace:
    manager = Mock()
    manager.contain.return_value = memstore is not None
    manager.get_memstore.return_value = memstore
    root = SimpleNamespace(
        descriptor_dir=Path("/descriptor"),
        default_variable_prefix="{{",
        default_variable_suffix="}}",
        memstore_manager=manager,
        clients={source: client} if client is not None else {},
    )
    return SimpleNamespace(root=root)


def test_generate_mongodb_requires_selector_or_collection_before_reading(monkeypatch: pytest.MonkeyPatch) -> None:
    client = object()
    query = Mock()
    collection_read = Mock()
    monkeypatch.setattr(io_source_router, "is_mongodb_client", lambda value: value is client)
    monkeypatch.setattr(io_source_router, "database_get_by_page_with_query", query)
    monkeypatch.setattr(io_source_router, "database_get_by_page_with_type", collection_read)

    with pytest.raises(ValueError, match="MongoDB source requires"):
        io_source_router.read_generate_database_source(
            client, None, "products", None, DataSourcePagination(skip=0, limit=1), False
        )

    query.assert_not_called()
    collection_read.assert_not_called()


def test_generate_database_io_rejects_unsupported_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(io_source_router, "is_mongodb_client", lambda _: False)
    monkeypatch.setattr(io_source_router, "is_rdbms_client", lambda _: False)

    with pytest.raises(ValueError, match="Cannot load data from client: object"):
        io_source_router.read_generate_database_source(object(), None, "rows", None, None, False)


@pytest.mark.parametrize(("target", "has_upsert_target"), [("mongo.upsert", True), ("mongo.delete", False)])
def test_generate_passes_mongodb_upsert_target_to_io(
    monkeypatch: pytest.MonkeyPatch, target: str, has_upsert_target: bool
) -> None:
    client = object()
    context = _generate_source_context("mongo", client)
    statement = _generate_source_statement(source_entity="rows", targets={target})
    database_read = Mock(return_value=[])
    monkeypatch.setattr(generate_source_router, "read_generate_database_source", database_read)
    monkeypatch.setattr(io_exporter_routing, "is_mongodb_client", lambda value: value is client)

    rows, _ = generate_source_router.load_generate_source(
        context, statement, "mongo", "|", False, None, None, DataSourcePagination(skip=0, limit=1)
    )

    assert rows == []
    assert database_read.call_args.args[-1] is has_upsert_target


@pytest.mark.parametrize("source_kind", ["memstore", "rdbms", "mongodb"])
def test_generate_unsupported_offset_fails_before_source_read(
    monkeypatch: pytest.MonkeyPatch, source_kind: str
) -> None:
    source = "source"
    client = object() if source_kind != "memstore" else None
    memstore = Mock() if source_kind == "memstore" else None
    context = _generate_source_context(source, client, memstore)
    database_read = Mock()
    monkeypatch.setattr(generate_source_router, "read_generate_database_source", database_read)

    with pytest.raises(ValueError, match="offset= is only supported"):
        generate_source_router.load_generate_source(
            context,
            _generate_source_statement(offset=1, selector="{}", source_entity="rows"),
            source,
            "|",
            False,
            None,
            None,
            DataSourcePagination(skip=0, limit=1),
        )

    database_read.assert_not_called()
    if memstore is not None:
        memstore.get_data_by_type.assert_not_called()


def test_chunk_source_reader_delegates_database_page_to_generate_source(monkeypatch: pytest.MonkeyPatch) -> None:
    client = object()
    context = _generate_source_context("db", client)
    context.root.default_source_scripted = False
    context.root.default_separator = "|"
    statement = _generate_source_statement(
        source="db", distribution=SourceDistribution.ORDERED, source_script=None, separator=None, unique=False
    )
    query = Mock(return_value=[{"id": 7}])
    monkeypatch.setattr(generate_source_router, "read_generate_database_source", query)
    statement.selector = "select 7"

    rows, build_from_source = ChunkSourceReader(context, statement, 0, 4).read_page(2, 4)

    assert rows == [{"id": 7}]
    assert build_from_source is True
    actual = query.call_args.args
    assert actual[:4] == (client, "select 7", "products", None)
    assert (actual[4].skip, actual[4].limit) == (2, 2)
    assert actual[5:] == (False,)
