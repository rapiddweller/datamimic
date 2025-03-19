import datetime
import pytest

from datamimic_ce.domains.common.models.person import Person
from datamimic_ce.domains.insurance.models.insurance_company import InsuranceCompany
from datamimic_ce.domains.insurance.models.insurance_policy import InsurancePolicy
from datamimic_ce.domains.insurance.models.insurance_product import InsuranceProduct
from datamimic_ce.domains.insurance.services.insurance_policy_service import InsurancePolicyService

class TestInsurancePolicy:
    _supported_datasets = ["US", "DE"]
    def _test_single_insurance_policy(self, insurance_policy: InsurancePolicy):
        assert isinstance(insurance_policy, InsurancePolicy)    
        assert isinstance(insurance_policy.id, str)
        assert isinstance(insurance_policy.company, InsuranceCompany)
        assert isinstance(insurance_policy.product, InsuranceProduct)
        assert isinstance(insurance_policy.policy_holder, Person)
        assert isinstance(insurance_policy.coverages, list)
        assert isinstance(insurance_policy.premium, float)
        assert isinstance(insurance_policy.premium_frequency, str)
        assert isinstance(insurance_policy.start_date, datetime.date)
        assert isinstance(insurance_policy.end_date, datetime.date) 
        assert isinstance(insurance_policy.status, str)
        assert isinstance(insurance_policy.created_date, datetime.date)

        assert insurance_policy.id is not None    
        assert insurance_policy.company is not None
        assert insurance_policy.product is not None
        assert insurance_policy.policy_holder is not None
        assert insurance_policy.coverages is not None
        assert insurance_policy.premium is not None
        assert insurance_policy.premium_frequency is not None
        assert insurance_policy.start_date is not None
        assert insurance_policy.end_date is not None
        assert insurance_policy.status is not None
        assert insurance_policy.created_date is not None

        assert insurance_policy.id != ""
        assert insurance_policy.start_date != ""
        assert insurance_policy.end_date != ""
        assert insurance_policy.status != ""
        assert insurance_policy.created_date != ""


    def test_generate_single_insurance_policy(self):
        insurance_policy_service = InsurancePolicyService()
        insurance_policy = insurance_policy_service.generate()
        self._test_single_insurance_policy(insurance_policy)

    def test_generate_multiple_insurance_policies(self):
        insurance_policy_service = InsurancePolicyService()
        insurance_policies = insurance_policy_service.generate_batch(10)
        assert len(insurance_policies) == 10
        for insurance_policy in insurance_policies:
            self._test_single_insurance_policy(insurance_policy)

    def test_insurance_policy_property_cache(self):       
        insurance_policy_service = InsurancePolicyService()
        insurance_policy = insurance_policy_service.generate()
        assert insurance_policy is not None
        assert insurance_policy.id == insurance_policy.id
        assert insurance_policy.company == insurance_policy.company
        assert insurance_policy.product == insurance_policy.product
        assert insurance_policy.policy_holder == insurance_policy.policy_holder
        assert insurance_policy.premium == insurance_policy.premium
        assert insurance_policy.premium_frequency == insurance_policy.premium_frequency
        assert insurance_policy.start_date == insurance_policy.start_date
        assert insurance_policy.end_date == insurance_policy.end_date
        assert insurance_policy.status == insurance_policy.status
        assert insurance_policy.created_date == insurance_policy.created_date

    @pytest.mark.flaky(reruns=10)
    def test_two_different_entities(self):
        insurance_policy_service = InsurancePolicyService()
        insurance_policy1 = insurance_policy_service.generate()
        insurance_policy2 = insurance_policy_service.generate() 
        assert insurance_policy1.id != insurance_policy2.id
        assert insurance_policy1.company != insurance_policy2.company
        assert insurance_policy1.product != insurance_policy2.product
        assert insurance_policy1.policy_holder != insurance_policy2.policy_holder
        assert insurance_policy1.premium != insurance_policy2.premium
        assert insurance_policy1.start_date != insurance_policy2.start_date
        assert insurance_policy1.end_date != insurance_policy2.end_date
        assert insurance_policy1.status != insurance_policy2.status
        assert insurance_policy1.created_date != insurance_policy2.created_date 

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        insurance_policy_service = InsurancePolicyService(dataset=dataset)
        insurance_policy = insurance_policy_service.generate()
        self._test_single_insurance_policy(insurance_policy)

    def test_not_supported_dataset(self):
        insurance_policy_service = InsurancePolicyService(dataset="FR")
        policy = insurance_policy_service.generate()
        with pytest.raises(FileNotFoundError):
            policy.to_dict()