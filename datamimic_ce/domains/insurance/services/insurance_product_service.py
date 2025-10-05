# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance Product Service.

This module provides service functions for generating and managing insurance products.
"""

from random import Random

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.insurance.generators.insurance_product_generator import InsuranceProductGenerator
from datamimic_ce.domains.insurance.models.insurance_product import InsuranceProduct


class InsuranceProductService(BaseDomainService[InsuranceProduct]):
    """Service for generating and managing insurance products."""

    def __init__(self, dataset: str | None = None, rng: Random | None = None):
        """Initialize the insurance product service.

        Args:
            dataset: The country code (e.g., "US", "DE") to use for data generation.
        """
        super().__init__(InsuranceProductGenerator(dataset=dataset, rng=rng), InsuranceProduct)

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        return compute_supported_datasets(
            [
                "insurance/products_{CC}.csv",
                "insurance/product/coverage_counts_{CC}.csv",
            ],
            start=Path(__file__),
        )
