# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance Product Service.

This module provides service functions for generating and managing insurance products.
"""

from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.insurance.generators.insurance_product_generator import InsuranceProductGenerator
from datamimic_ce.domains.insurance.models.insurance_product import InsuranceProduct


class InsuranceProductService(BaseDomainService[InsuranceProduct]):
    """Service for generating and managing insurance products."""

    def __init__(self, dataset: str | None = None):
        """Initialize the insurance product service.

        Args:
            dataset: The country code (e.g., "US", "DE") to use for data generation.
        """
        super().__init__(InsuranceProductGenerator(dataset=dataset), InsuranceProduct)
