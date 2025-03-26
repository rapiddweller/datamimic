# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Administration office generator utilities.

This module provides utility functions for generating administration office data.
"""

from typing import TypeVar

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.common.literal_generators.family_name_generator import FamilyNameGenerator
from datamimic_ce.domains.common.literal_generators.given_name_generator import GivenNameGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator

T = TypeVar("T")  # Define a type variable for generic typing


class AdministrationOfficeGenerator(BaseDomainGenerator):
    """Generator for administration office data."""

    def __init__(self, dataset: str | None = None):
        """Initialize the administration office generator.

        Args:
            dataset: The country code to use for data generation
        """
        self._dataset = dataset or "US"
        self._address_generator = AddressGenerator(dataset=self._dataset)
        self._phone_number_generator = PhoneNumberGenerator(dataset=self._dataset)
        self._family_name_generator = FamilyNameGenerator(dataset=self._dataset)
        self._given_name_generator = GivenNameGenerator(dataset=self._dataset)

    @property
    def address_generator(self) -> AddressGenerator:
        return self._address_generator

    @property
    def phone_number_generator(self) -> PhoneNumberGenerator:
        return self._phone_number_generator

    @property
    def family_name_generator(self) -> FamilyNameGenerator:
        return self._family_name_generator

    @property
    def given_name_generator(self) -> GivenNameGenerator:
        return self._given_name_generator
