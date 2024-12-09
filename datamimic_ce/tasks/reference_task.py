# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

import random

from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.statements.reference_statement import ReferenceStatement
from datamimic_ce.tasks.task import Task


class ReferenceTask(Task):
    def __init__(self, statement: ReferenceStatement, pagination: DataSourcePagination):
        self._statement = statement
        self._pagination = pagination
        self._iterator = None

    @property
    def statement(self) -> ReferenceStatement:
        return self._statement

    def execute(self, ctx: GenIterContext):
        """
        Generate data for element "reference"
        :param ctx:
        :return:
        """
        # TODO: apply distribution when retrieve foreign key
        # Init iterator on first execution
        if self._iterator is None:
            client = ctx.root.clients[self.statement.source]
            if not isinstance(client, RdbmsClient):
                raise ValueError("<reference> currently support only data source RDBMS")
            # Load dataset from source
            dataset = client.get_random_rows_by_column(
                self.statement.source_type,
                self.statement.source_key,
                self._pagination,
                self._statement.unique,
            )
            # Handle unique key
            if self._statement.unique:
                # Raise error when number of records is greater than number of keys
                if self._pagination.limit > len(dataset):
                    raise RuntimeError(f"Length of result is greater than referenced key: {self._statement.name}")
                else:
                    self._iterator = iter(random.sample(dataset, self._pagination.limit))
            # Handle no unique key
            else:
                dataset = [random.choice(dataset) for _ in range(self._pagination.limit)]
                self._iterator = iter(dataset)
        value = next(self._iterator)

        # Add field "attribute" into current product
        ctx.add_current_product_field(self._statement.name, value)
