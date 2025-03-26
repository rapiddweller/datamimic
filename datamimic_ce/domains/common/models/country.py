# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.common.generators.country_generator import CountryGenerator


class Country(BaseEntity):
    """
    Represents a country with various attributes.

    This class provides access to country data including ISO code, name, language,
    phone code, and population.
    """

    def __init__(self, country_generator: CountryGenerator):
        super().__init__()
        self._country_generator = country_generator

    @property
    @property_cache
    def iso_code(self) -> str:
        """Get the ISO code of the country.

        Returns:
            The ISO code of the country
        """
        return self.country_data["iso_code"]

    @property
    @property_cache
    def country_data(self) -> dict[str, Any]:
        """Get the country data.

        Returns:
            The country data
        """
        return self._country_generator.get_random_country()

    @property
    @property_cache
    def name(self) -> str:
        """Get the name of the country.

        Returns:
            The name of the country
        """
        return self.country_data["name"]

    @property
    @property_cache
    def default_language_locale(self) -> str:
        """Get the default language locale of the country.

        Returns:
            The default language locale of the country
        """
        return self.country_data["default_language_locale"]

    @property
    @property_cache
    def phone_code(self) -> str:
        """Get the phone code of the country.

        Returns:
            The phone code of the country
        """
        return self.country_data["phone_code"]

    @property
    @property_cache
    def population(self) -> str:
        """Get the population of the country.

        Returns:
            The population of the country
        """
        return self.country_data["population"]

    def to_dict(self) -> dict[str, Any]:
        """Convert the country to a dictionary.

        Returns:
            A dictionary representation of the country
        """
        return {
            "iso_code": self.iso_code,
            "name": self.name,
            "default_language_locale": self.default_language_locale,
            "phone_code": self.phone_code,
            "population": self.population,
        }
