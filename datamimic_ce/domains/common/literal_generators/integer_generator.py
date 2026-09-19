# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from collections.abc import Iterator

from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.enums.distribution_enums import NumberDistribution
from datamimic_ce.utils.distribution_sampling import cumulated_index
from datamimic_ce.utils.number_sequences import build_number_sequence


class IntegerGenerator(BaseLiteralGenerator):
    def __init__(
        self,
        min: int = 0,
        max: int = 1000000,
        distribution: NumberDistribution = NumberDistribution.UNIFORM,
        rng: random.Random | None = None,
    ) -> None:
        super().__init__(rng=rng)
        if min > max:
            raise ValueError(f"Failed when init IntegerGenerator because min({min}) > max({max})")
        if not isinstance(distribution, NumberDistribution):
            raise TypeError(f"distribution must be a NumberDistribution, got {type(distribution).__name__}")
        self._min = min
        self._max = max
        self._distribution = distribution
        # Sequence-type members walk a stateful iterator; exhaustion propagates as
        # StopIteration (the engine ends the row loop, like a source running dry)
        self._sequence: Iterator[int | float] | None = None
        if distribution not in (NumberDistribution.UNIFORM, NumberDistribution.CUMULATED):
            self._sequence = build_number_sequence(distribution, min, max, 1, self._rng, integral=True)

    def generate(self) -> int:
        if self._sequence is not None:
            return int(next(self._sequence))
        if self._distribution is NumberDistribution.CUMULATED:
            return self._min + cumulated_index(self._rng, self._max - self._min)
        return self._rng.randint(self._min, self._max)
