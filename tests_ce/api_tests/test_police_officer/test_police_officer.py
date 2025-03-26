from datetime import datetime

import pytest

from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.public_sector.models.police_officer import PoliceOfficer
from datamimic_ce.domains.public_sector.services.police_officer_service import PoliceOfficerService


class TestEntityPoliceOfficer:
    _supported_datasets = ["US", "DE"]

    def _test_single_police_officer(self, police_officer: PoliceOfficer):
        assert isinstance(police_officer, PoliceOfficer)
        assert isinstance(police_officer.officer_id, str)
        assert isinstance(police_officer.badge_number, str)
        assert isinstance(police_officer.given_name, str)
        assert isinstance(police_officer.family_name, str)
        assert isinstance(police_officer.full_name, str)
        assert isinstance(police_officer.gender, str)
        assert isinstance(police_officer.birthdate, datetime)
        assert isinstance(police_officer.age, int)
        assert isinstance(police_officer.rank, str)
        assert isinstance(police_officer.department, str)
        assert isinstance(police_officer.unit, str)
        assert isinstance(police_officer.hire_date, str)
        assert isinstance(police_officer.years_of_service, int)
        assert isinstance(police_officer.certifications, list)
        assert isinstance(police_officer.languages, list)
        assert isinstance(police_officer.shift, str)
        assert isinstance(police_officer.email, str)
        assert isinstance(police_officer.phone, str)
        assert isinstance(police_officer.address, Address)
        assert police_officer.officer_id is not None and police_officer.officer_id != ""
        assert police_officer.badge_number is not None and police_officer.badge_number != ""
        assert police_officer.given_name is not None and police_officer.given_name != ""
        assert police_officer.family_name is not None and police_officer.family_name != ""
        assert police_officer.full_name is not None and police_officer.full_name != ""
        assert police_officer.gender is not None and police_officer.gender != ""
        assert police_officer.birthdate is not None and police_officer.birthdate != ""
        assert police_officer.age is not None and police_officer.age != ""
        assert police_officer.rank is not None and police_officer.rank != ""
        assert police_officer.department is not None and police_officer.department != ""
        assert police_officer.unit is not None and police_officer.unit != ""
        assert police_officer.hire_date is not None and police_officer.hire_date != ""
        assert police_officer.years_of_service is not None and police_officer.years_of_service != ""
        assert police_officer.certifications is not None and police_officer.certifications != ""
        assert police_officer.languages is not None and police_officer.languages != ""
        assert police_officer.shift is not None and police_officer.shift != ""
        assert police_officer.email is not None and police_officer.email != ""
        assert police_officer.phone is not None and police_officer.phone != ""
        assert police_officer.address is not None and police_officer.address != ""

    def test_generate_single_police_officer(self):
        police_officer_service = PoliceOfficerService()
        police_officer = police_officer_service.generate()
        self._test_single_police_officer(police_officer)

    def test_generate_multiple_police_officers(self):
        police_officer_service = PoliceOfficerService()
        police_officers = police_officer_service.generate_batch(10)
        assert len(police_officers) == 10
        for police_officer in police_officers:
            self._test_single_police_officer(police_officer)

    def test_police_officer_property_cache(self):
        police_officer_service = PoliceOfficerService()
        police_officer = police_officer_service.generate()
        assert police_officer.badge_number == police_officer.badge_number
        assert police_officer.given_name == police_officer.given_name
        assert police_officer.family_name == police_officer.family_name
        assert police_officer.full_name == police_officer.full_name
        assert police_officer.gender == police_officer.gender
        assert police_officer.birthdate == police_officer.birthdate
        assert police_officer.age == police_officer.age
        assert police_officer.rank == police_officer.rank
        assert police_officer.department == police_officer.department
        assert police_officer.unit == police_officer.unit
        assert police_officer.hire_date == police_officer.hire_date
        assert police_officer.years_of_service == police_officer.years_of_service
        assert police_officer.certifications == police_officer.certifications
        assert police_officer.languages == police_officer.languages
        assert police_officer.shift == police_officer.shift
        assert police_officer.email == police_officer.email
        assert police_officer.phone == police_officer.phone
        assert police_officer.address == police_officer.address

    @pytest.mark.flaky(reruns=10)
    def test_two_different_entities(self):
        police_officer_service = PoliceOfficerService()
        police_officer1 = police_officer_service.generate()
        police_officer2 = police_officer_service.generate()
        assert police_officer1.given_name != police_officer2.given_name
        assert police_officer1.family_name != police_officer2.family_name
        assert police_officer1.full_name != police_officer2.full_name
        # assert police_officer1.gender != police_officer2.gender
        assert police_officer1.birthdate != police_officer2.birthdate
        assert police_officer1.age != police_officer2.age
        # assert police_officer1.rank != police_officer2.rank
        assert police_officer1.department != police_officer2.department
        assert police_officer1.unit != police_officer2.unit
        assert police_officer1.hire_date != police_officer2.hire_date
        assert police_officer1.years_of_service != police_officer2.years_of_service
        assert police_officer1.certifications != police_officer2.certifications
        assert police_officer1.languages != police_officer2.languages
        # assert police_officer1.shift != police_officer2.shift
        assert police_officer1.email != police_officer2.email
        assert police_officer1.phone != police_officer2.phone
        assert police_officer1.address != police_officer2.address

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_police_officer_dataset(self, dataset):
        police_officer_service = PoliceOfficerService(dataset=dataset)
        police_officer = police_officer_service.generate()
        self._test_single_police_officer(police_officer)

    def test_not_supported_dataset(self):
        police_officer_service = PoliceOfficerService(dataset="FR")
        police_officer = police_officer_service.generate()
        with pytest.raises(FileNotFoundError):
            police_officer.to_dict()
