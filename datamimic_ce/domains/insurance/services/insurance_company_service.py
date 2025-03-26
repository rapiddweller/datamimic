# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance Company Service.

This module provides service functions for generating and managing insurance companies.
"""

from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.insurance.generators.insurance_company_generator import InsuranceCompanyGenerator
from datamimic_ce.domains.insurance.models.insurance_company import InsuranceCompany


class InsuranceCompanyService(BaseDomainService[InsuranceCompany]):
    """Service for generating and managing insurance companies."""

    def __init__(self, dataset: str | None = None):
        super().__init__(InsuranceCompanyGenerator(dataset), InsuranceCompany)
