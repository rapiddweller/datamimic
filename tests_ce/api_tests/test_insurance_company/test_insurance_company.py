import pytest
from datamimic_ce.domains.common.literal_generators.generator_util import GeneratorUtil
from datamimic_ce.domains.insurance.models.insurance_company import InsuranceCompany
from datamimic_ce.domains.insurance.services.insurance_company_service import InsuranceCompanyService


class TestInsuranceCompany:
    _supported_datasets = ["US", "DE"]
    def _test_single_insurance_company(self, insurance_company: InsuranceCompany):
        assert isinstance(insurance_company, InsuranceCompany)
        assert isinstance(insurance_company.id, str)
        assert isinstance(insurance_company.name, str)
        assert isinstance(insurance_company.code, str)
        assert isinstance(insurance_company.founded_year, str)
        assert isinstance(insurance_company.headquarters, str)
        assert isinstance(insurance_company.website, str)

        assert insurance_company.id is not None
        assert insurance_company.name is not None
        assert insurance_company.code is not None
        assert insurance_company.founded_year is not None
        assert insurance_company.headquarters is not None
        assert insurance_company.website is not None

        assert insurance_company.id != ""
        #  ensure consistent UUID format by validating via common utility
        assert GeneratorUtil.is_valid_uuid(insurance_company.id)
        assert insurance_company.name != ""
        assert insurance_company.code != ""
        assert insurance_company.founded_year != ""
        assert insurance_company.headquarters != ""
        assert insurance_company.website != ""

    def test_generate_single_insurance_company(self):
        insurance_company_service = InsuranceCompanyService()
        insurance_company = insurance_company_service.generate()
        self._test_single_insurance_company(insurance_company)

    def test_generate_multiple_insurance_companies(self):
        insurance_company_service = InsuranceCompanyService()
        insurance_companies = insurance_company_service.generate_batch(10)
        assert len(insurance_companies) == 10
        for insurance_company in insurance_companies:
            self._test_single_insurance_company(insurance_company)

    def test_insurance_company_property_cache(self):
        insurance_company_service = InsuranceCompanyService()
        insurance_company = insurance_company_service.generate()
        assert insurance_company is not None
        assert insurance_company.id == insurance_company.id
        assert insurance_company.name == insurance_company.name
        assert insurance_company.code == insurance_company.code
        assert insurance_company.founded_year == insurance_company.founded_year
        assert insurance_company.headquarters == insurance_company.headquarters
        assert insurance_company.website == insurance_company.website

    @pytest.mark.flaky(reruns=3)
    def test_two_different_entities(self):
        insurance_company_service = InsuranceCompanyService()
        insurance_company1 = insurance_company_service.generate()
        insurance_company2 = insurance_company_service.generate()
        assert insurance_company1.id != insurance_company2.id
        assert insurance_company1.name != insurance_company2.name   
        assert insurance_company1.code != insurance_company2.code
        assert insurance_company1.founded_year != insurance_company2.founded_year
        assert insurance_company1.headquarters != insurance_company2.headquarters
        assert insurance_company1.website != insurance_company2.website

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        insurance_company_service = InsuranceCompanyService(dataset=dataset)
        insurance_company = insurance_company_service.generate()
        self._test_single_insurance_company(insurance_company)

    def test_not_supported_dataset(self):
        insurance_company_service = InsuranceCompanyService(dataset="FR")
        company = insurance_company_service.generate()
        # Fallback to US dataset with a single warning log; should not raise
        assert isinstance(company.to_dict(), dict)

    def test_supported_datasets_static(self):
        codes = InsuranceCompanyService.supported_datasets()
        assert isinstance(codes, set) and len(codes) > 0
        assert "US" in codes and "DE" in codes
