# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import random

from datamimic_ce.domains.common.generators.city_generator import CityGenerator
from datamimic_ce.domains.common.generators.country_generator import CountryGenerator
from datamimic_ce.domains.common.literal_generators.company_name_generator import CompanyNameGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.domains.common.literal_generators.street_name_generator import StreetNameGenerator
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator


class AddressGenerator(BaseDomainGenerator):
    """Generator for address data.

    This class generates random address data using the data from datasets.
    """

    def __init__(self, dataset: str | None = None, rng: random.Random | None = None):
        """Initialize the AddressGenerator.

        Args:
            dataset: The dataset to use for generating addresses.
        """
        self._dataset = (dataset or "US").upper()  #  keep dataset uppercase so dependent generators reuse data files
        self._rng: random.Random = rng or random.Random()

        # Init sub-generators
        self._city_generator = CityGenerator(dataset=self._dataset, rng=self._rng)
        self._country_generator = CountryGenerator(dataset=self._dataset, rng=self._rng)
        self._phone_number_generator = PhoneNumberGenerator(dataset=self._dataset, rng=self._rng)
        self._company_name_generator = CompanyNameGenerator(rng=self._rng)
        # Lazy initialization of street name generator
        self._street_name_generator = StreetNameGenerator(dataset=self._dataset, rng=self._rng)

    @property
    def dataset(self) -> str:
        """Get the dataset.

        Returns:
            The dataset.
        """
        return self._dataset

    @property
    def rng(self) -> random.Random:
        return self._rng

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

    @property
    def company_name_generator(self) -> CompanyNameGenerator:
        """Get the company name generator.

        Returns:
            The company name generator.
        """
        return self._company_name_generator

    @property
    def street_name_generator(self) -> StreetNameGenerator:
        """Get the street name generator.

        Returns:
            The street name generator.
        """
        return self._street_name_generator
