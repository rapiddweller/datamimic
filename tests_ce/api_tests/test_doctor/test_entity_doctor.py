import datetime
import random
import string
import pytest

from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.common.models.person import Person
from datamimic_ce.domains.healthcare.models.doctor import Doctor
from datamimic_ce.domains.healthcare.models.hospital import Hospital
from datamimic_ce.domains.healthcare.services.doctor_service import DoctorService



class TestEntityDoctor:
    _supported_datasets = ["US", "DE"]
    def _test_single_doctor(self, doctor: Doctor):
        assert isinstance(doctor, Doctor)
        assert isinstance(doctor.doctor_id, str)
        assert isinstance(doctor.address, Address)
        assert isinstance(doctor.phone, str)
        assert isinstance(doctor.email, str)
        assert isinstance(doctor.accepting_new_patients, bool)
        assert isinstance(doctor.office_hours, dict)
        assert isinstance(doctor.hospital, Hospital)
        assert isinstance(doctor.medical_school, str)
        assert isinstance(doctor.graduation_year, int)  
        assert isinstance(doctor.years_of_experience, int)
        assert isinstance(doctor.certifications, list)
        assert isinstance(doctor.specialty, str)
        assert isinstance(doctor.gender, str)
        assert isinstance(doctor.birthdate, datetime.datetime)
        assert isinstance(doctor.age, int)
        assert isinstance(doctor.first_name, str)
        assert isinstance(doctor.last_name, str)
        assert isinstance(doctor.full_name, str)
        assert isinstance(doctor.npi_number, str)
        assert isinstance(doctor.license_number, str)
        assert isinstance(doctor.person_data, Person)

        assert doctor.doctor_id is not None and doctor.doctor_id != ""
        assert doctor.address is not None and doctor.address != ""
        assert doctor.phone is not None and doctor.phone != ""
        assert doctor.email is not None and doctor.email != ""
        assert doctor.accepting_new_patients is not None 
        assert doctor.office_hours is not None and doctor.office_hours != {}
        assert doctor.hospital is not None and doctor.hospital != ""
        assert doctor.medical_school is not None and doctor.medical_school != ""
        assert doctor.graduation_year is not None 
        assert doctor.years_of_experience is not None 
        assert doctor.certifications is not None and doctor.certifications != []
        assert doctor.specialty is not None and doctor.specialty != ""
        assert doctor.gender is not None and doctor.gender != ""
        assert doctor.birthdate is not None and doctor.birthdate != datetime.datetime.min
        assert doctor.age is not None and doctor.age != 0
        assert doctor.first_name is not None and doctor.first_name != ""
        assert doctor.last_name is not None and doctor.last_name != ""
        assert doctor.full_name is not None and doctor.full_name != ""
        assert doctor.npi_number is not None and doctor.npi_number != ""
        assert doctor.license_number is not None and doctor.license_number != ""
        assert doctor.person_data is not None and doctor.person_data != ""

    def test_generate_single_doctor(self):
        doctor_service = DoctorService()
        doctor = doctor_service.generate()
        self._test_single_doctor(doctor)

    def test_generate_multiple_doctors(self):
        doctor_service = DoctorService()
        doctors = doctor_service.generate_batch(10)
        assert len(doctors) == 10
        for doctor in doctors:
            self._test_single_doctor(doctor)

    def test_hospital_property_cache(self):
        doctor_service = DoctorService()
        doctor = doctor_service.generate()
        assert doctor.doctor_id == doctor.doctor_id
        assert doctor.first_name == doctor.first_name
        assert doctor.last_name == doctor.last_name
        assert doctor.full_name == doctor.full_name
        assert doctor.npi_number == doctor.npi_number
        assert doctor.license_number == doctor.license_number
        assert doctor.hospital == doctor.hospital
        assert doctor.medical_school == doctor.medical_school
        assert doctor.graduation_year == doctor.graduation_year
        assert doctor.years_of_experience == doctor.years_of_experience
        assert doctor.certifications == doctor.certifications
        assert doctor.specialty == doctor.specialty
        assert doctor.gender == doctor.gender
        assert doctor.birthdate == doctor.birthdate
        assert doctor.age == doctor.age
        assert doctor.accepting_new_patients == doctor.accepting_new_patients
        assert doctor.office_hours == doctor.office_hours
        assert doctor.address == doctor.address
        assert doctor.phone == doctor.phone
        assert doctor.email == doctor.email

    def test_two_different_entities(self):
        doctor_service = DoctorService()
        doctor1 = doctor_service.generate()
        doctor2 = doctor_service.generate()
        assert doctor1.doctor_id != doctor2.doctor_id
        assert doctor1.first_name != doctor2.first_name
        assert doctor1.last_name != doctor2.last_name
        assert doctor1.full_name != doctor2.full_name
        assert doctor1.npi_number != doctor2.npi_number
        assert doctor1.license_number != doctor2.license_number
        assert doctor1.address != doctor2.address
        assert doctor1.phone != doctor2.phone
        assert doctor1.email != doctor2.email
        assert doctor1.office_hours != doctor2.office_hours
        assert doctor1.hospital != doctor2.hospital
        assert doctor1.medical_school != doctor2.medical_school
        assert doctor1.graduation_year != doctor2.graduation_year
        assert doctor1.years_of_experience != doctor2.years_of_experience
        assert doctor1.certifications != doctor2.certifications
        assert doctor1.specialty != doctor2.specialty
        assert doctor1.birthdate != doctor2.birthdate
        assert doctor1.age != doctor2.age   

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        doctor_service = DoctorService(dataset=dataset)
        doctor = doctor_service.generate()
        self._test_single_doctor(doctor)

    def test_not_supported_dataset(self):
        random_dataset = "".join(random.choices(string.ascii_uppercase, k=2))
        while random_dataset in self._supported_datasets:
            random_dataset = "".join(random.choices(string.ascii_uppercase, k=2))
        # Raise ValueError because Street name data not found for unsupported dataset
        with pytest.raises(ValueError):
            doctor_service = DoctorService(dataset=random_dataset)
