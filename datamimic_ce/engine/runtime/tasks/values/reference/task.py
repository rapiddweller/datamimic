# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import itertools
from collections.abc import Iterator

from datamimic_ce.engine.dsl.api import ReferenceStatement
from datamimic_ce.engine.io.api import DataSourcePagination
from datamimic_ce.engine.runtime.contexts.context import Context
from datamimic_ce.engine.runtime.contexts.geniter_context import GenIterContext
from datamimic_ce.engine.runtime.tasks.base.task import GenSubTask
from datamimic_ce.engine.runtime.tasks.sources.reference import load_reference_source, reference_uses_shared_cycle


class ReferenceTask(GenSubTask):
    def __init__(self, statement: ReferenceStatement, pagination: DataSourcePagination | None = None):
        self._statement: ReferenceStatement = statement
        self._pagination: DataSourcePagination | None = pagination
        # Each item is a {target: value} record (one source row's selected columns).
        self._iterator: Iterator[dict[str, object]] | None = None

    @property
    def statement(self) -> ReferenceStatement:
        return self._statement

    def execute(self, ctx: Context):
        """Generate a (composite) reference record from an RDBMS or MongoDB data source."""
        if self._iterator is None:
            if self._pagination is None and (
                self._statement.unique or reference_uses_shared_cycle(self._statement)
            ):
                # Unpaged tasks can be rebuilt per record inside control flow. Keep finite
                # unique cursors alive too; statement identity separates same-named branches.
                key = (
                    ("<reference>-unique", self._statement)
                    if self._statement.unique
                    else f"<reference>-cycle|{self._statement.full_name}"
                )
                shared = ctx.root.generators.get(key)
                if shared is None:
                    shared = self._init_iterator(ctx)
                    if not self._statement.unique:
                        shared = itertools.cycle(shared)
                    ctx.root.generators[key] = shared
                self._iterator = shared
            else:
                self._iterator = self._init_iterator(ctx)
        try:
            record = next(self._iterator)
        except StopIteration:
            if self._statement.unique:
                raise ValueError(
                    f"Cannot generate more unique values for <reference> '{self._statement.name}': source exhausted"
                ) from None
            self._iterator = None
            return self.execute(ctx)
        if isinstance(ctx, GenIterContext):
            for target, value in record.items():
                ctx.add_current_product_field(target, value)
        # Legacy single-field references return the scalar; composite ones return the record.
        return record[self._statement.targets[0]] if not self._statement.is_composite else record

    def _init_iterator(self, ctx: Context) -> Iterator[dict[str, object]]:
        return iter(load_reference_source(ctx, self._statement, self._pagination))
