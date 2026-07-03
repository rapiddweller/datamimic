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

    For loads_all distributions the pool is loaded and ordered ONCE per chunk on the
    first page; pages then slice their window out of the chunk's order:

    * one full source query per chunk instead of one per page (a source mutating
      between pages would silently break the disjoint-window guarantee — same seed
      over different data),
    * one O(pool) shuffle/draw per chunk instead of one per page,
    * after ordering, only the chunk-sized order stays retained — the pool is
      released. The transient full load itself is inherent to selecting from ALL
      rows; a spill-to-disk/keyset scheme would be the next step if pools outgrow
      worker RAM.
    """

    def __init__(
        self,
        context: "SetupContext | GenIterContext",
        stmt: "GenerateStatement",
        chunk_start: int,
        chunk_end: int,
    ):
        # Lazy import: tasks imports data_sources at module level (same pattern as
        # DataSourceRegistry's TaskUtil import).
        from datamimic_ce.tasks.task_util import TaskUtil

        self._context = context
        self._stmt = stmt
        self._chunk_start = chunk_start
        self._chunk_end = chunk_end
        root = context.root
        self._source_scripted = (
            stmt.source_script if stmt.source_script is not None else bool(root.default_source_scripted)
        )
        self._separator = stmt.separator or root.default_separator
        self._loads_all = (
            False if TaskUtil.is_source_ml_model(stmt) else (stmt.distribution.loads_all or bool(stmt.unique))
        )
        # Chunk-wide selection for loads_all distributions, ordered on first page.
        self._chunk_order: list | None = None
        self._build_from_source = True

    def read_page(self, page_start: int, page_end: int) -> tuple[list, bool]:
        """Rows for the page window [page_start, page_end) plus the build_from_source flag.

        ORDERED pushes the window down to the loader (skip/limit query, file slice);
        random/cumulated/unique slice the window out of ONE stable chunk order —
        every chunk selects from the same seeded global sequence, so the disjoint
        windows are complete and duplicate-free together (across pages AND workers).
        """
        from datamimic_ce.tasks.task_util import TaskUtil

        stmt = self._stmt

        if not self._loads_all:
            return TaskUtil.gen_task_load_data_from_source_or_script(
                self._context,
                stmt,
                stmt.source,
                self._separator,
                self._source_scripted,
                page_start,
                page_end,
                DataSourcePagination(skip=page_start, limit=page_end - page_start),
            )

        if self._chunk_order is None:
            pool, self._build_from_source = TaskUtil.gen_task_load_data_from_source_or_script(
                self._context, stmt, stmt.source, self._separator, self._source_scripted, None, None, None
            )
            # Stable per-statement seed -> identical global sequence in every chunk/worker;
            # each chunk keeps only its own window of it.
            seed = self._context.root.stable_distribution_seed(stmt.full_name)
            chunk_pagination = DataSourcePagination(
                skip=self._chunk_start, limit=self._chunk_end - self._chunk_start
            )
            if stmt.unique:
                self._chunk_order = DataSourceRegistry.get_unique_data(
                    pool, chunk_pagination, seed, f"<generate> '{stmt.name}'"
                )
            else:
                self._chunk_order = DataSourceRegistry.get_distributed_data(
                    pool, chunk_pagination, stmt.cyclic, seed, stmt.distribution
                )
            # pool goes out of scope here — retained memory is chunk-sized

        return (
            self._chunk_order[page_start - self._chunk_start : page_end - self._chunk_start],
            self._build_from_source,
        )
