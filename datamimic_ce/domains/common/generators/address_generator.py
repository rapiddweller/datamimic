# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import random
from typing import Any
from datamimic_ce.domains.common.data_loaders.address_loader import AddressDataLoader
from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.generators.generator import Generator


class AddressGenerator(Generator):
    """Generator for address data.

    This class generates random address data using the AddressDataLoader.
    """

    def __init__(self, country_code: str = "US"):
        """Initialize the AddressGenerator.

        Args:
            country_code: The country code to use for generating addresses.
        """
        self._country_code = country_code.upper()
        self._data_loader = AddressDataLoader(country_code=self._country_code)

    def generate(self) -> Address:
        """Generate a random address.

        Returns:
            An Address object.
        """
        address_data_dict = self._generate_random_address()
        return Address.create(address_data_dict)

    def generate_batch(self, count: int = 10) -> list[Address]:
        """Generate a batch of addresses.

        Args:
            count: The number of addresses to generate.

        Returns:
            A list of Address objects.
        """
        return [self.generate() for _ in range(count)]

    def _generate_random_address(self) -> dict[str, Any]:
        """Generate a random address.

        Returns:
            A dictionary containing address data.
        """
        # Get random street
        streets = self._data_loader.load_street_data()
        street = random.choice(streets) if streets else "Main Street"

        # Get random house number
        house_numbers = self._data_loader.load_house_numbers()
        house_number = random.choice(house_numbers) if house_numbers else "123"

        # Get random city data
        city_data = self._data_loader.city_loader.get_random_city()

        # Get country data
        country_data = self._data_loader.country_loader.get_country_by_iso_code(self._country_code)
        if not country_data:
            country_data = self._data_loader.country_loader.get_country_by_iso_code("US")

        # Get continent
        continent = self._data_loader.country_loader.get_continent_for_country(self._country_code)

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
            "country_code": self._country_code,
            "continent": continent,
            "latitude": latitude,
            "longitude": longitude,
            "phone": self._generate_phone_number(),
            "mobile_phone": self._generate_mobile_number(),
            "fax": self._generate_phone_number(),
        }

    def _generate_phone_number(self) -> str:
        """Generate a random phone number based on country code.

        Returns:
            A phone number string.
        """
        if self._country_code == "US":
            area_code = random.randint(200, 999)
            prefix = random.randint(200, 999)
            line = random.randint(1000, 9999)
            return f"+1 ({area_code}) {prefix}-{line}"
        elif self._country_code == "GB":
            area_code = random.randint(1000, 9999)
            number = random.randint(100000, 999999)
            return f"+44 {area_code} {number}"
        elif self._country_code == "DE":
            area_code = random.randint(10, 999)
            number = random.randint(1000000, 9999999)
            return f"+49 {area_code} {number}"
        elif self._country_code == "FR":
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
        if self._country_code == "US":
            area_code = random.randint(200, 999)
            prefix = random.randint(200, 999)
            line = random.randint(1000, 9999)
            return f"+1 ({area_code}) {prefix}-{line}"
        elif self._country_code == "GB":
            prefix = random.choice(["7700", "7800", "7900"])
            number = random.randint(100000, 999999)
            return f"+44 {prefix} {number}"
        elif self._country_code == "DE":
            prefix = random.choice(["151", "152", "157", "160", "170", "171", "175"])
            number = random.randint(1000000, 9999999)
            return f"+49 {prefix} {number}"
        elif self._country_code == "FR":
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