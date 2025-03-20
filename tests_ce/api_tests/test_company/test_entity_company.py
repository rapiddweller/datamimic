import pytest
from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.common.models.company import Company
from datamimic_ce.domains.common.services.company_service import CompanyService


class TestEntityCompany:
    _supported_datasets = ["AT", "AU", "BE", "BR", "CA", "CH", "CZ", "DE", "ES", "FI", "FR", "GB", "IE", "IT", "NL", "NO", "NZ", "PL", "RU", "SE", "SK", "TR", "UA", "US"]
    def _test_single_company(self, company: Company):
        assert isinstance(company, Company)
        assert isinstance(company.id, str)
        assert isinstance(company.short_name, str)
        assert isinstance(company.full_name, str)
        assert isinstance(company.sector, str)
        assert isinstance(company.legal_form, str)
        assert isinstance(company.address_data, Address)
        assert isinstance(company.email, str)
        assert isinstance(company.phone_number, str)
        assert isinstance(company.country_code, str)
        assert isinstance(company.country, str)
        assert isinstance(company.city, str)
        assert isinstance(company.state, str)   
        assert isinstance(company.zip_code, str)
                
        assert company.sector is not None and company.sector != ""
        assert company.legal_form is not None and company.legal_form != ""
        assert company.email is not None and company.email != ""
        assert company.phone_number is not None and company.phone_number != ""
        assert company.office_phone is not None and company.office_phone != ""
        assert company.fax is not None and company.fax != ""
        assert company.country_code is not None and company.country_code != ""
        assert company.country is not None and company.country != ""
        assert company.city is not None
        assert company.state is not None and company.state != ""
        assert company.zip_code is not None and company.zip_code != ""
        assert company.address_data is not None
        assert company.street is not None and company.street != ""
        assert company.house_number is not None and company.house_number != ""
        assert company.city is not None and company.city != ""
        assert company.state is not None and company.state != ""
        assert company.zip_code is not None and company.zip_code != ""

    def test_generate_single_company(self):
        company_service = CompanyService()
        company = company_service.generate()
        self._test_single_company(company)

    def test_generate_multiple_companies(self):
        company_service = CompanyService()
        companies = company_service.generate_batch(10)
        assert len(companies) == 10
        for company in companies:
            self._test_single_company(company)

    def test_company_property_cache(self):
        company_service = CompanyService()
        company = company_service.generate()    
        assert company is not None
        assert company.id == company.id
        assert company.short_name == company.short_name
        assert company.full_name == company.full_name
        assert company.sector == company.sector
        assert company.legal_form == company.legal_form
        assert company.address_data == company.address_data
        assert company.email == company.email
        assert company.phone_number == company.phone_number
        assert company.country_code == company.country_code
        assert company.country == company.country
        assert company.city == company.city
        assert company.state == company.state
        assert company.zip_code == company.zip_code

    @pytest.mark.flaky(reruns=3)
    def test_two_different_entities(self):
        company_service = CompanyService()
        company1 = company_service.generate()
        company2 = company_service.generate()
        assert company1.id != company2.id
        assert company1.short_name != company2.short_name
        assert company1.full_name != company2.full_name
        assert company1.sector != company2.sector
        assert company1.legal_form != company2.legal_form
        assert company1.address_data != company2.address_data
        assert company1.email != company2.email
        assert company1.phone_number != company2.phone_number
        assert company1.country_code == company2.country_code
        assert company1.country == company2.country
        assert company1.city != company2.city
        assert company1.state != company2.state
        assert company1.zip_code != company2.zip_code

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        company_service = CompanyService(dataset=dataset)
        company = company_service.generate()
        self._test_single_company(company)

    def test_not_supported_dataset(self):
        random_dataset = "XX"
        # Raise ValueError because Company data not found for unsupported dataset   
        with pytest.raises(ValueError):
            company_service = CompanyService(dataset=random_dataset)