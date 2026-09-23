"""Plan and load variable sources."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import Enum
from random import Random

from datamimic_ce.engine.dsl.api import (
    EL_VARIABLE,
    SourceFileFormat,
    StatementUtil,
    VariableStatement,
    source_file_format_for,
)
from datamimic_ce.engine.io.api import (
    DatabaseClient,
    DataSourcePagination,
    DataSourceRegistry,
    FileUtil,
    WeightedEntityDataSource,
)
from datamimic_ce.engine.runtime.contexts.context import Context
from datamimic_ce.engine.runtime.contexts.setup_context import SetupContext
from datamimic_ce.engine.runtime.evaluation import interpolate_variables
from datamimic_ce.engine.runtime.sources.selection import get_distributed_data, get_unique_data

from .router import data_source_cache_key


class VariableSourcePlanKind(str, Enum):
    FULL_LOAD = "full_load"
    ITERATION_SELECTOR = "iteration_selector"
    ITERATOR = "iterator"
    LAZY = "lazy"
    STORAGE = "storage"
    WEIGHTED = "weighted"


@dataclass(frozen=True)
class VariableSourcePlan:
    """Task-facing result of one centrally routed variable source."""

    kind: VariableSourcePlanKind
    data: Iterable[object] | None = None
    client: DatabaseClient | None = None
    weighted_source: WeightedEntityDataSource | None = None
    selector: str | None = None
    prefix: str = ""
    suffix: str = ""


def _variable_data_plan(
    context: SetupContext,
    stmt: VariableStatement,
    data: Iterable[object] | None,
    pagination: DataSourcePagination | None,
    *,
    force_full_pool: bool,
) -> VariableSourcePlan:
    """Shape a routed variable pool and expose only an execution mode to the task."""
    if data is None:
        return VariableSourcePlan(
            kind=VariableSourcePlanKind.STORAGE if force_full_pool else VariableSourcePlanKind.ITERATOR
        )

    loads_all = stmt.distribution.loads_all or bool(stmt.unique)
    if not loads_all:
        return VariableSourcePlan(
            kind=VariableSourcePlanKind.STORAGE if force_full_pool else VariableSourcePlanKind.ITERATOR,
            data=data,
        )

    seed = context.root.stable_distribution_seed(stmt.full_name)
    selected = (
        get_unique_data(
            data,
            None if force_full_pool else pagination,
            seed,
            f"<variable> '{stmt.name}'",
        )
        if stmt.unique
        else get_distributed_data(
            data,
            None if force_full_pool else pagination,
            stmt.cyclic,
            seed,
            stmt.distribution,
        )
    )
    return VariableSourcePlan(
        kind=VariableSourcePlanKind.STORAGE if force_full_pool else VariableSourcePlanKind.FULL_LOAD,
        data=selected,
    )


def plan_variable_source(
    context: SetupContext,
    stmt: VariableStatement,
    pagination: DataSourcePagination | None,
    *,
    force_full_pool: bool,
) -> VariableSourcePlan:
    """Route and page a variable source without leaking source policy into its task."""
    source = stmt.source
    if source is None:
        raise ValueError(f"<variable> '{stmt.name}' has no source to plan")

    loads_all = stmt.distribution.loads_all or bool(stmt.unique)
    source_format = source_file_format_for(EL_VARIABLE, source)
    separator = stmt.separator or context.default_separator

    if source_format is SourceFileFormat.WEIGHTED_ENTITY_CSV:
        seeded = context.derive_seeded_rng()
        return VariableSourcePlan(
            kind=VariableSourcePlanKind.WEIGHTED,
            weighted_source=WeightedEntityDataSource(
                file_path=context.root.descriptor_dir / source,
                separator=separator,
                rng=seeded if seeded is not None else Random(),
                weight_column_name=stmt.weight_column,
            ),
        )

    if stmt.selector is not None or stmt.iteration_selector is not None:
        selector = stmt.selector or stmt.iteration_selector
        if selector is None:  # narrowed explicitly for static analysis
            raise RuntimeError("variable selector plan reached an impossible empty selector")
        prefix = stmt.variable_prefix or context.default_variable_prefix
        suffix = stmt.variable_suffix or context.default_variable_suffix
        client = context.get_client_by_id(source)
        if not isinstance(client, DatabaseClient):
            raise ValueError(f"<variable> '{stmt.name}': 'selector' only works with 'source' database (MongoDB, SQL)")
        if stmt.iteration_selector is not None:
            return VariableSourcePlan(
                kind=VariableSourcePlanKind.ITERATION_SELECTOR,
                client=client,
                selector=selector,
                prefix=prefix,
                suffix=suffix,
            )

        rendered_selector = interpolate_variables(context, selector, prefix, suffix)
        if loads_all or force_full_pool or stmt.is_global_variable:
            data = client.get_by_page_with_query(rendered_selector)
        else:
            length = context.data_source_len.get(data_source_cache_key(stmt))
            if length is None:
                length = client.count_query_length(rendered_selector)
            data = client.get_cyclic_data(rendered_selector, bool(stmt.cyclic), length, pagination)
        return _variable_data_plan(context, stmt, data, pagination, force_full_pool=force_full_pool)

    if source_format is not None:
        if source_format is SourceFileFormat.CSV:
            data = FileUtil.read_csv_to_dict_list(context.root.descriptor_dir / source, separator)
        elif source_format is SourceFileFormat.XLSX:
            data = FileUtil.read_xlsx_to_dict_list(context.root.descriptor_dir / source)
        elif source_format is SourceFileFormat.FIXED_WIDTH:
            data = FileUtil.read_fixed_width_to_dict_list(context.root.descriptor_dir / source)
        elif source_format is SourceFileFormat.JSON:
            data = FileUtil.read_json_to_list(context.root.descriptor_dir / source)
        else:
            raise ValueError(f"Unsupported <variable> source format: {source_format.value}")
        if not (loads_all or force_full_pool):
            data = DataSourceRegistry.get_cyclic_data_iterator(data, pagination, stmt.cyclic)
        return _variable_data_plan(context, stmt, data, pagination, force_full_pool=force_full_pool)

    client = context.get_client_by_id(source)
    if client is not None:
        if not isinstance(client, DatabaseClient):
            raise ValueError(f"Cannot get data from source '{source}' of <variable> '{stmt.name}'")
        product_type = StatementUtil.resolve_source_entity(stmt)
        if product_type is None:
            data = None
        elif loads_all or force_full_pool:
            data = client.get_by_page_with_type(product_type)
        elif stmt.cyclic:
            data = DataSourceRegistry.get_cyclic_data_list(
                client.get_by_page_with_type(product_type), pagination, cyclic=True
            )
        else:
            data = client.get_by_page_with_type(product_type, pagination)
        return _variable_data_plan(context, stmt, data, pagination, force_full_pool=force_full_pool)

    if context.memstore_manager.contain(source):
        product_type = StatementUtil.resolve_source_entity(stmt)
        memstore = context.memstore_manager.get_memstore(source)
        data = (
            memstore.get_all_data_by_type(product_type)
            if loads_all or force_full_pool
            else memstore.get_data_by_type(product_type, pagination, stmt.cyclic)
        )
        return _variable_data_plan(context, stmt, data, pagination, force_full_pool=force_full_pool)

    if force_full_pool:
        raise ValueError(
            f"<variable> '{stmt.name}': 'storage' is not supported for a "
            "dynamic/script-evaluated source (no stable pool to materialize up front)"
        )
    return VariableSourcePlan(kind=VariableSourcePlanKind.LAZY)


def load_variable_iteration_selector(
    context: Context,
    client: DatabaseClient,
    selector: str,
    prefix: str,
    suffix: str,
) -> Iterable[object]:
    """Evaluate and execute one row-dependent variable selector."""
    return client.get_by_page_with_query(interpolate_variables(context, selector, prefix, suffix))


def load_variable_lazy_source(
    context: Context,
    stmt: VariableStatement,
    pagination: DataSourcePagination | None,
) -> Iterator[object] | None:
    """Evaluate a dynamic variable source and apply its paging/distribution contract."""
    if stmt.source is None:
        return None
    data = context.evaluate_python_expression(stmt.source)
    if not isinstance(data, Iterable):
        raise TypeError(f"Variable source for '{stmt.name}' must be iterable")
    if stmt.distribution.loads_all or stmt.unique:
        seed = context.root.stable_distribution_seed(stmt.full_name)
        selected: Iterable[object] = (
            get_unique_data(data, pagination, seed, f"<variable> '{stmt.name}'")
            if stmt.unique
            else get_distributed_data(data, pagination, stmt.cyclic, seed, stmt.distribution)
        )
        return iter(selected)
    return DataSourceRegistry.get_cyclic_data_iterator(data, pagination, stmt.cyclic)
