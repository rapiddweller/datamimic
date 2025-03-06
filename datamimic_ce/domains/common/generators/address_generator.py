# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.domains.common.data_loaders.address_loader import AddressDataLoader
from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domain_core.domain_generator import DomainGenerator


class AddressGenerator(DomainGenerator[Address]):
    """Generator for address data.

    This class generates random address data using the AddressDataLoader.
    """

    def __init__(self, country_code: str = "US"):
        """Initialize the AddressGenerator.

        Args:
            country_code: The country code to use for generating addresses.
        """
        super().__init__(AddressDataLoader(country_code=country_code), Address)
        self._country_code = country_code.upper()
