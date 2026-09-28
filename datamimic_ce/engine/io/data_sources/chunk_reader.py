# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.vocabulary.enums.distribution_enums import SourceDistribution
from datamimic_ce.engine.io.contracts import DataSourcePagination
from datamimic_ce.engine.io.data_sources.selection import get_distributed_data, get_unique_data


class ChunkSourceWindow:
    """Select and retain one chunk from a loaded source pool."""

    def __init__(
        self,
        pool: list[dict[str, object]],
        chunk: DataSourcePagination,
        *,
        unique: bool,
        cyclic: bool | None,
        distribution: SourceDistribution,
        seed: int,
        label: str,
    ) -> None:
        if unique:
            self._rows = get_unique_data(pool, chunk, seed, label)
        else:
            self._rows = get_distributed_data(pool, chunk, cyclic, seed, distribution)
        self._start = chunk.skip

    def read_page(self, start: int, end: int) -> list[dict[str, object]]:
        """Return the shallow page slice within this chunk."""
        return self._rows[start - self._start : end - self._start]
