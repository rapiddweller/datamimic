# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from random import Random

from datamimic_ce.domains.common.generators.city_generator import CityGenerator
from datamimic_ce.domains.common.models.city import City
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field

CITY_SCHEMA = EntitySchema(
    "City",
    (
        field("name", str, "City name."),
        field("postal_code", str, "Postal or ZIP code."),
        field("area_code", str, "Telephone area code."),
        field("state", str, "State, province, or region."),
        field("language", str, "Primary language.", optional=True),
        field("population", int, "Population count.", optional=True),
        field("name_extension", str, "City name extension or suffix."),
        field("country", str, "Human-readable country name."),
        field("country_code", str, "ISO 3166-1 alpha-2 country code."),
    ),
)


class CityService(BaseDomainService[City]):
    """Service for managing city data.

    This class provides methods for creating, retrieving, and managing city data.
    """

    DATASET_PATTERNS = (
        "common/city/city_{CC}.csv",
        "common/country_{CC}.csv",
    )

    def __init__(
        self,
        dataset: str | None = None,
        rng: Random | None = None,
    ):
        super().__init__(CityGenerator(dataset=dataset, rng=rng), City)

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return CITY_SCHEMA.fields
