from typing import Any

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.insurance.generators.insurance_coverage_generator import InsuranceCoverageGenerator


class InsuranceCoverage(BaseEntity):
    """Insurance coverage information."""

    def __init__(self, insurance_coverage_generator: InsuranceCoverageGenerator):
        super().__init__(insurance_coverage_generator)
        self.insurance_coverage_generator = insurance_coverage_generator

    @property
    @property_cache
    def coverage_data(self) -> dict[str, Any]:
        return self.insurance_coverage_generator.get_random_coverage()

    @property
    @property_cache
    def name(self) -> str:
        return self.coverage_data["name"]

    @property
    @property_cache
    def code(self) -> str:
        return self.coverage_data["code"]

    @property
    @property_cache
    def product_code(self) -> str:
        return self.coverage_data["product_code"]

    @property
    @property_cache
    def description(self) -> str:
        return self.coverage_data["description"]

    @property
    @property_cache
    def min_coverage(self) -> str:
        return self.coverage_data["min_coverage"]

    @property
    @property_cache
    def max_coverage(self) -> str:
        return self.coverage_data["max_coverage"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "code": self.code,
            "product_code": self.product_code,
            "description": self.description,
            "min_coverage": self.min_coverage,
            "max_coverage": self.max_coverage,
        }
