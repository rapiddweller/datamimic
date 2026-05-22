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
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field
from datamimic_ce.domains.insurance.generators.insurance_company_generator import InsuranceCompanyGenerator
from datamimic_ce.domains.insurance.models.insurance_company import InsuranceCompany

INSURANCE_COMPANY_SCHEMA = EntitySchema(
    "InsuranceCompany",
    (
        field("id", str, "Unique company identifier."),
        field("name", str, "Company name."),
        field("code", str, "Company code."),
        field("founded_year", str, "Year the company was founded."),
        field("headquarters", str, "Headquarters location."),
        field("website", str, "Website URL."),
    ),
)


class InsuranceCompanyService(BaseDomainService[InsuranceCompany]):
    """Service for generating and managing insurance companies."""

    def __init__(self, dataset: str | None = None, rng: Random | None = None):
        super().__init__(InsuranceCompanyGenerator(dataset=dataset, rng=rng), InsuranceCompany)

    DATASET_PATTERNS = ("insurance/companies_{CC}.csv",)

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return INSURANCE_COMPANY_SCHEMA.fields
