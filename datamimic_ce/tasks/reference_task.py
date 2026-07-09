# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import itertools
from collections.abc import Iterator
from typing import Any

from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.data_sources.data_source_registry import DataSourceRegistry
from datamimic_ce.enums.distribution_enums import SourceDistribution
from datamimic_ce.statements.reference_statement import ReferenceStatement
from datamimic_ce.tasks.task import GenSubTask


class ReferenceTask(GenSubTask):
    def __init__(self, statement: ReferenceStatement, pagination: DataSourcePagination | None = None):
        self._statement: ReferenceStatement = statement
        self._pagination: DataSourcePagination | None = pagination
        # Each item is a {target: value} record (one source row's selected columns).
        self._iterator: Iterator[dict[str, Any]] | None = None

    @property
    def statement(self) -> ReferenceStatement:
        return self._statement

    def execute(self, ctx: Context):
        """Generate a (composite) reference record from an RDBMS or MongoDB data source."""
        if self._iterator is None:
            if self._pagination is None and self._has_selection_modifier():
                # Without a page window the task may be rebuilt per record (nested in
                # <condition>/<while>), so the rotation lives in the root context — an endless
                # cycle over the selected order — instead of dying with the task instance.
                key = f"<reference>-cycle|{self._statement.full_name}"
                shared = ctx.root.generators.get(key)
                if shared is None:
                    shared = itertools.cycle(self._init_iterator(ctx))
                    ctx.root.generators[key] = shared
                self._iterator = shared
            else:
                self._iterator = self._init_iterator(ctx)
        try:
            record = next(self._iterator)
        except StopIteration:
            self._iterator = None
            return self.execute(ctx)
        if isinstance(ctx, GenIterContext):
            for target, value in record.items():
                ctx.add_current_product_field(target, value)
        # Legacy single-field references return the scalar; composite ones return the record.
        return record[self._statement.targets[0]] if not self._statement.is_composite else record

    def _has_selection_modifier(self) -> bool:
        """True when distribution/cyclic explicitly shape the selection (vs. the random default)."""
        stmt = self._statement
        if stmt.cyclic:
            return True
        return stmt.distribution is not None and SourceDistribution.coerce(stmt.distribution) is not (
            SourceDistribution.RANDOM
        )

    def _init_iterator(self, ctx: Context) -> Iterator[dict[str, Any]]:
        client = ctx.root.clients.get(self.statement.source)
        if not isinstance(client, RdbmsClient | MongoDBClient):
            raise ValueError(
                f"<reference> '{self._statement.name}': source '{self.statement.source}' is not a "
                "<database> or <mongodb> client (RDBMS and MongoDB are supported)"
            )
        rows = client.get_random_rows_by_columns(self.statement.source_type, self.statement.source_keys)
        if not rows:
            raise ValueError(f"No data found for reference {self._statement.name}")
        # Map each source row tuple to a {target: value} record.
        records = [dict(zip(self._statement.targets, row, strict=True)) for row in rows]
        return iter(self._select(records, ctx))

    def _select(self, records: list[dict[str, Any]], ctx: Context) -> list[dict[str, Any]]:
        """Distinct combinations route through the shared DataSourceRegistry.get_unique_data — the
        same SPOT as <variable>/<generate> unique (dedupe + shuffle + page window + strict). An
        explicit distribution/cyclic routes through the shared distribution dispatch. The default
        (no modifier) picks with replacement (a foreign key may repeat the same row), which has no
        registry counterpart, so it stays here."""
        stmt = self._statement
        if stmt.unique:
            # Stable per-statement seed so distinctness holds across pages, not just within one.
            seed = ctx.root.stable_distribution_seed(stmt.full_name)
            return DataSourceRegistry.get_unique_data(records, self._pagination, seed, f"<reference> '{stmt.name}'")
        distribution = SourceDistribution.coerce(stmt.distribution)
        if (stmt.distribution is not None and distribution is not SourceDistribution.RANDOM) or stmt.cyclic:
            seed = ctx.root.stable_distribution_seed(stmt.full_name)
            # Bare cyclic="true" means sequential wrap-around (legacy DSL semantics), i.e. ordered + cyclic.
            if distribution is SourceDistribution.ORDERED or (stmt.distribution is None and stmt.cyclic):
                return self._ordered(records)
            return DataSourceRegistry.get_distributed_data(records, self._pagination, stmt.cyclic, seed, distribution)
        # Default AND explicit distribution="random": pick with replacement (documented FK semantics).
        size = self._pagination.limit if self._pagination is not None else 1
        return [ctx.rng.choice(records) for _ in range(size)]

    def _ordered(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Rows in source order; cyclic wraps around, non-cyclic raises when the page outruns the
        pool (strict like unique — never silently under-generate)."""
        if self._pagination is None:
            # No page window (e.g. a reference nested in <if>/<while>): serve the full order; the
            # iterator wraps on reset, so rotation still advances instead of pinning to row 0.
            # Strictness needs a window, so the non-cyclic overrun check only runs when paginated.
            return records
        start = self._pagination.skip
        size = self._pagination.limit
        if self._statement.cyclic:
            return [records[(start + i) % len(records)] for i in range(size)]
        if start + size > len(records):
            raise ValueError(
                f"<reference> '{self._statement.name}' distribution='ordered' needs {start + size} rows "
                f'but the source has only {len(records)} (use cyclic="true" to wrap around)'
            )
        return records[start : start + size]
