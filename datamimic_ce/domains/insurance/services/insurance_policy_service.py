# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance Policy Service.

This module provides service functions for generating and managing insurance policies.
"""

from random import Random

from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.insurance.generators.insurance_policy_generator import InsurancePolicyGenerator
from datamimic_ce.domains.insurance.models.insurance_policy import InsurancePolicy


class InsurancePolicyService(BaseDomainService[InsurancePolicy]):
    """Service for generating and managing insurance policies."""

    def __init__(
        self,
        dataset: str | None = None,
        demographic_config: DemographicConfig | None = None,
        rng: Random | None = None,
    ):
        """Initialize the insurance policy service.

        Args:
            dataset: The country code (e.g., "US", "DE") to use for data generation.
        """
        import random as _r

        super().__init__(
            InsurancePolicyGenerator(dataset=dataset, demographic_config=demographic_config, rng=rng or _r.Random()),
            InsurancePolicy,
        )

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        patterns = [
            "insurance/policy/premium_buckets_{CC}.csv",
            "insurance/policy/premium_frequencies_{CC}.csv",
            "insurance/policy/statuses_{CC}.csv",
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
