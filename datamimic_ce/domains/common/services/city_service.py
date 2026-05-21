# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce.domains.common.generators.city_generator import CityGenerator
from datamimic_ce.domains.common.models.city import City
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import AttributeSpec, specs


class CityService(BaseDomainService[City]):
    """Service for managing city data.

    This class provides methods for creating, retrieving, and managing city data.
    """

    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
    ):
        super().__init__(CityGenerator(dataset=dataset, rng=rng), City)

    @classmethod
    def attribute_specs(cls) -> tuple[AttributeSpec, ...]:
        return specs(
            ("name", "str", "City name."),
            ("postal_code", "str", "Postal or ZIP code."),
            ("area_code", "str", "Telephone area code."),
            ("state", "str", "State, province, or region."),
            ("language", "str | None", "Primary language."),
            ("population", "int | None", "Population count."),
            ("name_extension", "str", "City name extension or suffix."),
            ("country", "str", "Human-readable country name."),
            ("country_code", "str", "ISO 3166-1 alpha-2 country code."),
        )

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        patterns = [
            "common/city/city_{CC}.csv",
            "common/country_{CC}.csv",
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
