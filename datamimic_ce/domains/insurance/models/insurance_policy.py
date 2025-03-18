import datetime
import random
from typing import Any
import uuid
from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.common.models.person import Person
from datamimic_ce.domains.insurance.generators.insurance_policy_generator import InsurancePolicyGenerator
from datamimic_ce.domains.insurance.models.insurance_company import InsuranceCompany
from datamimic_ce.domains.insurance.models.insurance_coverage import InsuranceCoverage
from datamimic_ce.domains.insurance.models.insurance_product import InsuranceProduct            


class InsurancePolicy(BaseEntity):
    """Insurance policy information."""

    def __init__(self, insurance_policy_generator: InsurancePolicyGenerator):
        super().__init__()
        self.insurance_policy_generator = insurance_policy_generator
        
    @property
    @property_cache
    def id(self) -> str:
        return str(uuid.uuid4())
    
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
    
    @property
    @property_cache
    def coverages(self) -> list[InsuranceCoverage]:
        return [InsuranceCoverage(self.insurance_policy_generator.insurance_coverage_generator) for _ in range(random.randint(1, 3))]
    
    @property
    @property_cache
    def premium(self) -> float:
        return random.uniform(100, 1000)
    
    @property
    @property_cache
    def premium_frequency(self) -> str:
        return random.choice(["monthly", "quarterly", "yearly"])
    
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
        return random.choice(["active", "inactive", "cancelled"])   
    
    @property
    @property_cache
    def created_date(self) -> datetime:
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
    
