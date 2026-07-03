# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import TYPE_CHECKING

from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.data_sources.data_source_registry import DataSourceRegistry

if TYPE_CHECKING:
    from datamimic_ce.contexts.geniter_context import GenIterContext
    from datamimic_ce.contexts.setup_context import SetupContext
    from datamimic_ce.statements.generate_statement import GenerateStatement


class ChunkSourceReader:
    """Chunk-scoped source reader: hands each page its window of the statement's source.

    Owns the source knowledge that pagination needs — which distributions select from
    ALL rows (random/cumulated shuffle, unique dedupe) versus reading page windows
    directly (ordered) — so the worker only iterates pages.

    For loads_all distributions the full pool is loaded ONCE per chunk and cached:
    reloading per page costs one full query per page and, if the source mutates
    between pages, silently breaks the disjoint-window guarantee (same seed over
    different data).
    """

    def __init__(self, context: "SetupContext | GenIterContext", stmt: "GenerateStatement"):
        # Lazy import: tasks imports data_sources at module level (same pattern as
        # DataSourceRegistry's TaskUtil import).
        from datamimic_ce.tasks.task_util import TaskUtil

        self._context = context
        self._stmt = stmt
        root = context.root
        self._source_scripted = (
            stmt.source_script if stmt.source_script is not None else bool(root.default_source_scripted)
        )
        self._separator = stmt.separator or root.default_separator
        self._loads_all = (
            False if TaskUtil.is_source_ml_model(stmt) else (stmt.distribution.loads_all or bool(stmt.unique))
        )
        # Full pool for loads_all distributions, loaded on first page: (rows, build_from_source)
        self._pool: tuple[list, bool] | None = None

    def read_page(self, page_start: int, page_end: int) -> tuple[list, bool]:
        """Rows for the page window [page_start, page_end) plus the build_from_source flag.

        ORDERED pushes the window down to the loader (skip/limit query, file slice);
        random/cumulated/unique select the window from ONE stable global order of the
        cached pool — every page (and every worker) sees the same order, so the
        disjoint windows are complete and duplicate-free together.
        """
        from datamimic_ce.tasks.task_util import TaskUtil

        stmt = self._stmt
        pagination = DataSourcePagination(skip=page_start, limit=page_end - page_start)

        if not self._loads_all:
            return TaskUtil.gen_task_load_data_from_source_or_script(
                self._context,
                stmt,
                stmt.source,
                self._separator,
                self._source_scripted,
                page_start,
                page_end,
                pagination,
            )

        if self._pool is None:
            self._pool = TaskUtil.gen_task_load_data_from_source_or_script(
                self._context, stmt, stmt.source, self._separator, self._source_scripted, None, None, None
            )
        pool, build_from_source = self._pool

        # Stable per-statement seed -> identical global order on every page/worker.
        seed = self._context.root.stable_distribution_seed(stmt.full_name)
        if stmt.unique:
            rows = DataSourceRegistry.get_unique_data(pool, pagination, seed, f"<generate> '{stmt.name}'")
        else:
            rows = DataSourceRegistry.get_distributed_data(pool, pagination, stmt.cyclic, seed, stmt.distribution)
        return rows, build_from_source
