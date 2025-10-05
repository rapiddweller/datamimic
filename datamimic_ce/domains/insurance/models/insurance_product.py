# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance Product model.

This module defines the insurance product model for the insurance domain.
"""

from pathlib import Path
from typing import Any

from datamimic_ce.domains.domain_core import BaseEntity
from datamimic_ce.domains.domain_core.property_cache import property_cache
from datamimic_ce.domains.insurance.generators.insurance_product_generator import InsuranceProductGenerator
from datamimic_ce.domains.insurance.models.insurance_coverage import InsuranceCoverage
from datamimic_ce.domains.utils.rng_uuid import uuid4_from_random


class InsuranceProduct(BaseEntity):
    """Insurance product information."""

    def __init__(self, insurance_product_generator: InsuranceProductGenerator):
        super().__init__()
        self._insurance_product_generator = insurance_product_generator

    @property
    @property_cache
    def id(self) -> str:
        return uuid4_from_random(self._insurance_product_generator.rng)

    @property
    @property_cache
    def product_data(self) -> dict[str, Any]:
        return self._insurance_product_generator.get_random_product()

    @property
    @property_cache
    def type(self) -> str:
        return self.product_data["type"]

    @property
    @property_cache
    def code(self) -> str:
        return self.product_data["code"]

    @property
    @property_cache
    def description(self) -> str:
        return self.product_data["description"]

    @property
    @property_cache
    def coverages(self) -> list[InsuranceCoverage]:
        #  Delegate dataset I/O to generator helper per SOC
        count = self._insurance_product_generator.pick_coverage_count(start_path=Path(__file__))
        return [
            InsuranceCoverage(self._insurance_product_generator.insurance_coverage_generator)
            for _ in range(max(1, count))
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "code": self.code,
            "description": self.description,
            "coverages": [coverage.to_dict() for coverage in self.coverages],
        }
