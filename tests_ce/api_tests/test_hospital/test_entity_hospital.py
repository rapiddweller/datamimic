import random
import string
import pytest

from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.healthcare.models.hospital import Hospital
from datamimic_ce.domains.healthcare.services.hospital_service import HospitalService


class TestEntityHospital:
    _supported_datasets = ["US", "DE"]
    def _test_single_hospital(self, hospital: Hospital):
        assert isinstance(hospital, Hospital)
        assert isinstance(hospital.hospital_id, str)
        assert isinstance(hospital.name, str)
        assert isinstance(hospital.address, Address)
        assert isinstance(hospital.phone, str)
        assert isinstance(hospital.email, str)
        assert isinstance(hospital.website, str)
        assert isinstance(hospital.type, str)
        assert isinstance(hospital.departments, list)
        assert isinstance(hospital.services, list)
        assert isinstance(hospital.bed_count, int)
        assert isinstance(hospital.staff_count, int)
        assert isinstance(hospital.founding_year, int)
        assert isinstance(hospital.accreditation, list)
        assert isinstance(hospital.emergency_services, bool)
        assert isinstance(hospital.teaching_status, bool)
        assert isinstance(hospital.emergency_services, bool)

        assert hospital.hospital_id is not None and hospital.hospital_id != ""
        assert hospital.name is not None and hospital.name != ""
        assert hospital.address is not None and hospital.address != ""
        assert hospital.phone is not None and hospital.phone != ""
        assert hospital.email is not None and hospital.email != ""
        assert hospital.website is not None and hospital.website != ""
        assert hospital.type is not None and hospital.type != ""
        assert hospital.departments is not None and hospital.departments != []
        assert hospital.services is not None and hospital.services != []
        assert hospital.bed_count is not None and hospital.bed_count != 0
        assert hospital.staff_count is not None and hospital.staff_count != 0
        assert hospital.founding_year is not None and hospital.founding_year != 0
        assert hospital.accreditation is not None and hospital.accreditation != []
        assert hospital.emergency_services is not None 
        assert hospital.teaching_status is not None 
        assert hospital.emergency_services is not None 

    def test_generate_single_hospital(self):
        hospital_service = HospitalService()
        hospital = hospital_service.generate()
        self._test_single_hospital(hospital)

    def test_generate_multiple_hospitals(self):
        hospital_service = HospitalService()
        hospitals = hospital_service.generate_batch(10)
        assert len(hospitals) == 10
        for hospital in hospitals:
            self._test_single_hospital(hospital)

    def test_hospital_property_cache(self):
        hospital_service = HospitalService()
        hospital = hospital_service.generate()
        assert hospital.hospital_id == hospital.hospital_id
        assert hospital.name == hospital.name
        assert hospital.address == hospital.address
        assert hospital.phone == hospital.phone
        assert hospital.email == hospital.email
        assert hospital.website == hospital.website
        assert hospital.type == hospital.type
        assert hospital.departments == hospital.departments
        assert hospital.services == hospital.services
        assert hospital.bed_count == hospital.bed_count
        assert hospital.staff_count == hospital.staff_count
        assert hospital.founding_year == hospital.founding_year
        assert hospital.accreditation == hospital.accreditation
        assert hospital.emergency_services == hospital.emergency_services
        assert hospital.teaching_status == hospital.teaching_status

    def test_two_different_entities(self):
        hospital_service = HospitalService()
        hospital1 = hospital_service.generate()
        hospital2 = hospital_service.generate()
        assert hospital1.hospital_id != hospital2.hospital_id
        assert hospital1.name != hospital2.name
        assert hospital1.address != hospital2.address
        assert hospital1.phone != hospital2.phone
        assert hospital1.email != hospital2.email
        assert hospital1.website != hospital2.website
        assert hospital1.type != hospital2.type
        assert hospital1.departments != hospital2.departments
        assert hospital1.services != hospital2.services

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        hospital_service = HospitalService(dataset=dataset)
        hospital = hospital_service.generate()
        self._test_single_hospital(hospital)

    def test_not_supported_dataset(self):
        random_dataset = "".join(random.choices(string.ascii_uppercase, k=2))
        while random_dataset in self._supported_datasets:
            random_dataset = "".join(random.choices(string.ascii_uppercase, k=2))
        # Raise ValueError because Street name data not found for unsupported dataset
        with pytest.raises(ValueError):
            hospital_service = HospitalService(dataset=random_dataset)
