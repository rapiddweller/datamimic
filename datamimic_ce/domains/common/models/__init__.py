# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Common domain models.

This package provides models for common domain entities.
"""

from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.common.models.city import City
from datamimic_ce.domains.common.models.country import Country
from datamimic_ce.domains.common.models.person import Person

__all__ = [
    "Person",
    "City",
    "Country",
    "Address",
]
