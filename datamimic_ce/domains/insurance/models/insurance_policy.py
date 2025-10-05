import datetime
from pathlib import Path
from typing import Any

from datamimic_ce.domains.common.models.person import Person
from datamimic_ce.domains.domain_core import BaseEntity
from datamimic_ce.domains.domain_core.property_cache import property_cache
from datamimic_ce.domains.insurance.generators.insurance_policy_generator import InsurancePolicyGenerator
from datamimic_ce.domains.insurance.models.insurance_company import InsuranceCompany
from datamimic_ce.domains.insurance.models.insurance_coverage import InsuranceCoverage
from datamimic_ce.domains.insurance.models.insurance_product import InsuranceProduct
from datamimic_ce.domains.utils.rng_uuid import uuid4_from_random


class InsurancePolicy(BaseEntity):
    """Insurance policy information."""

    def __init__(self, insurance_policy_generator: InsurancePolicyGenerator):
        super().__init__()
        self.insurance_policy_generator = insurance_policy_generator

    @property
    @property_cache
    def id(self) -> str:
        return uuid4_from_random(self.insurance_policy_generator.rng)

    @property
    @property_cache
    def company(self) -> InsuranceCompany:
        return InsuranceCompany(self.insurance_policy_generator.insurance_company_generator)

    @property
    @property_cache
    def product(self) -> InsuranceProduct:
        return InsuranceProduct(self.insurance_policy_generator.insurance_product_generator)

    @property
    @property_cache
    def policy_holder(self) -> Person:
        return Person(self.insurance_policy_generator.person_generator)

    @policy_holder.setter
    def policy_holder(self, value: Person) -> None:
        """Set the policy holder.

        Args:
            value: The person to set as the policy holder.
        """
        self._field_cache["policy_holder"] = value

    @property
    @property_cache
    def coverages(self) -> list[InsuranceCoverage]:
        rng = self.insurance_policy_generator.rng
        return [
            InsuranceCoverage(self.insurance_policy_generator.insurance_coverage_generator)
            for _ in range(rng.randint(1, 3))
        ]

    @property
    @property_cache
    def premium(self) -> float:
        #  Delegate dataset I/O to generator helper per SOC
        return self.insurance_policy_generator.pick_premium_amount(start_path=Path(__file__))

    @premium.setter
    def premium(self, value: float) -> None:
        """Set the premium amount.

        Args:
            value: The premium amount to set.
        """
        self._field_cache["premium"] = value

    @property
    @property_cache
    def premium_frequency(self) -> str:
        #  Delegate dataset I/O to generator helper per SOC
        return self.insurance_policy_generator.pick_premium_frequency(start_path=Path(__file__))

    @property
    @property_cache
    def start_date(self) -> datetime.date:
        return self.insurance_policy_generator.datetime_generator.generate_date()

    @property
    @property_cache
    def end_date(self) -> datetime.date:
        return self.insurance_policy_generator.datetime_generator.generate_date()

    @property
    @property_cache
    def status(self) -> str:
        #  Delegate dataset I/O to generator helper per SOC
        return self.insurance_policy_generator.pick_status(start_path=Path(__file__))

    @status.setter
    def status(self, value: str) -> None:
        """Set the policy status.

        Args:
            value: The status to set.
        """
        self._field_cache["status"] = value

    @property
    @property_cache
    def created_date(self) -> datetime.datetime:
        return self.insurance_policy_generator.datetime_generator.generate_date()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "company": self.company.to_dict(),
            "product": self.product.to_dict(),
            "policy_holder": self.policy_holder.to_dict(),
            "coverages": [coverage.to_dict() for coverage in self.coverages],
            "premium": self.premium,
            "premium_frequency": self.premium_frequency,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status,
            "created_date": self.created_date,
        }
