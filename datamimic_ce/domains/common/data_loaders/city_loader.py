# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from typing import Any

from datamimic_ce.core.base_data_loader import BaseDataLoader
from datamimic_ce.logger import logger
from datamimic_ce.utils.file_util import FileUtil


class CityDataLoader(BaseDataLoader):
    """Data loader for city data.

    This class is responsible for loading city and state data from CSV files.
    It provides methods to load city data, state data, and country information.
    """

    # Regional fallbacks for countries
    _REGIONAL_FALLBACKS: dict[str, tuple[str, ...]] = {
        # Western Europe fallbacks
        "DE": ("AT", "CH", "LU"),  # German-speaking
        "FR": ("BE", "CH", "LU", "MC"),  # French-speaking
        "IT": ("CH", "SM", "VA"),  # Italian-speaking
        "NL": ("BE", "LU"),  # Dutch-speaking
        # Nordic fallbacks
        "SE": ("NO", "DK", "FI"),  # Scandinavian
        "NO": ("SE", "DK", "FI"),
        "DK": ("NO", "SE", "DE"),
        "FI": ("SE", "EE"),
        # Eastern Europe fallbacks
        "PL": ("CZ", "SK", "DE"),
        "CZ": ("SK", "PL", "AT"),
        "SK": ("CZ", "PL", "HU"),
        "HU": ("SK", "RO", "AT"),
        # Balkan fallbacks
        "BA": ("HR", "RS", "SI"),  # Bosnia fallbacks
        "HR": ("SI", "BA", "AT"),
        "RS": ("BA", "BG", "RO"),
        # English-speaking fallbacks
        "US": ("CA", "GB", "AU"),
        "GB": ("IE", "US", "CA"),
        "CA": ("US", "GB"),
        "AU": ("NZ", "GB", "US"),
        "NZ": ("AU", "GB", "US"),
    }

    # Default dataset if none available
    _DEFAULT_DATASET = "US"

    # Module-level cache to avoid repeated file I/O
    _CITY_DATA_CACHE: dict[str, tuple[dict[str, int], list[tuple]]] = {}
    _STATE_DATA_CACHE: dict[str, dict[str, str]] = {}
    _COUNTRY_NAME_CACHE: dict[str, str] = {}

    def __init__(self, country_code: str = "US"):
        """Initialize the CityDataLoader.

        Args:
            country_code: The country code to use for loading data.
        """
        super().__init__()
        self.country_code = country_code.upper()
        self._data_cache: dict[str, Any] = {}
        self._current_dataset = self.country_code

    def load_city_data(self) -> tuple[dict[str, int], list[tuple]]:
        """Load city data from CSV file.

        Returns:
            A tuple containing the header dictionary and city data.
        """
        cache_key = f"city_data_{self.country_code}"

        # Check if we already have this dataset in cache
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        # Check if we already have this dataset in class cache
        if self.country_code in self._CITY_DATA_CACHE:
            self._data_cache[cache_key] = self._CITY_DATA_CACHE[self.country_code]
            return self._data_cache[cache_key]

        # Prepare data file path
        base_path = self._get_base_path_city()
        city_file_path = base_path / f"city_{self.country_code}.csv"

        # Try to load the requested dataset
        if city_file_path.exists():
            try:
                # Load city data
                city_header_dict, city_data = FileUtil.read_csv_to_dict_of_tuples_with_header(city_file_path, delimiter=";")

                # Cache the data
                self._data_cache[cache_key] = (city_header_dict, city_data)
                self._CITY_DATA_CACHE[self.country_code] = (city_header_dict, city_data)
                self._current_dataset = self.country_code

                return city_header_dict, city_data
            except Exception as e:
                logger.warning(f"Error loading dataset '{self.country_code}': {e}")
        else:
            logger.warning(f"Dataset '{self.country_code}' not found")

        # Try regional fallbacks
        for fallback in self._REGIONAL_FALLBACKS.get(self.country_code, ()):
            fallback_city_path = base_path / f"city_{fallback}.csv"

            # Check if file exists
            if not fallback_city_path.exists():
                continue

            try:
                logger.info(f"Using regional fallback '{fallback}' for dataset '{self.country_code}'")

                # Load city data from fallback
                city_header_dict, city_data = FileUtil.read_csv_to_dict_of_tuples_with_header(
                    fallback_city_path, delimiter=";"
                )

                # Cache the data
                self._data_cache[cache_key] = (city_header_dict, city_data)
                self._CITY_DATA_CACHE[self.country_code] = (city_header_dict, city_data)
                self._current_dataset = fallback

                return city_header_dict, city_data
            except Exception as e:
                logger.warning(f"Error loading fallback {fallback}: {e}")
                continue

        # If no fallbacks worked, use US as last resort
        logger.warning(f"No fallbacks found for '{self.country_code}', using default dataset 'US'")
        self._current_dataset = self._DEFAULT_DATASET

        # Load US city data
        us_city_path = base_path / f"city_{self._DEFAULT_DATASET}.csv"
        city_header_dict, city_data = FileUtil.read_csv_to_dict_of_tuples_with_header(
            us_city_path, delimiter=";"
        )

        # Cache the data
        self._data_cache[cache_key] = (city_header_dict, city_data)
        self._CITY_DATA_CACHE[self.country_code] = (city_header_dict, city_data)

        return city_header_dict, city_data

    def load_state_data(self) -> dict[str, str]:
        """Load state data from CSV file.

        Returns:
            A dictionary mapping state IDs to state names.
        """
        cache_key = f"state_data_{self._current_dataset}"

        # Check if we already have this dataset in cache
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        # Check if we already have this dataset in class cache
        if self._current_dataset in self._STATE_DATA_CACHE:
            self._data_cache[cache_key] = self._STATE_DATA_CACHE[self._current_dataset]
            return self._data_cache[cache_key]

        # Prepare data file path
        base_path = self._get_base_path_state()
        state_file_path = base_path / f"state_{self._current_dataset}.csv"

        try:
            # Load state data
            state_headers, state_data = FileUtil.read_csv_to_dict_of_tuples_with_header(state_file_path)

            # Build state dictionary
            state_dict = dict(
                zip(
                    [data[state_headers["id"]] for data in state_data],
                    [data[state_headers["name"]] for data in state_data],
                    strict=False,
                )
            )

            # Cache the data
            self._data_cache[cache_key] = state_dict
            self._STATE_DATA_CACHE[self._current_dataset] = state_dict

            return state_dict

        except FileNotFoundError:
            logger.warning(f"State data file not found: {state_file_path}")
            return {}

    def load_country_name(self) -> str:
        """Load country name from CSV file.

        Returns:
            The name of the country.
        """
        # Check if we already have this dataset in class cache
        if self._current_dataset in self._COUNTRY_NAME_CACHE:
            return self._COUNTRY_NAME_CACHE[self._current_dataset]

        # Load country data
        country_path = self._get_base_path_country() / "country.csv"
        country_df = FileUtil.read_csv_to_list_of_tuples_without_header(country_path, delimiter=",")

        country_name = ""
        for c in country_df:
            if c[0] == self._current_dataset:
                country_name = str(c[3])  # Country name is at index 3
                # Cache the country name
                self._COUNTRY_NAME_CACHE[self._current_dataset] = country_name
                break

        return country_name

    def get_city_by_index(self, index: int) -> dict[str, Any]:
        """Get a city by index.

        Args:
            index: The index of the city to get.

        Returns:
            A dictionary containing the city data.
        """
        # Load city data
        city_header_dict, city_data = self.load_city_data()

        # Load state data
        state_dict = self.load_state_data()

        # Load country name
        country_name = self.load_country_name()

        # Check if index is valid
        if index < 0 or index >= len(city_data):
            index = 0

        # Get city row
        city_row = city_data[index]

        # Build city dictionary
        return {
            "name": city_row[city_header_dict.get("name")],
            "postal_code": city_row[city_header_dict.get("postalCode")],
            "area_code": city_row[city_header_dict.get("areaCode")],
            "state_id": city_row[city_header_dict.get("state.id")],
            "state": state_dict.get(city_row[city_header_dict.get("state.id")] or "", ""),
            "language": city_row[city_header_dict.get("language")] if "language" in city_header_dict else None,
            "population": city_row[city_header_dict.get("population")],
            "name_extension": city_row[city_header_dict.get("nameExtension")] if "nameExtension" in city_header_dict else "",
            "country": country_name,
            "country_code": self._current_dataset,
        }

    def get_random_city(self) -> dict[str, Any]:
        """Get a random city.

        Returns:
            A dictionary containing the city data.
        """
        import random

        # Load city data
        _, city_data = self.load_city_data()

        # Get random index
        random_index = random.randint(0, len(city_data) - 1)

        # Get city by index
        return self.get_city_by_index(random_index)

    def get_cities_batch(self, count: int = 10) -> list[dict[str, Any]]:
        """Get a batch of cities.

        Args:
            count: The number of cities to get.

        Returns:
            A list of dictionaries containing city data.
        """
        import random

        # Load city data
        _, city_data = self.load_city_data()

        # Get random indices
        random_indices = random.sample(range(len(city_data)), min(count, len(city_data)))

        # Get cities by indices
        return [self.get_city_by_index(index) for index in random_indices]

    def _get_base_path_city(self) -> Path:
        """Get the base path for city data.

        Returns:
            The base path for city data.
        """
        return Path(__file__).parent.parent.parent.parent / "data" / "common" / "city"

    def _get_base_path_state(self) -> Path:
        """Get the base path for state data.

        Returns:
            The base path for state data.
        """
        return Path(__file__).parent.parent.parent.parent / "data" / "common" / "state"

    def _get_base_path_country(self) -> Path:
        """Get the base path for country data.

        Returns:
            The base path for country data.
        """
        return Path(__file__).parent.parent.parent.parent / "data" / "common"
