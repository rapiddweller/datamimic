# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.domains.common.literal_generators.data_faker_generator import DataFakerGenerator


class UrlGenerator(BaseLiteralGenerator):
    """
    Generate a random url
    """

    def __init__(self, locale: str | None = None, schemes: list[str] | None = None):
        self._gen = DataFakerGenerator(locale=locale, method="url", schemes=schemes)

    def generate(self) -> str:
        url: str = self._gen.generate()
        return url
