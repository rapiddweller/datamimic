# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

import random
from decimal import Decimal


class FloatGenerator:
    def __init__(self, min: float = 0, max: float = 10, granularity: float = 0.1) -> None:
        if min > max:
            raise ValueError(f"Failed when init FloatGenerator because min({min}) > max({max})")

        self._min = min
        self._max = max
        self._granularity = granularity

    def generate(self) -> float:
        # Generate a random floating-point number within the adjusted range
        random_float = random.uniform(self._min, self._max)

        # change calculation numbers to Decimal to prevent floating point arithmetics error, e.g. 8.200000000000001
        random_decimal = Decimal(str(random_float))
        granularity_decimal = Decimal(str(self._granularity))

        # Round the random float to the specified granularity
        rounded_random_decimal = round(random_decimal / granularity_decimal) * granularity_decimal

        return float(rounded_random_decimal)
