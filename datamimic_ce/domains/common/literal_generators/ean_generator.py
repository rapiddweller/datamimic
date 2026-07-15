# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from typing import Any

from datamimic_ce.domains.common.literal_generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator


class EANGenerator(BaseLiteralGenerator):
    """EAN-13 codes via faker.

    ``unique=True`` guarantees no repeated code across the generator's lifetime (legacy-DSL
    ``EANGenerator(unique)`` parity) - needed when the EAN is a primary key.
    """

    _UNIQUE_MAX_RETRIES = 100

    def __init__(self, locale: str | None = "en_US", unique: bool = False, rng: random.Random | None = None) -> None:
        super().__init__(rng=rng)
        self._gen = DataFakerGenerator(method="ean", locale=locale, rng=rng)
        self._unique = unique
        self._seen: set[Any] = set()

    def generate(self) -> Any:
        value = self._gen.generate()
        if not self._unique:
            return value
        # The EAN-13 space (~1e12) makes collisions vanishingly rare; a bounded retry loop is
        # enough and still fails loudly instead of hanging if the space were ever exhausted.
        for _ in range(self._UNIQUE_MAX_RETRIES):
            if value not in self._seen:
                self._seen.add(value)
                return value
            value = self._gen.generate()
        raise ValueError(f"EANGenerator(unique=True) found no fresh EAN after {self._UNIQUE_MAX_RETRIES} retries")
