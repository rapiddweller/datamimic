# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import itertools
from collections.abc import Iterator
from typing import Any

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
        """Generate a (composite) reference record from an RDBMS or MongoDB data source."""
        if self._iterator is None:
            if self._pagination is None and DataSourceRegistry.reference_uses_shared_cycle(self._statement):
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

    def _init_iterator(self, ctx: Context) -> Iterator[dict[str, Any]]:
        return iter(DataSourceRegistry.load_reference_source(ctx, self._statement, self._pagination))
