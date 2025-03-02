# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path
from typing import Any

from datamimic_ce.core.base_data_loader import BaseDataLoader
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
    _STREET_DATA_CACHE: dict[str, list[str]] = {}
    _HOUSE_NUMBER_CACHE: dict[str, list[str]] = {}
    _CONTINENT_CACHE: dict[str, str] = {}

    def __init__(self, country_code: str = "US"):
        """Initialize the AddressDataLoader.

        Args:
            country_code: The country code to use for loading data.
        """
        super().__init__()
        self.country_code = country_code.upper()
        self._data_cache: dict[str, Any] = {}
        self._current_dataset = self.country_code

        # Initialize related data loaders
        self._city_loader = CityDataLoader(country_code=self.country_code)
        self._country_loader = CountryDataLoader()

    def load_street_data(self) -> list[str]:
        """Load street data from CSV file.

        Returns:
            A list of street names.
        """
        cache_key = f"street_data_{self.country_code}"

        # Check if we already have this dataset in cache
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        # Check if we already have this dataset in class cache
        if self.country_code in self._STREET_DATA_CACHE:
            self._data_cache[cache_key] = self._STREET_DATA_CACHE[self.country_code]
            return self._data_cache[cache_key]

        # Prepare data file path
        base_path = self._get_base_path_address()
        street_file_path = base_path / f"street_{self.country_code}.csv"

        # Try to load the requested dataset
        if street_file_path.exists():
            try:
                # Load street data
                street_data = FileUtil.read_csv_to_list_of_tuples_without_header(street_file_path, delimiter=";")

                # Flatten the list if it's a list of tuples
                if street_data and isinstance(street_data[0], tuple):
                    street_data = [item[0] for item in street_data]

                # Cache the data
                self._data_cache[cache_key] = street_data
                self._STREET_DATA_CACHE[self.country_code] = street_data
                self._current_dataset = self.country_code

                return street_data
            except Exception as e:
                logger.warning(f"Error loading dataset '{self.country_code}': {e}")
        else:
            logger.warning(f"Street dataset '{self.country_code}' not found")

        # Try regional fallbacks
        for fallback in self._REGIONAL_FALLBACKS.get(self.country_code, ()):
            fallback_street_path = base_path / f"street_{fallback}.csv"

            # Check if file exists
            if not fallback_street_path.exists():
                continue

            try:
                logger.info(f"Using regional fallback '{fallback}' for street dataset '{self.country_code}'")

                # Load street data from fallback
                street_data = FileUtil.read_csv_to_list_of_tuples_without_header(fallback_street_path, delimiter=";")

                # Flatten the list if it's a list of tuples
                if street_data and isinstance(street_data[0], tuple):
                    street_data = [item[0] for item in street_data]

                # Cache the data
                self._data_cache[cache_key] = street_data
                self._STREET_DATA_CACHE[self.country_code] = street_data
                self._current_dataset = fallback

                return street_data
            except Exception as e:
                logger.warning(f"Error loading fallback {fallback}: {e}")
                continue

        # If no fallbacks worked, use US as last resort
        logger.warning(f"No fallbacks found for '{self.country_code}', using default dataset 'US'")
        self._current_dataset = self._DEFAULT_DATASET

        # Load US street data
        us_street_path = base_path / f"street_{self._DEFAULT_DATASET}.csv"
        try:
            street_data = FileUtil.read_csv_to_list_of_tuples_without_header(us_street_path, delimiter=";")

            # Flatten the list if it's a list of tuples
            if street_data and isinstance(street_data[0], tuple):
                street_data = [item[0] for item in street_data]

            # Cache the data
            self._data_cache[cache_key] = street_data
            self._STREET_DATA_CACHE[self.country_code] = street_data

            return street_data
        except Exception as e:
            logger.error(f"Error loading default street dataset: {e}")
            return []

    def load_house_numbers(self) -> list[str]:
        """Load house number data.

        Returns:
            A list of house numbers.
        """
        cache_key = f"house_number_{self.country_code}"

        # Check if we already have this dataset in cache
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        # Check if we already have this dataset in class cache
        if self.country_code in self._HOUSE_NUMBER_CACHE:
            self._data_cache[cache_key] = self._HOUSE_NUMBER_CACHE[self.country_code]
            return self._data_cache[cache_key]

        # Generate house numbers based on country format
        house_numbers = []

        # North American format (mostly numeric)
        if self.country_code in ["US", "CA"]:
            house_numbers = [str(i) for i in range(1, 10000, 2)]  # Odd numbers up to 9999

        # European format (can include letters)
        elif self.country_code in ["DE", "FR", "GB", "IT", "ES"]:
            # Basic numbers
            house_numbers = [str(i) for i in range(1, 200)]

            # Add some with letters for certain countries
            if self.country_code in ["GB", "NL"]:
                for i in range(1, 50):
                    house_numbers.append(f"{i}A")
                    house_numbers.append(f"{i}B")

        # Default format
        else:
            house_numbers = [str(i) for i in range(1, 200)]

        # Cache the data
        self._data_cache[cache_key] = house_numbers
        self._HOUSE_NUMBER_CACHE[self.country_code] = house_numbers

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

    def get_random_address(self) -> dict[str, Any]:
        """Get a random address.

        Returns:
            A dictionary containing address data.
        """
        # Get random street
        streets = self.load_street_data()
        street = random.choice(streets) if streets else "Main Street"

        # Get random house number
        house_numbers = self.load_house_numbers()
        house_number = random.choice(house_numbers) if house_numbers else "123"

        # Get random city data
        city_data = self._city_loader.get_random_city()

        # Get country data
        country_data = self._country_loader.get_country_by_iso_code(self.country_code)
        if not country_data:
            country_data = self._country_loader.get_country_by_iso_code("US")

        # Get continent
        continent = self.get_continent_for_country(self.country_code)

        # Generate random coordinates (simplified)
        latitude = random.uniform(-90, 90)
        longitude = random.uniform(-180, 180)

        # Build address dictionary
        return {
            "street": street,
            "house_number": house_number,
            "city": city_data["name"],
            "state": city_data["state"],
            "postal_code": city_data["postal_code"],
            "country": country_data["name"] if country_data else "United States",
            "country_code": self.country_code,
            "continent": continent,
            "latitude": latitude,
            "longitude": longitude,
            "phone": self._generate_phone_number(),
            "mobile_phone": self._generate_mobile_number(),
            "fax": self._generate_phone_number(),
        }

    def get_addresses_batch(self, count: int = 10) -> list[dict[str, Any]]:
        """Get a batch of addresses.

        Args:
            count: The number of addresses to get.

        Returns:
            A list of dictionaries containing address data.
        """
        return [self.get_random_address() for _ in range(count)]

    def _generate_phone_number(self) -> str:
        """Generate a random phone number based on country code.

        Returns:
            A phone number string.
        """
        if self.country_code == "US":
            area_code = random.randint(200, 999)
            prefix = random.randint(200, 999)
            line = random.randint(1000, 9999)
            return f"+1 ({area_code}) {prefix}-{line}"
        elif self.country_code == "GB":
            area_code = random.randint(1000, 9999)
            number = random.randint(100000, 999999)
            return f"+44 {area_code} {number}"
        elif self.country_code == "DE":
            area_code = random.randint(10, 999)
            number = random.randint(1000000, 9999999)
            return f"+49 {area_code} {number}"
        elif self.country_code == "FR":
            part1 = random.randint(10, 99)
            part2 = random.randint(10, 99)
            part3 = random.randint(10, 99)
            part4 = random.randint(10, 99)
            part5 = random.randint(10, 99)
            return f"+33 {part1} {part2} {part3} {part4} {part5}"
        else:
            # Generic international format
            country_code_num = random.randint(1, 999)
            number = random.randint(1000000000, 9999999999)
            return f"+{country_code_num} {number}"

    def _generate_mobile_number(self) -> str:
        """Generate a random mobile phone number based on country code.

        Returns:
            A mobile phone number string.
        """
        if self.country_code == "US":
            area_code = random.randint(200, 999)
            prefix = random.randint(200, 999)
            line = random.randint(1000, 9999)
            return f"+1 ({area_code}) {prefix}-{line}"
        elif self.country_code == "GB":
            prefix = random.choice(["7700", "7800", "7900"])
            number = random.randint(100000, 999999)
            return f"+44 {prefix} {number}"
        elif self.country_code == "DE":
            prefix = random.choice(["151", "152", "157", "160", "170", "171", "175"])
            number = random.randint(1000000, 9999999)
            return f"+49 {prefix} {number}"
        elif self.country_code == "FR":
            prefix = "6"
            part1 = random.randint(10, 99)
            part2 = random.randint(10, 99)
            part3 = random.randint(10, 99)
            part4 = random.randint(10, 99)
            return f"+33 {prefix}{part1} {part2} {part3} {part4}"
        else:
            # Generic international format
            country_code_num = random.randint(1, 999)
            number = random.randint(1000000000, 9999999999)
            return f"+{country_code_num} {number}"

    def _get_base_path_address(self) -> Path:
        """Get the base path for address data.

        Returns:
            The base path for address data.
        """
        return Path(__file__).parent.parent.parent.parent / "data" / "common" / "address"
