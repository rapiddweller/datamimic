# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator


class IntegerGenerator(BaseLiteralGenerator):
    def __init__(self, min: int = 0, max: int = 1000000, rng: random.Random | None = None) -> None:
        if min > max:
            raise ValueError(f"Failed when init IntegerGenerator because min({min}) > max({max})")
        self._min = min
        self._max = max
        self._rng: random.Random = rng or random.Random()

    def generate(self) -> int:
        return self._rng.randint(self._min, self._max)
