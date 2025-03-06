# # DATAMIMIC
# # Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# # This software is licensed under the MIT License.
# # See LICENSE file for the full text of the license.
# # For questions and support, contact: info@rapiddweller.com

# import time

# from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
# from datamimic_ce.domains.common.models.address import Address


# class AddressService:
#     """Service for managing address data.

#     This class provides methods for creating, retrieving, and managing address data.
#     """

#     def __init__(self):
#         """Initialize the AddressService."""
#         self._generators: dict[str, AddressGenerator] = {}
#         self._default_country_code = "US"


#     def set_default_country_code(self, country_code: str) -> None:
#         """Set the default country code for generating addresses.

#         Args:
#             country_code: The country code to use.
#         """
#         self._default_country_code = country_code.upper()

#     def _get_generator(self, country_code: str) -> AddressGenerator:
#         """Get or create a generator for the specified country code.

#         Args:
#             country_code: The country code to use.

#         Returns:
#             An AddressGenerator for the specified country code.
#         """
#         if country_code not in self._generators:
#             self._generators[country_code] = AddressGenerator(country_code=country_code)
#         return self._generators[country_code]


#     def create_address(self, country_code: str | None = None) -> Address:
#         """Create a new address.

#         Args:
#             country_code: The country code to use for generating the address.

#         Returns:
#             A new Address object.
#         """
#         country_code = country_code.upper() if country_code else self._default_country_code

#         # Get or create generator for the country code
#         generator = self._get_generator(country_code)

#         # Generate a new address
#         address = generator.generate()

#         return address

#     def create_addresses_batch(self, count: int = 10, country_code: str | None = None) -> list[Address]:
#         """Create a batch of addresses.

#         Args:
#             count: The number of addresses to create.
#             country_code: The country code to use for generating the addresses.

#         Returns:
#             A list of Address objects.
#         """
#         country_code = country_code.upper() if country_code else self._default_country_code

#         # Get or create generator for the country code
#         generator = self._get_generator(country_code)

#         # Generate a batch of addresses
#         addresses = generator.generate_batch(count)

#         return addresses
    