# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.domains.common.data_loaders.city_loader import CityDataLoader
from datamimic_ce.domains.common.models.city import City
from datamimic_ce.generators.generator import Generator


class CityGenerator(Generator):
    """Generator for city data.

    This class generates random city data using the CityDataLoader.
    """

    def __init__(self, country_code: str = "US", data_loader: CityDataLoader = None):
        """Initialize the CityGenerator.

        Args:
            country_code: The country code to use for generating cities.
            data_loader: Optional data loader to use. If not provided, a new one will be created.
        """
        self._country_code = country_code.upper()
        self._data_loader = data_loader if data_loader is not None else CityDataLoader(country_code=self._country_code)

    @property
    def country_code(self) -> str:
        """Get the country code.

        Returns:
            The country code.
        """
        return self._country_code

    def generate(self) -> City:
        """Generate a random city.

        Returns:
            A City object.
        """
        city_data = self._data_loader.get_random_city()
        return City.create(city_data)

    def generate_batch(self, count: int = 10) -> list[City]:
        """Generate a batch of cities.

        Args:
            count: The number of cities to generate.

        Returns:
            A list of City objects.
        """
        cities_data = self._data_loader.get_cities_batch(count)
        return [City.create(city_data) for city_data in cities_data]

    def get_by_index(self, index: int) -> City:
        """Get a city by index.

        Args:
            index: The index of the city to get.

        Returns:
            A City object.
        """
        city_data = self._data_loader.get_city_by_index(index)
        return City.create(city_data)

    def set_country_code(self, country_code: str) -> None:
        """Set the country code for generating cities.

        Args:
            country_code: The country code to use.
        """
        self._country_code = country_code.upper()
        self._data_loader.country_code = self._country_code
