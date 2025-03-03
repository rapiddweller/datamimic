# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.core.interfaces import Generator
from datamimic_ce.domains.common.data_loaders.country_loader import CountryDataLoader
from datamimic_ce.domains.common.models.country import Country


class CountryGenerator(Generator):
    """Generator for country data.

    This class generates random country data using the CountryDataLoader.
    """

    def __init__(self, data_loader: CountryDataLoader = None):
        """Initialize the CountryGenerator.

        Args:
            data_loader: Optional data loader to use. If not provided, a new one will be created.
        """
        self._data_loader = data_loader if data_loader is not None else CountryDataLoader()

    def generate(self) -> Country:
        """Generate a random country.

        Returns:
            A Country object.
        """
        country_data = self._data_loader.get_random_country()
        return Country.create(country_data)

    def generate_batch(self, count: int = 10) -> list[Country]:
        """Generate a batch of countries.

        Args:
            count: The number of countries to generate.

        Returns:
            A list of Country objects.
        """
        countries_data = self._data_loader.get_countries_batch(count)
        return [Country.create(country_data) for country_data in countries_data]

    def get_by_iso_code(self, iso_code: str) -> Country | None:
        """Get a country by ISO code.

        Args:
            iso_code: The ISO code of the country to get.

        Returns:
            A Country object, or None if not found.
        """
        country_data = self._data_loader.get_country_by_iso_code(iso_code)
        if country_data is None:
            return None
        return Country.create(country_data)
