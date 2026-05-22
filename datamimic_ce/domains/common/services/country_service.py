# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from random import Random

from datamimic_ce.domains.common.generators.country_generator import CountryGenerator
from datamimic_ce.domains.common.models.country import Country
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field

COUNTRY_SCHEMA = EntitySchema(
    "Country",
    (
        field("iso_code", str, "ISO 3166-1 alpha-2 country code."),
        field("name", str, "Human-readable country name."),
        field("default_language_locale", str, "Default language locale."),
        field("phone_code", str, "International dialing code."),
        field("population", str, "Population count."),
    ),
)


class CountryService(BaseDomainService[Country]):
    """Service for managing country data.

    This class provides methods for creating, retrieving, and managing country data.
    """

    DATASET_PATTERNS = ("common/country_{CC}.csv",)

    def __init__(
        self,
        dataset: str | None = None,
        rng: Random | None = None,
    ):
        super().__init__(CountryGenerator(dataset=dataset, rng=rng), Country)

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return COUNTRY_SCHEMA.fields
