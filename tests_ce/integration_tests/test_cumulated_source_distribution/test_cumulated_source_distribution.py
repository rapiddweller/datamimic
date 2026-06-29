# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Unit guards for the cumulated source-row sampler.

The DSL behaviour (cumulated × every source/consumer, bell shape, seed replay) lives in
``test_distribution_matrix/``. This file keeps only the two bits that matrix can't reach:
the paginated draw-sequence contiguity of ``get_cumulated_data`` and the ``coerce``
validation boundary.
"""

from __future__ import annotations

import pytest


class TestGetCumulatedDataPagination:
    """Lock the subtle bit: paginated batches continue one draw sequence (page 2 follows
    page 1), so seeded multi-page reads equal a single contiguous read."""

    def test_pages_are_contiguous(self):
        from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
        from datamimic_ce.data_sources.data_source_registry import DataSourceRegistry

        data = list(range(27))
        whole = DataSourceRegistry.get_cumulated_data(data, DataSourcePagination(0, 100), seed=7)
        page1 = DataSourceRegistry.get_cumulated_data(data, DataSourcePagination(0, 40), seed=7)
        page2 = DataSourceRegistry.get_cumulated_data(data, DataSourcePagination(40, 60), seed=7)
        assert page1 + page2 == whole

    def test_empty_source(self):
        from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
        from datamimic_ce.data_sources.data_source_registry import DataSourceRegistry

        assert DataSourceRegistry.get_cumulated_data([], DataSourcePagination(0, 10), seed=1) == []


class TestSourceDistributionCoerce:
    """coerce is the validation boundary for <variable> (no model validator there)."""

    def test_absent_is_random(self):
        from datamimic_ce.enums.distribution_enums import SourceDistribution

        assert SourceDistribution.coerce(None) is SourceDistribution.RANDOM
        assert SourceDistribution.coerce("cumulated") is SourceDistribution.CUMULATED

    def test_unknown_raises(self):
        from datamimic_ce.enums.distribution_enums import SourceDistribution

        with pytest.raises(ValueError):
            SourceDistribution.coerce("garbage")
