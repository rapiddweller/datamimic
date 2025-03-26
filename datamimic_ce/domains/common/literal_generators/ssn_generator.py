# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.domains.common.literal_generators.data_faker_generator import DataFakerGenerator


class SSNGenerator(BaseLiteralGenerator):
    def __init__(self, locale: str | None = "en_US") -> None:
        self._gen = DataFakerGenerator(method="ssn", locale=locale)

    def generate(self) -> Any:
        return self._gen.generate()
