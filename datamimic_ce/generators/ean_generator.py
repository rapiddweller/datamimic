# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from typing import Any

from datamimic_ce.generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.generators.generator import Generator


class EANGenerator(Generator):
    def __init__(self, locale: str | None = "en_US") -> None:
        self._gen = DataFakerGenerator(method="ean", locale=locale)

    def generate(self) -> Any:
        return self._gen.generate()
