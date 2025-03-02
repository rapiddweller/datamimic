# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import uuid

from datamimic_ce.domains.common.generators.country_generator import CountryGenerator
from datamimic_ce.domains.common.models.country import Country


class CountryService:
    """Service for managing country data.

    This class provides methods for creating, retrieving, and managing country data.
    """

    def __init__(self):
        """Initialize the CountryService."""
        self._countries: dict[str, Country] = {}
        self._generator: CountryGenerator = CountryGenerator()

    def create_country(self) -> Country:
        """Create a new country.

        Returns:
            A new Country object.
        """
        # Generate a new country
        country = self._generator.generate()

        # Store the country with a unique ID
        country_id = f"country-{uuid.uuid4()}"
        self._countries[country_id] = country

        return country

    def create_countries_batch(self, count: int = 10) -> list[Country]:
        """Create a batch of countries.

        Args:
            count: The number of countries to create.

        Returns:
            A list of Country objects.
        """
        # Generate a batch of countries
        countries = self._generator.generate_batch(count)

        # Store the countries with unique IDs
        for country in countries:
            country_id = f"country-{uuid.uuid4()}"
            self._countries[country_id] = country

        return countries

    def get_country(self, country_id: str) -> Country:
        """Get a country by ID.

        Args:
            country_id: The ID of the country to get.

        Returns:
            The Country object.

        Raises:
            KeyError: If the country ID is not found.
        """
        if country_id not in self._countries:
            raise KeyError(f"Country with ID '{country_id}' not found")
        return self._countries[country_id]

    def get_country_by_iso_code(self, iso_code: str) -> Country | None:
        """Get a country by ISO code.

        Args:
            iso_code: The ISO code of the country to get.

        Returns:
            The Country object, or None if not found.
        """
        return self._generator.get_by_iso_code(iso_code)

    def get_all_countries(self) -> list[Country]:
        """Get all countries.

        Returns:
            A list of all Country objects.
        """
        return list(self._countries.values())

    def clear_countries(self) -> None:
        """Clear all countries."""
        self._countries.clear()
