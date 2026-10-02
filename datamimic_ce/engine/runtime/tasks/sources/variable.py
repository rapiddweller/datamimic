"""Plan variable source execution and retain runtime-owned policy."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import Enum
from random import Random

from datamimic_ce.engine.dsl.api import EL_VARIABLE, VariableStatement
from datamimic_ce.engine.dsl.vocabulary.source_capabilities import SourceFileFormat, source_file_format_for
from datamimic_ce.engine.io.api import (
    Client,
    DataSourcePagination,
    VariableSourceRequest,
    WeightedEntityDataSource,
    get_distributed_data,
    get_unique_data,
    is_database_client,
    read_variable_query,
    read_variable_source,
    select_row_iterator,
)
from datamimic_ce.engine.runtime.contexts.context import Context, SetupContext
from datamimic_ce.engine.runtime.scripting.evaluation import interpolate_variables
from datamimic_ce.engine.runtime.tasks.sources.length import data_source_cache_key


class VariableSourcePlanKind(str, Enum):
    FULL_LOAD = "full_load"
    ITERATION_SELECTOR = "iteration_selector"
    ITERATOR = "iterator"
    LAZY = "lazy"
    STORAGE = "storage"
    WEIGHTED = "weighted"


@dataclass(frozen=True)
class VariableSourcePlan:
    """Task-facing result of one planned variable source."""

    kind: VariableSourcePlanKind
    data: Iterable[object] | None = None
    client: Client | None = None
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
    """Shape a loaded pool and expose only an execution mode to the task."""
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
    """Plan variable source execution while keeping policy in Runtime."""
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
        if selector is None:
            raise RuntimeError("variable selector plan reached an impossible empty selector")
        prefix = stmt.variable_prefix or context.default_variable_prefix
        suffix = stmt.variable_suffix or context.default_variable_suffix
        client = context.get_client_by_id(source)
        if client is None or not is_database_client(client):
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
        full_pool = bool(loads_all or force_full_pool or stmt.is_global_variable)
        cached_length = None if full_pool else context.data_source_len.get(data_source_cache_key(stmt))
        data = read_variable_query(
            client,
            rendered_selector,
            pagination,
            full_pool=full_pool,
            cached_length=cached_length,
            cyclic=bool(stmt.cyclic),
        )
        return _variable_data_plan(context, stmt, data, pagination, force_full_pool=force_full_pool)

    request = VariableSourceRequest(
        source=source,
        descriptor_dir=context.root.descriptor_dir,
        separator=separator,
        source_entity=stmt.source_entity,
        source_type=stmt.type,
        name=stmt.name,
        materialize_full_pool=loads_all or force_full_pool,
        cyclic=bool(stmt.cyclic),
    )
    source_data: Iterable[object] | None
    if source_format is not None:
        source_data = read_variable_source(request, None, None, pagination)
        return _variable_data_plan(context, stmt, source_data, pagination, force_full_pool=force_full_pool)

    client = context.get_client_by_id(source)
    if client is not None:
        source_data = read_variable_source(request, client, None, pagination)
        return _variable_data_plan(context, stmt, source_data, pagination, force_full_pool=force_full_pool)

    if context.memstore_manager.contain(source):
        memstore = context.memstore_manager.get_memstore(source)
        source_data = read_variable_source(request, None, memstore, pagination)
        return _variable_data_plan(context, stmt, source_data, pagination, force_full_pool=force_full_pool)

    if force_full_pool:
        raise ValueError(
            f"<variable> '{stmt.name}': 'storage' is not supported for a "
            "dynamic/script-evaluated source (no stable pool to materialize up front)"
        )
    return VariableSourcePlan(kind=VariableSourcePlanKind.LAZY)


def load_variable_iteration_selector(
    context: Context,
    client: Client,
    selector: str,
    prefix: str,
    suffix: str,
) -> Iterable[object]:
    """Evaluate and execute one row-dependent variable selector."""
    return read_variable_query(
        client,
        interpolate_variables(context, selector, prefix, suffix),
        None,
        full_pool=True,
        cached_length=None,
        cyclic=False,
    )


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
    return select_row_iterator(data, pagination, bool(stmt.cyclic))


__all__ = [
    "VariableSourcePlan",
    "VariableSourcePlanKind",
    "load_variable_iteration_selector",
    "load_variable_lazy_source",
    "plan_variable_source",
]
