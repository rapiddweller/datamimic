# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com



from datamimic_ce.domains.common.data_loaders.company_loader import CompanyLoader
from datamimic_ce.domains.common.models.company import Company
from datamimic_ce.generators.domain_generator import DomainGenerator


class CompanyGenerator(DomainGenerator[Company]):
    """Generator for company-related attributes.
    
    Provides methods to generate company-related attributes such as
    company names, emails, URLs, and other information.
    """
    
    def __init__(self, country_code: str = "US"):
        super().__init__(CompanyLoader(country_code=country_code), Company)
        self._country_code = country_code
        