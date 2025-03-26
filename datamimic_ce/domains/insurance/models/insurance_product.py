# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance Product model.

This module defines the insurance product model for the insurance domain.
"""

import random
import uuid
from typing import Any

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.insurance.generators.insurance_product_generator import InsuranceProductGenerator
from datamimic_ce.domains.insurance.models.insurance_coverage import InsuranceCoverage


class InsuranceProduct(BaseEntity):
    """Insurance product information."""

    def __init__(self, insurance_product_generator: InsuranceProductGenerator):
        super().__init__()
        self._insurance_product_generator = insurance_product_generator

    @property
    @property_cache
    def id(self) -> str:
        return str(uuid.uuid4())

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
        return [
            InsuranceCoverage(self._insurance_product_generator.insurance_coverage_generator)
            for _ in range(random.randint(1, 3))
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "code": self.code,
            "description": self.description,
            "coverages": [coverage.to_dict() for coverage in self.coverages],
        }
