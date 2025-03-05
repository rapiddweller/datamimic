# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from typing import Any

from datamimic_ce.logger import logger
from datamimic_ce.utils.file_util import FileUtil


class CountryDataLoader:
    """Data loader for country data.

    This class is responsible for loading country data from CSV files.
    It provides methods to load country data and access specific countries.
    """

    # Module-level cache to avoid repeated file I/O
    _COUNTRY_DATA_CACHE: list[tuple[Any, ...]] = []
    _COUNTRY_CODE_INDEX: dict[str, int] = {}

    def __init__(self):
        """Initialize the CountryDataLoader."""
        super().__init__()
        self._data_cache: dict[str, Any] = {}

    def load_country_data(self) -> list[tuple[Any, ...]]:
        """Load country data from CSV file.

        Returns:
            A list of tuples containing country data.
        """
        cache_key = "country_data"

        # Check if we already have this data in cache
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        # Check if we already have this data in class cache
        if self._COUNTRY_DATA_CACHE:
            self._data_cache[cache_key] = self._COUNTRY_DATA_CACHE
            return self._data_cache[cache_key]

        # Prepare data file path
        country_file_path = self._get_base_path_country() / "country.csv"

        try:
            # Load country data
            country_data = FileUtil.read_csv_to_list_of_tuples_without_header(country_file_path, delimiter=",")

            # Build index for faster lookup by country code
            for i, country in enumerate(country_data):
                self._COUNTRY_CODE_INDEX[country[0]] = i

            # Cache the data
            self._data_cache[cache_key] = country_data
            self._COUNTRY_DATA_CACHE = country_data

            return country_data

        except Exception as e:
            logger.error(f"Error loading country data: {e}")
            return []

    def get_country_by_iso_code(self, iso_code: str) -> dict[str, Any] | None:
        """Get a country by ISO code.

        Args:
            iso_code: The ISO code of the country to get.

        Returns:
            A dictionary containing the country data, or None if not found.
        """
        # Load country data
        country_data = self.load_country_data()

        # Get country index
        index = self._COUNTRY_CODE_INDEX.get(iso_code.upper())
        if index is None:
            return None

        # Get country row
        country_row = country_data[index]

        # Build country dictionary
        return {
            "iso_code": country_row[0],
            "default_language_locale": country_row[1],
            "phone_code": country_row[2],
            "name": country_row[3],
            "population": country_row[4],
        }

    def get_random_country(self) -> dict[str, Any]:
        """Get a random country.

        Returns:
            A dictionary containing the country data.
        """
        import random

        # Load country data
        country_data = self.load_country_data()

        # Get random index
        random_index = random.randint(0, len(country_data) - 1)

        # Get country row
        country_row = country_data[random_index]

        # Build country dictionary
        return {
            "iso_code": country_row[0],
            "default_language_locale": country_row[1],
            "phone_code": country_row[2],
            "name": country_row[3],
            "population": country_row[4],
        }

    def get_countries_batch(self, count: int = 10) -> list[dict[str, Any]]:
        """Get a batch of countries.

        Args:
            count: The number of countries to get.

        Returns:
            A list of dictionaries containing country data.
        """
        import random

        # Load country data
        country_data = self.load_country_data()

        # Get random indices
        random_indices = random.sample(range(len(country_data)), min(count, len(country_data)))

        # Get countries
        countries = []
        for index in random_indices:
            country_row = country_data[index]
            countries.append(
                {
                    "iso_code": country_row[0],
                    "default_language_locale": country_row[1],
                    "phone_code": country_row[2],
                    "name": country_row[3],
                    "population": country_row[4],
                }
            )

        return countries

    def _get_base_path_country(self) -> Path:
        """Get the base path for country data.

        Returns:
            The base path for country data.
        """
        return Path(__file__).parent.parent.parent.parent / "data" / "common"
