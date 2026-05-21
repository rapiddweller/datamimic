# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce.domains.common.literal_generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator


class CNPJGenerator(BaseLiteralGenerator):
    """
    Generates Brazilian CNPJ numbers.
    """

    def __init__(self, rng: random.Random | None = None) -> None:
        super().__init__(rng=rng)
        self._gen = DataFakerGenerator(method="cnpj", locale="pt_BR", rng=rng)

    def generate(self) -> str:
        return self._gen.generate()
