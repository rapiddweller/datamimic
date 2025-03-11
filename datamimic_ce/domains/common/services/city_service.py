# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import uuid

from datamimic_ce.domains.common.generators.city_generator import CityGenerator
from datamimic_ce.domains.common.models.city import City
from datamimic_ce.domain_core.base_domain_service import BaseDomainService

class CityService(BaseDomainService[City]):
    """Service for managing city data.

    This class provides methods for creating, retrieving, and managing city data.
    """
    def __init__(self):
        super().__init__(CityGenerator(), City)

    # def __init__(self):
    #     """Initialize the CityService."""
    #     self._cities: dict[str, City] = {}
    #     self._generators: dict[str, CityGenerator] = {}
    #     self._default_country_code = "US"

    # def create_city(self, country_code: str | None = None) -> City:
    #     """Create a new city.

    #     Args:
    #         country_code: The country code to use for generating the city.

    #     Returns:
    #         A new City object.
    #     """
    #     country_code = country_code.upper() if country_code else self._default_country_code

    #     # Get or create generator for the country code
    #     generator = self._get_generator(country_code)

    #     # Generate a new city
    #     city = generator.generate()

    #     # Store the city with a unique ID
    #     city_id = f"city-{uuid.uuid4()}"
    #     self._cities[city_id] = city

    #     return city

    # def create_cities_batch(self, count: int = 10, country_code: str | None = None) -> list[City]:
    #     """Create a batch of cities.

    #     Args:
    #         count: The number of cities to create.
    #         country_code: The country code to use for generating the cities.

    #     Returns:
    #         A list of City objects.
    #     """
    #     country_code = country_code.upper() if country_code else self._default_country_code

    #     # Get or create generator for the country code
    #     generator = self._get_generator(country_code)

    #     # Generate a batch of cities
    #     cities = generator.generate_batch(count)

    #     # Store the cities with unique IDs
    #     for city in cities:
    #         city_id = f"city-{uuid.uuid4()}"
    #         self._cities[city_id] = city

    #     return cities

    # def get_city(self, city_id: str) -> City:
    #     """Get a city by ID.

    #     Args:
    #         city_id: The ID of the city to get.

    #     Returns:
    #         The City object.

    #     Raises:
    #         KeyError: If the city ID is not found.
    #     """
    #     if city_id not in self._cities:
    #         raise KeyError(f"City with ID '{city_id}' not found")
    #     return self._cities[city_id]

    # def get_all_cities(self) -> list[City]:
    #     """Get all cities.

    #     Returns:
    #         A list of all City objects.
    #     """
    #     return list(self._cities.values())

    # def clear_cities(self) -> None:
    #     """Clear all cities."""
    #     self._cities.clear()

    # def set_default_country_code(self, country_code: str) -> None:
    #     """Set the default country code for generating cities.

    #     Args:
    #         country_code: The country code to use.
    #     """
    #     self._default_country_code = country_code.upper()

    # def _get_generator(self, country_code: str) -> CityGenerator:
    #     """Get or create a generator for the specified country code.

    #     Args:
    #         country_code: The country code to use.

    #     Returns:
    #         A CityGenerator for the specified country code.
    #     """
    #     if country_code not in self._generators:
    #         self._generators[country_code] = CityGenerator(country_code=country_code)
    #     return self._generators[country_code]
