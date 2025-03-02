# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Common domain data loaders.

This package provides data loaders for common domain entities.
"""

from datamimic_ce.domains.common.data_loaders.address_loader import AddressDataLoader
from datamimic_ce.domains.common.data_loaders.city_loader import CityDataLoader
from datamimic_ce.domains.common.data_loaders.company_loader import CompanyLoader
from datamimic_ce.domains.common.data_loaders.country_loader import CountryDataLoader
from datamimic_ce.domains.common.data_loaders.phone_number_loader import PhoneNumberDataLoader

__all__ = [
    "PhoneNumberDataLoader",
    "CityDataLoader",
    "CountryDataLoader",
    "AddressDataLoader",
    "CompanyLoader",
]
