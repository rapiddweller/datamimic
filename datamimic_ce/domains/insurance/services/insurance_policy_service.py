# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance Policy Service.

This module provides service functions for generating and managing insurance policies.
"""

from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.insurance.generators.insurance_policy_generator import InsurancePolicyGenerator
from datamimic_ce.domains.insurance.models.insurance_policy import InsurancePolicy


class InsurancePolicyService(BaseDomainService[InsurancePolicy]):
    """Service for generating and managing insurance policies."""

    def __init__(self, dataset: str | None = None):
        """Initialize the insurance policy service.

        Args:
            dataset: The country code (e.g., "US", "DE") to use for data generation.
        """
        super().__init__(InsurancePolicyGenerator(dataset=dataset), InsurancePolicy)
