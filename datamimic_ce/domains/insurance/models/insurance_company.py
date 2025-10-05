# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance Company model.

This module defines the insurance company model for the insurance domain.
"""

from typing import Any

from datamimic_ce.domains.domain_core import BaseEntity
from datamimic_ce.domains.domain_core.property_cache import property_cache
from datamimic_ce.domains.insurance.generators.insurance_company_generator import InsuranceCompanyGenerator


class InsuranceCompany(BaseEntity):
    """Insurance company information."""

    def __init__(self, insurance_company_generator: InsuranceCompanyGenerator):
        super().__init__()
        self._insurance_company_generator = insurance_company_generator

    @property
    @property_cache
    def id(self) -> str:
        rng = self._insurance_company_generator.rng
        alphabet = "0123456789abcdef"
        sections = [8, 4, 4, 4, 12]
        parts = ["".join(rng.choice(alphabet) for _ in range(length)) for length in sections]
        return "-".join(parts)

    @property
    @property_cache
    def company_data(self) -> dict[str, Any]:
        return self._insurance_company_generator.get_random_company()

    @property
    @property_cache
    def name(self) -> str:
        return self.company_data["name"]

    @property
    @property_cache
    def code(self) -> str:
        return self.company_data["code"]

    @property
    @property_cache
    def founded_year(self) -> str:
        return self.company_data["founded_year"]

    @property
    @property_cache
    def headquarters(self) -> str:
        return self.company_data["headquarters"]

    @property
    @property_cache
    def website(self) -> str:
        website = str(self.company_data["website"])
        if website and not website.startswith("http"):
            return f"https://{website.lstrip(':/')}"
        return website

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "founded_year": self.founded_year,
            "headquarters": self.headquarters,
            "website": self.website,
        }
