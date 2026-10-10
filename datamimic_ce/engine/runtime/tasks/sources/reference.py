"""Runtime source operations for reference statements."""

from datamimic_ce.engine.dsl.api import (
    ReferenceStatement,
    SourceDistribution,
)
from datamimic_ce.engine.io.api import (
    DataSourcePagination,
    read_reference_rows,
    select_reference_rows,
)
from datamimic_ce.engine.runtime.contexts.context import Context


def reference_uses_shared_cycle(stmt: ReferenceStatement) -> bool:
    """Whether an unpaged reference needs root-owned rotation across rebuilt tasks."""
    if stmt.cyclic:
        return True
    return stmt.distribution is not None and SourceDistribution.coerce(stmt.distribution) is not (
        SourceDistribution.RANDOM
    )


def load_reference_source(
    context: Context,
    stmt: ReferenceStatement,
    pagination: DataSourcePagination | None,
) -> list[dict[str, object]]:
    """Load, map and select reference rows behind one typed datasource boundary."""
    client = context.root.clients.get(stmt.source)
    records = read_reference_rows(client, stmt.source, stmt.source_type, stmt.source_keys, stmt.targets, stmt.name)

    seed = context.root.stable_distribution_seed(stmt.full_name)
    distribution = SourceDistribution.coerce(stmt.distribution)
    random_rng = None
    if not stmt.unique and distribution is SourceDistribution.RANDOM and not stmt.cyclic:
        size = pagination.limit if pagination is not None else 1
        if size > 0:
            random_rng = context.rng
    default_cyclic_ordered = stmt.distribution is None and stmt.cyclic
    return select_reference_rows(
        records,
        pagination,
        stmt.cyclic,
        distribution,
        stmt.distribution is not None,
        stmt.unique,
        seed,
        f"<reference> '{stmt.name}'",
        random_rng,
        default_cyclic_ordered,
    )
