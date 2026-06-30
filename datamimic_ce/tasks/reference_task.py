# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from collections.abc import Iterator
from typing import Any

from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.data_sources.data_source_registry import DataSourceRegistry
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
        """Generate a (composite) reference record from an RDBMS data source."""
        if self._iterator is None:
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

    def _init_iterator(self, ctx: Context) -> Iterator[dict[str, Any]]:
        client = ctx.root.clients.get(self.statement.source)
        if not isinstance(client, RdbmsClient):
            raise ValueError("Reference task currently only supports RDBMS data sources")
        rows = client.get_random_rows_by_columns(self.statement.source_type, self.statement.source_keys)
        if not rows:
            raise ValueError(f"No data found for reference {self._statement.name}")
        # Map each source row tuple to a {target: value} record.
        records = [dict(zip(self._statement.targets, row, strict=True)) for row in rows]
        return iter(self._select(records, ctx))

    def _select(self, records: list[dict[str, Any]], ctx: Context) -> list[dict[str, Any]]:
        """Distinct combinations route through the shared DataSourceRegistry.get_unique_data — the
        same SPOT as <variable>/<generate> unique (dedupe + shuffle + page window + strict). A
        non-unique reference picks with replacement (a foreign key may repeat the same row), which
        has no registry counterpart, so it stays here."""
        if self._statement.unique:
            # ponytail: distinctness holds within a page, not across pages — the per-page seed
            # advances, same pre-existing limitation as <variable source unique>. The default
            # pageSize (>= count up to 10k) keeps it single-page; cross-page paging is a separate fix.
            return DataSourceRegistry.get_unique_data(
                records, self._pagination, ctx.root.get_distribution_seed(), f"<reference> '{self._statement.name}'"
            )
        size = self._pagination.limit if self._pagination is not None else 1
        return [ctx.rng.choice(records) for _ in range(size)]
