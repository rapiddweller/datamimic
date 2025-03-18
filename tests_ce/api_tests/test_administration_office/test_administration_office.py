from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.common.services.address_service import AddressService
from datamimic_ce.domains.public_sector.models.administration_office import AdministrationOffice
from datamimic_ce.domains.public_sector.services.administration_office_service import AdministrationOfficeService


class TestEntityAdministrationOffice:
    def _test_single_administration_office(self, administration_office: AdministrationOffice):
        assert isinstance(administration_office, AdministrationOffice)
        assert isinstance(administration_office.name, str)
        assert isinstance(administration_office.type, str)
        assert isinstance(administration_office.jurisdiction, str)
        assert isinstance(administration_office.founding_year, int)
        assert isinstance(administration_office.staff_count, int)
        assert isinstance(administration_office.annual_budget, int)
        assert isinstance(administration_office.hours_of_operation, dict)
        assert isinstance(administration_office.website, str)
        assert isinstance(administration_office.email, str)
        assert isinstance(administration_office.phone, str)
        assert isinstance(administration_office.services, list)
        assert isinstance(administration_office.departments, list)
        assert isinstance(administration_office.leadership, dict)
        assert isinstance(administration_office.address, Address)

        assert administration_office.name is not None and administration_office.name != ""
        assert administration_office.type is not None and administration_office.type != ""
        assert administration_office.jurisdiction is not None and administration_office.jurisdiction != ""
        assert administration_office.founding_year is not None and administration_office.founding_year != ""
        assert administration_office.staff_count is not None and administration_office.staff_count != ""
        assert administration_office.annual_budget is not None and administration_office.annual_budget != ""
        assert administration_office.hours_of_operation is not None and administration_office.hours_of_operation != ""
        assert administration_office.website is not None and administration_office.website != ""
        assert administration_office.email is not None and administration_office.email != ""
        assert administration_office.phone is not None and administration_office.phone != ""
        
    def test_generate_single_address(self):
        administration_office_service = AdministrationOfficeService()
        administration_office = administration_office_service.generate()
        self._test_single_administration_office(administration_office)

    def test_generate_multiple_addresses(self):
        administration_office_service = AdministrationOfficeService()
        administration_offices = administration_office_service.generate_batch(10)
        assert len(administration_offices) == 10
        for administration_office in administration_offices:
            self._test_single_administration_office(administration_office)

    def test_administration_office_property_cache(self):
        administration_office_service = AdministrationOfficeService()
        administration_office = administration_office_service.generate()
        assert administration_office.name == administration_office.name
        assert administration_office.type == administration_office.type
        assert administration_office.jurisdiction == administration_office.jurisdiction
        assert administration_office.founding_year == administration_office.founding_year
        assert administration_office.staff_count == administration_office.staff_count
        assert administration_office.annual_budget == administration_office.annual_budget
        assert administration_office.hours_of_operation == administration_office.hours_of_operation
        assert administration_office.website == administration_office.website
        assert administration_office.email == administration_office.email
        assert administration_office.phone == administration_office.phone
        assert administration_office.services == administration_office.services
        assert administration_office.departments == administration_office.departments
        assert administration_office.leadership == administration_office.leadership
        assert administration_office.address == administration_office.address

    def test_two_different_entities(self):
        administration_office_service = AdministrationOfficeService()
        administration_office1 = administration_office_service.generate()
        administration_office2 = administration_office_service.generate()
        assert administration_office1.name != administration_office2.name
        assert administration_office1.type != administration_office2.type
        assert administration_office1.jurisdiction != administration_office2.jurisdiction
        assert administration_office1.founding_year != administration_office2.founding_year
        assert administration_office1.staff_count != administration_office2.staff_count
        assert administration_office1.annual_budget != administration_office2.annual_budget
        assert administration_office1.hours_of_operation != administration_office2.hours_of_operation
        assert administration_office1.website != administration_office2.website
        assert administration_office1.email != administration_office2.email
        assert administration_office1.phone != administration_office2.phone
        assert administration_office1.services != administration_office2.services
        assert administration_office1.departments != administration_office2.departments
        assert administration_office1.leadership != administration_office2.leadership
        assert administration_office1.address != administration_office2.address

