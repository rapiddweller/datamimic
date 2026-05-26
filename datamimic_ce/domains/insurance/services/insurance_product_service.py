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
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field
from datamimic_ce.domains.insurance.generators.insurance_product_generator import InsuranceProductGenerator
from datamimic_ce.domains.insurance.models.insurance_product import InsuranceProduct

INSURANCE_PRODUCT_SCHEMA = EntitySchema(
    "InsuranceProduct",
    (
        field("id", str, "Unique product identifier."),
        field("type", str, "Product type."),
        field("code", str, "Product code."),
        field("description", str, "Product description."),
        field("coverages", list, "Coverage entries for the product."),
    ),
)


class InsuranceProductService(BaseDomainService[InsuranceProduct]):
    """Service for generating and managing insurance products."""

    def __init__(self, dataset: str | None = None, rng: Random | None = None):
        """Initialize the insurance product service.

        Args:
            dataset: The country code (e.g., "US", "DE") to use for data generation.
            rng: Optional seeded random instance for deterministic output.
        """
        super().__init__(InsuranceProductGenerator(dataset=dataset, rng=rng), InsuranceProduct)

    DATASET_PATTERNS = (
        "insurance/products_{CC}.csv",
        "insurance/product/coverage_counts_{CC}.csv",
    )

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return INSURANCE_PRODUCT_SCHEMA.fields
