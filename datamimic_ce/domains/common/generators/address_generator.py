# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.core.interfaces import Generator
from datamimic_ce.domains.common.data_loaders.address_loader import AddressDataLoader
from datamimic_ce.domains.common.models.address import Address


class AddressGenerator(Generator):
    """Generator for address data.

    This class generates random address data using the AddressDataLoader.
    """

    def __init__(self, country_code: str = "US", data_loader: AddressDataLoader = None):
        """Initialize the AddressGenerator.

        Args:
            country_code: The country code to use for generating addresses.
            data_loader: Optional data loader to use. If not provided, a new one will be created.
        """
        self._country_code = country_code.upper()
        self._data_loader = (
            data_loader if data_loader is not None else AddressDataLoader(country_code=self._country_code)
        )

    @property
    def country_code(self) -> str:
        """Get the country code.

        Returns:
            The country code.
        """
        return self._country_code

    def generate(self) -> Address:
        """Generate a random address.

        Returns:
            An Address object.
        """
        address_data = self._data_loader.get_random_address()
        return Address.create(address_data)

    def generate_batch(self, count: int = 10) -> list[Address]:
        """Generate a batch of addresses.

        Args:
            count: The number of addresses to generate.

        Returns:
            A list of Address objects.
        """
        addresses_data = self._data_loader.get_addresses_batch(count)
        return [Address.create(address_data) for address_data in addresses_data]

    def set_country_code(self, country_code: str) -> None:
        """Set the country code for generating addresses.

        Args:
            country_code: The country code to use.
        """
        self._country_code = country_code.upper()
        self._data_loader = AddressDataLoader(country_code=self._country_code)
