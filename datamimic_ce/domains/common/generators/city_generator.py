# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.domains.common.data_loaders.city_loader import CityDataLoader
from datamimic_ce.domains.common.models.city import City
from datamimic_ce.domain_core.domain_generator import DomainGenerator


class CityGenerator(DomainGenerator[City]):
    """Generator for city data.

    This class generates random city data using the CityDataLoader.
    """

    def __init__(self, country_code: str = "US"):
        """Initialize the CityGenerator.

        Args:
            country_code: The country code to use for generating cities.
        """
        super().__init__(CityDataLoader(country_code=country_code), City)
        self._country_code = country_code.upper()

