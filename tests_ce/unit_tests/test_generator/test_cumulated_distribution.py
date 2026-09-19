# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""L3 shape test for the legacy 'cumulated' distribution on ranged numerics.

Surface: engine (datamimic_ce). Proves IntegerGenerator/FloatGenerator sample a
symmetric bell (mean=midpoint, edges reachable but rarer than centre) when
distribution='cumulated', matching the legacy cumulated number generators., so the shape contract is verified here in
Python rather than in a seeded DSL model. The DSL fixture proves L1 (parses+runs) only.
"""

import random
from decimal import Decimal

from datamimic_ce.domains.common.literal_generators.float_generator import FloatGenerator
from datamimic_ce.domains.common.literal_generators.integer_generator import IntegerGenerator
from datamimic_ce.enums.distribution_enums import NumberDistribution

N = 20000


def _histogram(samples, lo, hi):
    counts = [0] * (hi - lo + 1)
    for s in samples:
        counts[s - lo] += 1
    return counts


class TestCumulatedInteger:
    def test_mean_is_midpoint(self):
        gen = IntegerGenerator(min=0, max=50, distribution=NumberDistribution.CUMULATED, rng=random.Random(42))
        mean = sum(gen.generate() for _ in range(N)) / N
        assert abs(mean - 25) < 1.0  # legacy checkAverage(0, 50, 25)

    def test_symmetric_bell(self):
        lo, hi = 1, 27  # the dominant corpus case: number_of_items min=1 max=27
        gen = IntegerGenerator(min=lo, max=hi, distribution=NumberDistribution.CUMULATED, rng=random.Random(7))
        counts = _histogram((gen.generate() for _ in range(N)), lo, hi)
        # centre denser than edges
        centre = counts[len(counts) // 2]
        assert centre > counts[0] and centre > counts[-1]
        # symmetric: count[i] ~= count[mirror] where both are well-populated
        for i in range(len(counts) // 2):
            c1, c2 = counts[i], counts[-1 - i]
            if c1 > 50 and c2 > 50:
                assert 0.8 < c1 / c2 < 1.2

    def test_endpoints_reachable_narrow_range(self):
        # Mirrors the legacy suite's checkDistribution(0, 5): on a narrow range both edges hit.
        # (On a wide range edges are ~(1/span)^5 -> effectively unreachable, by design.)
        lo, hi = 0, 5
        gen = IntegerGenerator(min=lo, max=hi, distribution=NumberDistribution.CUMULATED, rng=random.Random(7))
        counts = _histogram((gen.generate() for _ in range(N)), lo, hi)
        assert counts[0] > 0 and counts[-1] > 0

    def test_within_bounds(self):
        gen = IntegerGenerator(min=5, max=9, distribution=NumberDistribution.CUMULATED, rng=random.Random(1))
        assert all(5 <= gen.generate() <= 9 for _ in range(N))


class TestCumulatedFloat:
    def test_mean_is_midpoint_and_on_grid(self):
        # the dominant corpus case: price min=0.49 max=99.99 granularity=0.10
        gen = FloatGenerator(
            min=0.49, max=99.99, granularity=0.10, distribution=NumberDistribution.CUMULATED, rng=random.Random(3)
        )
        vals = [gen.generate() for _ in range(N)]
        assert abs(sum(vals) / N - 50.24) < 1.0  # midpoint of [0.49, 99.99]
        # every value lands on the granularity grid and stays in range
        assert all(0.49 <= v <= 99.99 for v in vals)
        # every value sits exactly on the 0.10 grid offset from min (checked in Decimal,
        # since float (v-0.49)/0.10 carries representation error)
        grid = Decimal("0.10")
        assert all((Decimal(str(v)) - Decimal("0.49")) % grid == 0 for v in vals[:200])


class TestGuards:
    def test_raw_string_rejected(self):
        # distribution is always a real NumberDistribution; a bare string must NOT
        # silently fall through to uniform — it raises (no silent loss).
        for cls in (IntegerGenerator, FloatGenerator):
            try:
                cls(distribution="cumulated")
                assert False, f"{cls.__name__} accepted a raw string distribution"
            except TypeError:
                pass

    def test_default_is_uniform_unchanged(self):
        # no distribution -> byte-identical to the original uniform path
        a = IntegerGenerator(min=0, max=1000, rng=random.Random(99))
        b = IntegerGenerator(min=0, max=1000, rng=random.Random(99))
        assert [a.generate() for _ in range(100)] == [b.generate() for _ in range(100)]
        ref = random.Random(99)
        assert IntegerGenerator(min=0, max=1000, rng=random.Random(99)).generate() == ref.randint(0, 1000)
