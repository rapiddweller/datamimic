# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Common domain services.

This package provides services for common domain entities.
"""

from datamimic_ce.domains.shared.services.address_service import AddressService
from datamimic_ce.domains.shared.services.city_service import CityService
from datamimic_ce.domains.shared.services.company_service import CompanyService
from datamimic_ce.domains.shared.services.country_service import CountryService
from datamimic_ce.domains.shared.services.person_service import PersonService

# Expose for dynamic import
__all__ = [
    "CityService",
    "CountryService",
    "AddressService",
    "PersonService",
    "CompanyService",
]
