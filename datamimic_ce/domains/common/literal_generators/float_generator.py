# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from decimal import Decimal

from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.enums.distribution_enums import NumberDistribution
from datamimic_ce.utils.distribution_sampling import cumulated_index


class FloatGenerator(BaseLiteralGenerator):
    def __init__(
        self,
        min: float = 0,
        max: float = 10,
        granularity: float = 0.1,
        distribution: NumberDistribution = NumberDistribution.UNIFORM,
        rng: random.Random | None = None,
    ) -> None:
        super().__init__(rng=rng)
        if min > max:
            raise ValueError(f"Failed when init FloatGenerator because min({min}) > max({max})")
        if not isinstance(distribution, NumberDistribution):
            raise TypeError(f"distribution must be a NumberDistribution, got {type(distribution).__name__}")

        self._min = min
        self._max = max
        self._granularity = granularity
        self._distribution = distribution

    def generate(self) -> float:
        granularity_decimal = Decimal(str(self._granularity))

        if self._distribution is NumberDistribution.CUMULATED:
            # Bell over the granularity grid. Span in Decimal so the top bin is reachable
            # (float (99.99-0.49)/0.10 = 994.999..., which would drop max).
            span = int((Decimal(str(self._max)) - Decimal(str(self._min))) / granularity_decimal)
            return float(Decimal(str(self._min)) + cumulated_index(self._rng, span) * granularity_decimal)

        # Generate a random floating-point number within the adjusted range
        random_float = self._rng.uniform(self._min, self._max)

        # change calculation numbers to Decimal to prevent floating point arithmetics error, e.g. 8.200000000000001
        random_decimal = Decimal(str(random_float))

        # Round the random float to the specified granularity
        rounded_random_decimal = round(random_decimal / granularity_decimal) * granularity_decimal

        return float(rounded_random_decimal)
