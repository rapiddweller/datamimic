# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import random

from datamimic_ce.domains.common.generators.country_generator import CountryGenerator
from datamimic_ce.domains.common.models.country import Country
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import AttributeSpec, specs


class CountryService(BaseDomainService[Country]):
    """Service for managing country data.

    This class provides methods for creating, retrieving, and managing country data.
    """

    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
    ):
        super().__init__(CountryGenerator(dataset=dataset, rng=rng), Country)

    @classmethod
    def attribute_specs(cls) -> tuple[AttributeSpec, ...]:
        return specs(
            ("iso_code", "str", "ISO 3166-1 alpha-2 country code."),
            ("name", "str", "Human-readable country name."),
            ("default_language_locale", "str", "Default language locale."),
            ("phone_code", "str", "International dialing code."),
            ("population", "str", "Population count."),
        )

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        return compute_supported_datasets(["common/country_{CC}.csv"], start=Path(__file__))
