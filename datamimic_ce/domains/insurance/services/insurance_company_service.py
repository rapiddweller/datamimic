# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance Company Service.

This module provides service functions for generating and managing insurance companies.
"""

import random
import uuid

from datamimic_ce.domains.insurance.data_loaders.insurance_loader import InsuranceDataLoader
from datamimic_ce.domains.insurance.models.insurance_company import InsuranceCompany


class InsuranceCompanyService:
    """Service for generating and managing insurance companies."""

    def __init__(self, dataset: str = "US"):
        """Initialize the insurance company service.

        Args:
            dataset: The country code (e.g., "US", "DE") to use for data generation.
        """
        self.dataset = dataset
        # Cache the loaded companies
        self._companies_by_weight = InsuranceDataLoader._load_companies_by_weight(dataset)

    def generate_insurance_company(self) -> InsuranceCompany:
        """Generate a random insurance company based on weighted probabilities.

        Returns:
            An InsuranceCompany object with randomly generated data.
        """
        if not self._companies_by_weight:
            raise ValueError(f"No insurance companies found for dataset {self.dataset}")

        # Select a company based on weights
        companies = [c[0] for c in self._companies_by_weight]
        weights = [c[1] for c in self._companies_by_weight]

        selected_company = random.choices(companies, weights=weights, k=1)[0]

        # Create and return an InsuranceCompany object
        return InsuranceCompany(
            id=str(uuid.uuid4()),
            name=selected_company.get("name", "Unknown Company"),
            code=selected_company.get("code", ""),
            founded_year=selected_company.get("founded_year", ""),
            headquarters=selected_company.get("headquarters", ""),
            website=selected_company.get("website", ""),
            logo_url=None,  # Logo URL is not available in the data
        )

    def generate_insurance_companies(self, count: int = 1) -> list[InsuranceCompany]:
        """Generate multiple random insurance companies.

        Args:
            count: The number of insurance companies to generate

        Returns:
            A list of InsuranceCompany objects with randomly generated data.
        """
        return [self.generate_insurance_company() for _ in range(count)]
