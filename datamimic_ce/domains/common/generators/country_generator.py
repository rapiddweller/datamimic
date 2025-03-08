# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.domains.common.data_loaders.country_loader import CountryDataLoader
from datamimic_ce.domains.common.models.country import Country
from datamimic_ce.generators.domain_generator import DomainGenerator


class CountryGenerator(DomainGenerator[Country]):
    """Generator for country-related attributes.
    
    Provides methods to generate country-related attributes such as
    ISO code, name, default language locale, phone code, and population.
    """
    def __init__(self, country_code: str = "US"):
        super().__init__(CountryDataLoader(country_code=country_code), Country)
        self._country_code = country_code
        