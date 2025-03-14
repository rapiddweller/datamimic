# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance Product Service.

This module provides service functions for generating and managing insurance products.
"""

import random
import uuid

from datamimic_ce.domains.insurance.data_loaders.insurance_loader import InsuranceDataLoader
from datamimic_ce.domains.insurance.models.insurance_product import InsuranceCoverage, InsuranceProduct


class InsuranceProductService:
    """Service for generating and managing insurance products."""

    def __init__(self, dataset: str = "US"):
        """Initialize the insurance product service.

        Args:
            dataset: The country code (e.g., "US", "DE") to use for data generation.
        """
        self.dataset = dataset
        # Cache the loaded products
        self._products_by_weight = InsuranceDataLoader._load_products_by_weight(dataset)

    def generate_coverage(self, product_code: str) -> list[InsuranceCoverage]:
        """Generate coverages for a specific product.

        Args:
            product_code: The product code to generate coverages for

        Returns:
            A list of InsuranceCoverage objects for the product.
        """
        # Get coverages for the product
        coverages_by_weight = InsuranceDataLoader._load_coverages_by_weight(product_code, self.dataset)

        if not coverages_by_weight:
            return []

        result = []

        for coverage_tuple in coverages_by_weight:
            coverage_data = coverage_tuple[0]

            # Generate a random coverage amount within the min and max range
            min_coverage = coverage_data.get("min_coverage", 0)
            max_coverage = coverage_data.get("max_coverage", float("inf"))

            # Handle infinite coverage
            if max_coverage == float("inf"):
                if min_coverage > 0:
                    # For infinite max, use a range of 1x to 5x the minimum
                    coverage_amount = round(min_coverage * random.uniform(1.0, 5.0))
                else:
                    # Fallback to a reasonable range if min is 0
                    coverage_amount = round(random.uniform(10000, 1000000))
            else:
                # Normal case: range between min and max
                coverage_amount = round(random.uniform(min_coverage, max_coverage))

            coverage = InsuranceCoverage(
                id=str(uuid.uuid4()),
                name=coverage_data.get("name", "Unknown Coverage"),
                code=coverage_data.get("code", ""),
                description=coverage_data.get("description", ""),
                min_coverage=min_coverage,
                max_coverage=max_coverage,
            )

            result.append(coverage)

        return result

    def generate_insurance_product(self, include_coverages: bool = True) -> InsuranceProduct:
        """Generate a random insurance product based on weighted probabilities.

        Args:
            include_coverages: Whether to include coverages in the generated product

        Returns:
            An InsuranceProduct object with randomly generated data.
        """
        if not self._products_by_weight:
            raise ValueError(f"No insurance products found for dataset {self.dataset}")

        # Select a product based on weights
        products = [p[0] for p in self._products_by_weight]
        weights = [p[1] for p in self._products_by_weight]

        selected_product = random.choices(products, weights=weights, k=1)[0]
        product_code = selected_product.get("code", "")

        # Generate coverages if requested
        coverages = []
        if include_coverages and product_code:
            coverages = self.generate_coverage(product_code)

        # Create and return an InsuranceProduct object
        return InsuranceProduct(
            id=str(uuid.uuid4()),
            type=selected_product.get("type", "Unknown Product"),
            code=product_code,
            description=selected_product.get("description", ""),
            coverages=coverages,
        )

    def generate_insurance_products(self, count: int = 1, include_coverages: bool = True) -> list[InsuranceProduct]:
        """Generate multiple random insurance products.

        Args:
            count: The number of insurance products to generate
            include_coverages: Whether to include coverages in the generated products

        Returns:
            A list of InsuranceProduct objects with randomly generated data.
        """
        return [self.generate_insurance_product(include_coverages) for _ in range(count)]
