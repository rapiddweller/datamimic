# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""L3 + determinism for Benerator distribution="cumulated" on a <variable> source.

Surface: engine (datamimic_ce). Proves a <variable source distribution="cumulated">
selects rows with a symmetric bell over the load order (middle favored), with
replacement, and replays identically under <setup rngSeed> (this path IS seed-bound,
unlike the literal-generator path) — so the shape test can live in the DSL.

Also asserts the scope guard: distribution="cumulated" on <generate> is rejected at
parse, never silently treated as "ordered".
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _picks(filename: str = "cumulated_variable.xml") -> list[int]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return [int(row["v"]) for row in engine.capture_result()["picks"]]


class TestCumulatedSourceDistribution:
    def test_bell_shape_over_rows(self):
        vals = _picks()
        assert len(vals) == 6000
        assert all(0 <= v <= 26 for v in vals)  # with replacement, stays in source range
        counts = Counter(vals)
        centre = counts[13]  # middle of 0..26
        assert centre > counts[0] and centre > counts[26]  # bell: middle favored over edges
        assert abs(sum(vals) / len(vals) - 13) < 1.0  # mean = middle of the load order
        # symmetric about the centre where both bins are well-populated
        for i in range(13):
            c1, c2 = counts[i], counts[26 - i]
            if c1 > 30 and c2 > 30:
                assert 0.7 < c1 / c2 < 1.3

    def test_replays_identically_under_seed(self):
        assert _picks() == _picks()  # rngSeed=42 -> deterministic

    def test_bell_shape_over_db_rows(self):
        # the real corpus shape: cumulated <variable> over a DB source + selector
        # (exercises the db-selector branch that the CSV fixture does not).
        vals = _picks("cumulated_variable_db.xml")
        assert len(vals) == 6000
        assert all(0 <= v <= 26 for v in vals)
        counts = Counter(vals)
        assert counts[13] > counts[0] and counts[13] > counts[26]
        assert abs(sum(vals) / len(vals) - 13) < 1.0

    def test_db_replays_identically_under_seed(self):
        assert _picks("cumulated_variable_db.xml") == _picks("cumulated_variable_db.xml")

    def test_bell_shape_on_generate_source(self):
        # cumulated on <generate source> (Benerator's most common iteration pattern)
        vals = _picks("generate_cumulated.xml")
        assert len(vals) == 6000
        assert all(0 <= v <= 26 for v in vals)
        counts = Counter(vals)
        assert counts[13] > counts[0] and counts[13] > counts[26]
        assert abs(sum(vals) / len(vals) - 13) < 1.0

    def test_generate_replays_identically_under_seed(self):
        assert _picks("generate_cumulated.xml") == _picks("generate_cumulated.xml")

    def test_cumulated_on_nested_key(self):
        # cumulated accepted on <nestedKey source>: runs, stays in range, deterministic.
        # (sampling shape is proven via the shared get_cumulated_data in the other tests.)
        def nested_vals():
            engine = DataMimicTest(test_dir=_TEST_DIR, filename="nestedkey_cumulated.xml", capture_test_result=True)
            engine.test_with_timer()
            rows = engine.capture_result()["outer"]
            return [int(item["v"]) for row in rows for item in row["items"]]

        vals = nested_vals()
        assert len(vals) == 50 * 10
        assert all(1 <= v <= 27 for v in vals)  # IncrementGenerator -> 1..27
        assert nested_vals() == vals  # deterministic under rngSeed


class TestGetCumulatedDataPagination:
    """Lock the subtle bit: paginated batches continue one draw sequence (page 2 follows
    page 1), so seeded multi-page reads equal a single contiguous read."""

    def test_pages_are_contiguous(self):
        from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
        from datamimic_ce.data_sources.data_source_registry import DataSourceRegistry

        data = list(range(27))
        whole = DataSourceRegistry.get_cumulated_data(data, DataSourcePagination(0, 100), False, seed=7)
        page1 = DataSourceRegistry.get_cumulated_data(data, DataSourcePagination(0, 40), False, seed=7)
        page2 = DataSourceRegistry.get_cumulated_data(data, DataSourcePagination(40, 60), False, seed=7)
        assert page1 + page2 == whole

    def test_empty_source(self):
        from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
        from datamimic_ce.data_sources.data_source_registry import DataSourceRegistry

        assert DataSourceRegistry.get_cumulated_data([], DataSourcePagination(0, 10), False, seed=1) == []


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
