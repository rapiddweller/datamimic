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
        return Address(self._data_loader)

    def generate_batch(self, count: int = 10) -> list[Address]:
        """Generate a batch of addresses.

        Args:
            count: The number of addresses to generate.

        Returns:
            A list of Address objects.
        """
        return [self.generate() for _ in range(count)]
