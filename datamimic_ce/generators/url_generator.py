# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

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
