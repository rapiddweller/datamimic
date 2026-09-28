# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.api import GenerateStatement
from datamimic_ce.engine.io.api import ChunkSourceWindow, DataSourcePagination
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.contexts.geniter_context import GenIterContext
from datamimic_ce.engine.runtime.tasks.sources.router import load_generate_source


class ChunkSourceReader:
    """Adapt a GenerateStatement source into stable per-page chunk rows."""

    def __init__(
        self,
        context: SetupContext | GenIterContext,
        stmt: GenerateStatement,
        chunk_start: int,
        chunk_end: int,
    ) -> None:
        self._context = context
        self._stmt = stmt
        self._chunk_start = chunk_start
        self._chunk_end = chunk_end
        root = context.root
        self._source_scripted = (
            stmt.source_script if stmt.source_script is not None else bool(root.default_source_scripted)
        )
        self._separator = stmt.separator or root.default_separator
        self._loads_all = stmt.distribution.loads_all or bool(stmt.unique)
        self._window: ChunkSourceWindow | None = None
        self._build_from_source = True

    def read_page(self, page_start: int, page_end: int) -> tuple[list[dict[str, object]], bool]:
        """Read a page directly or slice it from this chunk's stable source selection."""
        stmt = self._stmt
        if not self._loads_all:
            return load_generate_source(
                self._context,
                stmt,
                stmt.source,
                self._separator,
                self._source_scripted,
                page_start,
                page_end,
                DataSourcePagination(skip=page_start, limit=page_end - page_start),
            )

        if self._window is None:
            pool, self._build_from_source = load_generate_source(
                self._context, stmt, stmt.source, self._separator, self._source_scripted, None, None, None
            )
            seed = self._context.root.stable_distribution_seed(stmt.full_name)
            self._window = ChunkSourceWindow(
                pool,
                DataSourcePagination(skip=self._chunk_start, limit=self._chunk_end - self._chunk_start),
                unique=bool(stmt.unique),
                cyclic=stmt.cyclic,
                distribution=stmt.distribution,
                seed=seed,
                label=f"<generate> '{stmt.name}'",
            )

        return self._window.read_page(page_start, page_end), self._build_from_source
