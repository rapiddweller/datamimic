# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance Policy Service.

This module provides service functions for generating and managing insurance policies.
"""

from datetime import date
from random import Random

from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field
from datamimic_ce.domains.insurance.generators.insurance_policy_generator import InsurancePolicyGenerator
from datamimic_ce.domains.insurance.models.insurance_policy import InsurancePolicy

INSURANCE_POLICY_SCHEMA = EntitySchema(
    "InsurancePolicy",
    (
        field("id", str, "Unique policy identifier."),
        field("company", dict, "Issuing insurance company."),
        field("product", dict, "Insured product."),
        field("policy_holder", dict, "Policy holder details."),
        field("coverages", list, "Coverage entries on the policy."),
        field("premium", float, "Premium amount."),
        field("premium_frequency", str, "Premium payment frequency."),
        field("start_date", date, "Policy start date."),
        field("end_date", date, "Policy end date."),
        field("status", str, "Policy status."),
        field("created_date", date, "Policy creation date."),
    ),
)


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
            demographic_config: Optional demographic configuration.
            rng: Optional seeded random instance for deterministic output.
        """
        super().__init__(
            InsurancePolicyGenerator(
                dataset=dataset,
                demographic_config=demographic_config,
                rng=rng,
            ),
            InsurancePolicy,
        )

    DATASET_PATTERNS = (
        "insurance/policy/premium_buckets_{CC}.csv",
        "insurance/policy/premium_frequencies_{CC}.csv",
        "insurance/policy/statuses_{CC}.csv",
    )

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return INSURANCE_POLICY_SCHEMA.fields
