# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance data generators.

This module provides generator classes for insurance-related data.
"""

import json
import uuid
from typing import Any

from datamimic_ce.domains.insurance.services.insurance_company_service import InsuranceCompanyService
from datamimic_ce.domains.insurance.services.insurance_policy_service import InsurancePolicyService
from datamimic_ce.domains.insurance.services.insurance_product_service import InsuranceProductService


class InsuranceCompanyGenerator(Generator):
    """Generator for insurance company data."""

    def __init__(self, dataset: str = "US", **kwargs):
        """Initialize the insurance company generator.

        Args:
            dataset: The country code to use for data generation
            **kwargs: Additional arguments to pass to the generator
        """
        super().__init__(**kwargs)
        self.service = InsuranceCompanyService(dataset=dataset)

    def generate(self) -> dict[str, Any]:
        """Generate an insurance company.

        Returns:
            A dictionary containing insurance company data
        """
        company = self.service.generate_insurance_company()
        return company.dict()


class InsuranceProductGenerator(Generator):
    """Generator for insurance product data."""

    def __init__(self, dataset: str = "US", include_coverages: bool = True, **kwargs):
        """Initialize the insurance product generator.

        Args:
            dataset: The country code to use for data generation
            include_coverages: Whether to include coverages in the generated products
            **kwargs: Additional arguments to pass to the generator
        """
        super().__init__(**kwargs)
        self.service = InsuranceProductService(dataset=dataset)
        self.include_coverages = include_coverages

    def generate(self) -> dict[str, Any]:
        """Generate an insurance product.

        Returns:
            A dictionary containing insurance product data
        """
        product = self.service.generate_insurance_product(include_coverages=self.include_coverages)
        return product.dict()


class InsurancePolicyGenerator(Generator):
    """Generator for insurance policy data."""

    def __init__(self, dataset: str = "US", **kwargs):
        """Initialize the insurance policy generator.

        Args:
            dataset: The country code to use for data generation
            **kwargs: Additional arguments to pass to the generator
        """
        super().__init__(**kwargs)
        self.service = InsurancePolicyService(dataset=dataset)

    def generate(self) -> dict[str, Any]:
        """Generate an insurance policy.

        Returns:
            A dictionary containing insurance policy data
        """
        policy = self.service.generate_insurance_policy()
        # Convert the policy to a dictionary with all nested objects
        return json.loads(policy.json())


class InsuranceDataGenerator(Generator):
    """Generator for comprehensive insurance data including companies, products, and policies."""

    def __init__(
        self,
        dataset: str = "US",
        include_companies: bool = True,
        include_products: bool = True,
        include_policies: bool = True,
        num_companies: int = 1,
        num_products: int = 1,
        num_policies: int = 1,
        **kwargs,
    ):
        """Initialize the insurance data generator.

        Args:
            dataset: The country code to use for data generation
            include_companies: Whether to include companies in the generated data
            include_products: Whether to include products in the generated data
            include_policies: Whether to include policies in the generated data
            num_companies: The number of companies to generate
            num_products: The number of products to generate
            num_policies: The number of policies to generate
            **kwargs: Additional arguments to pass to the generator
        """
        super().__init__(**kwargs)
        self.dataset = dataset
        self.include_companies = include_companies
        self.include_products = include_products
        self.include_policies = include_policies
        self.num_companies = num_companies
        self.num_products = num_products
        self.num_policies = num_policies
        self.company_service = InsuranceCompanyService(dataset=dataset)
        self.product_service = InsuranceProductService(dataset=dataset)
        self.policy_service = InsurancePolicyService(dataset=dataset)

    def generate(self) -> dict[str, Any]:
        """Generate comprehensive insurance data.

        Returns:
            A dictionary containing insurance data including companies, products, and policies
        """
        result = {
            "id": str(uuid.uuid4()),
            "dataset": self.dataset,
        }

        # Generate companies if requested
        if self.include_companies:
            companies = self.company_service.generate_insurance_companies(count=self.num_companies)
            result["companies"] = [json.loads(company.json()) for company in companies]
            # Use the first company for products if available
            company = companies[0] if companies else None
        else:
            company = None

        # Generate products if requested
        if self.include_products:
            products = self.product_service.generate_insurance_products(count=self.num_products, include_coverages=True)
            result["products"] = [json.loads(product.json()) for product in products]
            # Use the first product for policies if available
            product = products[0] if products else None
        else:
            product = None

        # Generate policies if requested
        if self.include_policies:
            policies = []
            for _ in range(self.num_policies):
                # Use a different company and product for each policy if available
                policy = self.policy_service.generate_insurance_policy(
                    company=company,
                    product=product,
                )
                policies.append(policy)
            result["policies"] = [json.loads(policy.json()) for policy in policies]

        return result
