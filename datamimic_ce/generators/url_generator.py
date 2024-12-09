# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/


from datamimic_ce.generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.generators.generator import Generator


class UrlGeneratorModel:
    def __init__(self, locale: str | None = None, schemes: list[str] | None = None):
        self._gen = DataFakerGenerator(locale=locale, method="url", schemes=schemes)


class UrlGenerator(Generator, UrlGeneratorModel):
    """
    Generate a random url
    """

    def generate(self) -> str:
        url: str = self._gen.generate()
        return url
