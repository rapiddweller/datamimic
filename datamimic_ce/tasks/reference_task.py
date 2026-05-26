# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from collections.abc import Iterator
from random import Random

from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.statements.reference_statement import ReferenceStatement
from datamimic_ce.tasks.task import GenSubTask


class ReferenceTask(GenSubTask):
    def __init__(self, statement: ReferenceStatement, pagination: DataSourcePagination | None = None):
        self._statement: ReferenceStatement = statement
        self._pagination: DataSourcePagination | None = pagination
        self._iterator: Iterator[str | int | float] | None = None

    @property
    def statement(self) -> ReferenceStatement:
        return self._statement

    def execute(self, ctx: Context):
        """Generate a reference value from an RDBMS data source."""
        if self._iterator is None:
            self._iterator = self._init_iterator(ctx)
        try:
            value = next(self._iterator)
        except StopIteration:
            self._iterator = None
            return self.execute(ctx)
        if isinstance(ctx, GenIterContext):
            ctx.add_current_product_field(self._statement.name, value)
        return value

    def _init_iterator(self, ctx: Context) -> Iterator[str | int | float]:
        client = ctx.root.clients.get(self.statement.source)
        if not isinstance(client, RdbmsClient):
            raise ValueError("Reference task currently only supports RDBMS data sources")
        dataset: list[str | int | float] = client.get_random_rows_by_column(
            self.statement.source_type, self.statement.source_key, self._pagination, self._statement.unique
        )
        if not dataset:
            raise ValueError(f"No data found for reference {self._statement.name}")
        return iter(self._sample(dataset, ctx.rng))

    def _sample(self, dataset: list[str | int | float], rng: Random) -> list[str | int | float]:
        if self._statement.unique:
            sample_size = self._pagination.limit if self._pagination is not None else 1
            if sample_size > len(dataset):
                raise RuntimeError(
                    f"Cannot generate {sample_size} unique values - only {len(dataset)} available for "
                    f"{self._statement.name}"
                )
            return rng.sample(dataset, sample_size)
        if self._pagination is not None:
            return [rng.choice(dataset) for _ in range(self._pagination.limit)]
        return [rng.choice(dataset)]
