# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path
from typing import Any, ClassVar

from datamimic_ce.domain_core.base_data_loader import BaseDataLoader
from datamimic_ce.domains.common.data_loaders.city_loader import CityDataLoader
from datamimic_ce.domains.common.data_loaders.country_loader import CountryDataLoader
from datamimic_ce.logger import logger
from datamimic_ce.utils.file_util import FileUtil


class AddressDataLoader(BaseDataLoader):
    """Data loader for address data.

    This class is responsible for loading address data from CSV files.
    It provides methods to load street names, house numbers, and other address components.
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
    BaseDataLoader._LOADED_DATA_CACHE["street"] = {}
    _STREET_DATA_CACHE = BaseDataLoader._LOADED_DATA_CACHE["street"]
    BaseDataLoader._LOADED_DATA_CACHE["house_number"] = {}
    _HOUSE_NUMBER_CACHE = BaseDataLoader._LOADED_DATA_CACHE["house_number"]
    BaseDataLoader._LOADED_DATA_CACHE["continent"] = {}
    _CONTINENT_CACHE = BaseDataLoader._LOADED_DATA_CACHE["continent"]

    def __init__(self, country_code: str = _DEFAULT_DATASET):
        """Initialize the AddressDataLoader.

        Args:
            country_code: The country code to use for loading data.
        """
        super().__init__()
        self._country_code = country_code.upper()

        # Initialize related data loaders
        self._city_loader = CityDataLoader(country_code=self._country_code)
        self._country_loader = CountryDataLoader()

    @property
    def country_code(self) -> str:
        """Get the country code.

        Returns:
            The country code.
        """
        return self._country_code
    @property
    def city_loader(self) -> CityDataLoader:
        """Get the city data loader.

        Returns:
            The city data loader.
        """
        return self._city_loader
    
    @property
    def country_loader(self) -> CountryDataLoader:
        """Get the country data loader.

        Returns:
            The country data loader.
        """
        return self._country_loader
    
    @staticmethod
    def _get_base_path_address() -> Path:
        """Get the base path for address data.

        Returns:
            The base path for address data.
        """
        return Path(__file__).parent.parent.parent.parent / "data" / "common" / "address"

    def load_street_data(self) -> list[str]:
        """Load street data from CSV file.

        Returns:
            A list of street names.
        """

        # Check if we already have this dataset in cache
        if self._country_code in self._STREET_DATA_CACHE:
            return self._STREET_DATA_CACHE[self._country_code]

        # Prepare data file path
        base_path = self._get_base_path_address()
        street_file_path = base_path / f"street_{self._country_code}.csv"

        # Try to load the requested dataset
        if street_file_path.exists():
            try:
                # Load street data
                street_data = FileUtil.read_csv_to_list_of_tuples_without_header(street_file_path, delimiter=";")

                # Flatten the list if it's a list of tuples
                if street_data and isinstance(street_data[0], tuple):
                    street_data = [item[0] for item in street_data]

                # Cache the data
                self._STREET_DATA_CACHE[self._country_code] = street_data

                return street_data
            except Exception as e:
                logger.warning(f"Error loading dataset '{self._country_code}': {e}")
        else:
            logger.warning(f"Street dataset '{self._country_code}' not found")

        # Try regional fallbacks
        for fallback in self._REGIONAL_FALLBACKS.get(self._country_code, ()):
            fallback_street_path = base_path / f"street_{fallback}.csv"

            # Check if file exists
            if not fallback_street_path.exists():
                continue

            try:
                logger.info(f"Using regional fallback '{fallback}' for street dataset '{self._country_code}'")

                # Load street data from fallback
                street_data = FileUtil.read_csv_to_list_of_tuples_without_header(fallback_street_path, delimiter=";")

                # Flatten the list if it's a list of tuples
                if street_data and isinstance(street_data[0], tuple):
                    street_data = [item[0] for item in street_data]

                # Cache the data
                self._STREET_DATA_CACHE[self._country_code] = street_data

                return street_data
            except Exception as e:
                logger.warning(f"Error loading fallback {fallback}: {e}")
                continue

        # If no fallbacks worked, use US as last result
        logger.warning(f"No fallbacks found for '{self._country_code}', using default dataset 'US'")
        self._country_code = self._DEFAULT_DATASET

        # Load US street data
        us_street_path = base_path / f"street_{self._DEFAULT_DATASET}.csv"
        try:
            street_data = FileUtil.read_csv_to_list_of_tuples_without_header(us_street_path, delimiter=";")

            # Flatten the list if it's a list of tuples
            if street_data and isinstance(street_data[0], tuple):
                street_data = [item[0] for item in street_data]

            # Cache the data
            self._STREET_DATA_CACHE[self._country_code] = street_data

            return street_data
        except Exception as e:
            logger.error(f"Error loading default street dataset: {e}")
            return []

    def load_house_numbers(self) -> list[str]:
        """Load house number data.

        Returns:
            A list of house numbers.
        """
        # Check if we already have this dataset in cache
        if self._country_code in self._HOUSE_NUMBER_CACHE:
            return self._HOUSE_NUMBER_CACHE[self._country_code]

        # Generate house numbers based on country format
        house_numbers = []

        # North American format (mostly numeric)
        if self._country_code in ["US", "CA"]:
            house_numbers = [str(i) for i in range(1, 10000, 2)]  # Odd numbers up to 9999

        # European format (can include letters)
        elif self._country_code in ["DE", "FR", "GB", "IT", "ES"]:
            # Basic numbers
            house_numbers = [str(i) for i in range(1, 200)]

            # Add some with letters for certain countries
            if self._country_code in ["GB", "NL"]:
                for i in range(1, 50):
                    house_numbers.append(f"{i}A")
                    house_numbers.append(f"{i}B")

        # Default format
        else:
            house_numbers = [str(i) for i in range(1, 200)]

        # Cache the data
        self._HOUSE_NUMBER_CACHE[self._country_code] = house_numbers

        return house_numbers

    def get_continent_for_country(self, country_code: str) -> str:
        """Get the continent for a country code.

        Args:
            country_code: The country code to look up.

        Returns:
            The continent name.
        """
        # Check cache first
        if country_code in self._CONTINENT_CACHE:
            return self._CONTINENT_CACHE[country_code]

        # Continent mapping
        continent_mapping = {
            # North America
            "US": "North America",
            "CA": "North America",
            "MX": "North America",
            # Europe
            "GB": "Europe",
            "DE": "Europe",
            "FR": "Europe",
            "IT": "Europe",
            "ES": "Europe",
            "NL": "Europe",
            "BE": "Europe",
            "CH": "Europe",
            "AT": "Europe",
            "SE": "Europe",
            "NO": "Europe",
            "DK": "Europe",
            "FI": "Europe",
            "PT": "Europe",
            "IE": "Europe",
            "PL": "Europe",
            "CZ": "Europe",
            "HU": "Europe",
            "RO": "Europe",
            "BG": "Europe",
            "GR": "Europe",
            "HR": "Europe",
            "RS": "Europe",
            "SK": "Europe",
            "SI": "Europe",
            # Asia
            "CN": "Asia",
            "JP": "Asia",
            "IN": "Asia",
            "KR": "Asia",
            "ID": "Asia",
            "TH": "Asia",
            "VN": "Asia",
            "MY": "Asia",
            "PH": "Asia",
            "SG": "Asia",
            # South America
            "BR": "South America",
            "AR": "South America",
            "CO": "South America",
            "PE": "South America",
            "CL": "South America",
            "VE": "South America",
            "EC": "South America",
            # Africa
            "ZA": "Africa",
            "NG": "Africa",
            "EG": "Africa",
            "MA": "Africa",
            "KE": "Africa",
            # Oceania
            "AU": "Oceania",
            "NZ": "Oceania",
        }

        continent = continent_mapping.get(country_code, "Unknown")

        # Cache the result
        self._CONTINENT_CACHE[country_code] = continent

        return continent

    
