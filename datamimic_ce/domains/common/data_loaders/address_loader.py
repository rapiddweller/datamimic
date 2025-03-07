# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce import logger
from datamimic_ce.domain_core.base_data_loader import BaseDataLoader
from datamimic_ce.domains.common.data_loaders.city_loader import CityDataLoader
from datamimic_ce.domains.common.data_loaders.country_loader import CountryDataLoader
from datamimic_ce.generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.generators.street_name_generator import StreetNameGenerator


class AddressDataLoader(BaseDataLoader):
    """Data loader for address data.

    This class is responsible for loading address data from CSV files.
    It provides methods to load street names, house numbers, and other address components.
    """
    # Default dataset if none available
    _DEFAULT_DATASET = "US"

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
        self._phone_number_generator = PhoneNumberGenerator()
        self._current_street_name_generator = None

    @property   
    def phone_number_generator(self) -> PhoneNumberGenerator:
        """Get the phone number generator.

        Returns:
            The phone number generator.
        """
        return self._phone_number_generator
    
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
    
    def generate_street_name(self) -> str:
        """Generate a street name.

        Returns:
            A street name.
        """
        try:
            self._current_street_name_generator = StreetNameGenerator(dataset=self._country_code)
            return self._current_street_name_generator.generate()
        except FileNotFoundError:
            logger.warning(f"Street dataset '{self._country_code}' not found")

        logger.warning(f"No street dataset found for '{self._country_code}', using regional fallbacks")
        for fallback in self._REGIONAL_FALLBACKS.get(self._country_code, ()):
            try:
                self._current_street_name_generator = StreetNameGenerator(dataset=fallback)
                return self._current_street_name_generator.generate()
            except FileNotFoundError:
                continue

        logger.warning(f"No street dataset found for '{self._country_code}', using default dataset 'US'")
        self._country_code = self._DEFAULT_DATASET
        self._current_street_name_generator = StreetNameGenerator(dataset=self._DEFAULT_DATASET)
        return self._current_street_name_generator.generate()

    def generate_house_number(self) -> str:
        """Generate a house number.

        Returns:
            A house number.
        """
        # North American format (mostly numeric)
        if self._country_code in ["US", "CA"]:
            house_number = str(random.randint(1, 9999))

        # European format (can include letters)
        elif self._country_code in ["DE", "FR", "GB", "IT", "ES"]:
            house_number = str(random.randint(1, 9999))

            # Add some with letters for certain countries randomly
            if self._country_code in ["GB", "NL"]:
                if random.random() < 0.2:
                    house_number = f"{house_number}A"
                elif random.random() < 0.3:
                    house_number = f"{house_number}B"

        return house_number

    def get_continent_for_country(self, country_code: str) -> str:
        """Get the continent for a country code.

        Args:
            country_code: The country code to look up.

        Returns:
            The continent name.
        """
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

        return continent_mapping.get(country_code, "Unknown")
