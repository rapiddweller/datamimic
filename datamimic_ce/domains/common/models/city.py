# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.common.generators.city_generator import CityGenerator


class City(BaseEntity):
    """
    Represents a city with various attributes.

    This class provides access to city data including name, postal code, area code,
    state, language, population, and country information.
    """

    def __init__(self, city_generator: CityGenerator):
        super().__init__()
        self._city_generator = city_generator

    @property
    @property_cache
    def city_data(self) -> dict[str, Any]:
        """Get the city data.

        Returns:
            The city data.
        """
        return self._city_generator.get_random_city()

    @property
    @property_cache
    def name(self) -> str:
        """Get the name of the city.

        Returns:
            The name of the city.
        """
        return self.city_data["name"]

    @property
    @property_cache
    def postal_code(self) -> str:
        """Get the postal code of the city.

        Returns:
            The postal code of the city.
        """
        return self.city_data["postal_code"]

    @property
    @property_cache
    def area_code(self) -> str:
        """Get the area code of the city.

        Returns:
            The area code of the city.
        """
        return self.city_data["area_code"]

    @property
    @property_cache
    def state(self) -> str:
        """Get the state of the city.

        Returns:
            The state of the city.
        """
        return self.city_data["state"]

    @property
    @property_cache
    def language(self) -> str | None:
        """Get the language of the city.

        Returns:
            The language of the city.
        """
        return self.city_data["language"]

    @property
    @property_cache
    def population(self) -> int | None:
        """Get the population of the city.

        Returns:
            The population of the city.
        """
        population = self.city_data["population"]
        if population is None or population == "":
            return None
        return int(population)

    @property
    @property_cache
    def name_extension(self) -> str:
        """Get the name extension of the city.

        Returns:
            The name extension of the city.
        """
        return self.city_data["name_extension"]

    @property
    @property_cache
    def country(self) -> str:
        """Get the country of the city.

        Returns:
            The country of the city.
        """
        return self.city_data["country"]

    @property
    @property_cache
    def country_code(self) -> str:
        """Get the country code of the city.

        Returns:
            The country code of the city.

        """
        return self.city_data["country_code"]

    def to_dict(self) -> dict[str, Any]:
        """Convert the city to a dictionary.

        Returns:
            A dictionary representation of the city.
        """
        return {
            "name": self.name,
            "postal_code": self.postal_code,
            "area_code": self.area_code,
            "state": self.state,
            "language": self.language,
            "population": self.population,
            "name_extension": self.name_extension,
            "country": self.country,
            "country_code": self.country_code,
        }
