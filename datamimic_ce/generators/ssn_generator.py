# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from datamimic_ce.generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.generators.generator import Generator


class SSNGenerator(Generator):
    def __init__(self, locale: str | None = "en_US") -> None:
        self._gen = DataFakerGenerator(method="ssn", locale=locale)

    def generate(self) -> Any:
        return self._gen.generate()
