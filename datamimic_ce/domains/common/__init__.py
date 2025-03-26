# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Common domain module.

This module provides entities, data loaders, generators, and services for common entities
such as address, city, company, country, crm, digital_wallet, person, and product.
"""

from datamimic_ce.domains.common import generators, models, services

__all__ = [
    "models",
    "generators",
    "services",
]
