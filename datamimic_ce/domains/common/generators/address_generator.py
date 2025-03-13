# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import random

from datamimic_ce import logger
from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.generators.city_generator import CityGenerator
from datamimic_ce.domains.common.generators.country_generator import CountryGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.domains.common.literal_generators.street_name_generator import StreetNameGenerator


class AddressGenerator(BaseDomainGenerator):
    """Generator for address data.

    This class generates random address data using the AddressDataLoader.
    """
    # Default dataset if none available
    _DEFAULT_DATASET = "US"

    def __init__(self, country_code: str = _DEFAULT_DATASET):
        """Initialize the AddressGenerator.

        Args:
            country_code: The country code to use for generating addresses.
        """
        self._country_code = country_code.upper()

        # Initialize related data loaders
        self._city_generator = CityGenerator(country_code=self._country_code)
        self._country_generator = CountryGenerator()
        self._phone_number_generator = PhoneNumberGenerator()
        self._current_street_name_generator = None

    @property
    def country_code(self) -> str:
        """Get the country code.

        Returns:
            The country code.
        """
        return self._country_code

    @property
    def city_generator(self) -> CityGenerator:
        """Get the city generator.

        Returns:
            The city generator.
        """
        return self._city_generator

    @property
    def country_generator(self) -> CountryGenerator:
        """Get the country generator.

        Returns:
            The country generator.
        """
        return self._country_generator

    @property
    def phone_number_generator(self) -> PhoneNumberGenerator:
        """Get the phone number generator.

        Returns:
            The phone number generator.
        """
        return self._phone_number_generator

    def generate_street_name(self) -> str:
        """Generate a street name.

        Returns:
            A street name.
        """
        if self._current_street_name_generator is not None:
            return self._current_street_name_generator.generate()

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
