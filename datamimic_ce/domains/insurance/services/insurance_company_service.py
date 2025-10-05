# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance Company Service.

This module provides service functions for generating and managing insurance companies.
"""

from random import Random

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.insurance.generators.insurance_company_generator import InsuranceCompanyGenerator
from datamimic_ce.domains.insurance.models.insurance_company import InsuranceCompany


class InsuranceCompanyService(BaseDomainService[InsuranceCompany]):
    """Service for generating and managing insurance companies."""

    def __init__(self, dataset: str | None = None, rng: Random | None = None):
        super().__init__(InsuranceCompanyGenerator(dataset=dataset, rng=rng), InsuranceCompany)

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        return compute_supported_datasets(["insurance/companies_{CC}.csv"], start=Path(__file__))
