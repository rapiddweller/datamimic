# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from collections.abc import Iterator

from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.statements.reference_statement import ReferenceStatement
from datamimic_ce.tasks.task import Task


class ReferenceTask(Task):
    def __init__(self, statement: ReferenceStatement, pagination: DataSourcePagination | None = None):
        self._statement: ReferenceStatement = statement
        self._pagination: DataSourcePagination | None = pagination
        self._iterator: Iterator[str | int | float] | None = None

    @property
    def statement(self) -> ReferenceStatement:
        return self._statement

    def execute(self, ctx: Context | GenIterContext):
        """
        Generate data for element "reference" by retrieving values from an RDBMS data source.
        """
        if self._iterator is None:
            # Get RDBMS client
            client = ctx.root.clients.get(self.statement.source)
            if not isinstance(client, RdbmsClient):
                raise ValueError("Reference task currently only supports RDBMS data sources")

            # Load dataset from source
            dataset: list[str | int | float] = client.get_random_rows_by_column(
                self.statement.source_type, self.statement.source_key, self._pagination, self._statement.unique
            )

            if not dataset:
                raise ValueError(f"No data found for reference {self._statement.name}")

            # Initialize iterator based on uniqueness requirements
            if self._statement.unique:
                # For unique values, we need to sample without replacement
                sample_size = self._pagination.limit if self._pagination is not None else 1
                if sample_size > len(dataset):
                    raise RuntimeError(
                        f"Cannot generate {sample_size} unique values - only {len(dataset)} available for "
                        f"{self._statement.name}"
                    )
                sampled_data = random.sample(dataset, sample_size)
                self._iterator = iter(sampled_data)
            else:
                # For non-unique values, we can sample with replacement
                if self._pagination is not None:
                    sampled_data = [random.choice(dataset) for _ in range(self._pagination.limit)]
                    self._iterator = iter(sampled_data)
                else:
                    self._iterator = iter([random.choice(dataset)])

        # Get next value, reinitialize if exhausted
        try:
            if self._iterator is None:
                raise ValueError("Iterator was not properly initialized")
            value = next(self._iterator)

            # Add field "attribute" into current product if context supports it
            if hasattr(ctx, "add_current_product_field"):
                ctx.add_current_product_field(self._statement.name, value)

            return value
        except StopIteration:
            # Reset iterator and try again
            self._iterator = None
            return self.execute(ctx)
