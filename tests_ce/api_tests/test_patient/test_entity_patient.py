import datetime

import pytest

from datamimic_ce.domains.common.models.person import Person
from datamimic_ce.domains.healthcare.models.patient import Patient
from datamimic_ce.domains.healthcare.services.patient_service import PatientService


class TestEntityPatient:
    _supported_datasets = ["US", "DE"]

    def _test_single_patient(self, patient: Patient):
        assert isinstance(patient, Patient)
        assert isinstance(patient.patient_id, str)
        assert isinstance(patient.medical_record_number, str)
        assert isinstance(patient.ssn, str)
        assert isinstance(patient.given_name, str)
        assert isinstance(patient.family_name, str)
        assert isinstance(patient.full_name, str)
        assert isinstance(patient.gender, str)
        assert isinstance(patient.birthdate, datetime.datetime)
        assert isinstance(patient.age, int)
        assert isinstance(patient.blood_type, str)
        assert isinstance(patient.height_cm, float)
        assert isinstance(patient.weight_kg, float)
        assert isinstance(patient.bmi, float)
        assert isinstance(patient.allergies, list)
        assert isinstance(patient.medications, list)
        assert isinstance(patient.conditions, list)
        assert isinstance(patient.emergency_contact, dict)
        assert isinstance(patient.insurance_provider, str)
        assert isinstance(patient.insurance_policy_number, str)
        assert isinstance(patient.person_data, Person)

        assert patient.patient_id is not None and patient.patient_id != ""
        assert patient.medical_record_number is not None and patient.medical_record_number != ""
        assert patient.ssn is not None and patient.ssn != ""
        assert patient.given_name is not None and patient.given_name != ""
        assert patient.family_name is not None and patient.family_name != ""
        assert patient.full_name is not None and patient.full_name != ""
        assert patient.gender is not None and patient.gender != ""
        assert patient.birthdate is not None and patient.birthdate != datetime.datetime.min
        assert patient.age is not None and patient.age != 0
        assert patient.blood_type is not None and patient.blood_type != ""
        assert patient.height_cm is not None and patient.height_cm != 0
        assert patient.weight_kg is not None and patient.weight_kg != 0
        assert patient.bmi is not None and patient.bmi != 0
        assert patient.allergies is not None
        assert patient.medications is not None
        assert patient.conditions is not None
        assert patient.emergency_contact is not None and patient.emergency_contact != {}
        assert patient.insurance_provider is not None and patient.insurance_provider != ""
        assert patient.insurance_policy_number is not None and patient.insurance_policy_number != ""
        assert patient.person_data is not None and patient.person_data != ""

    def test_generate_single_patient(self):
        patient_service = PatientService()
        patient = patient_service.generate()
        self._test_single_patient(patient)

    def test_generate_multiple_patients(self):
        patient_service = PatientService()
        patients = patient_service.generate_batch(10)
        assert len(patients) == 10
        for patient in patients:
            self._test_single_patient(patient)

    def test_hospital_property_cache(self):
        patient_service = PatientService()
        patient = patient_service.generate()
        assert patient.patient_id == patient.patient_id
        assert patient.given_name == patient.given_name
        assert patient.family_name == patient.family_name
        assert patient.full_name == patient.full_name
        assert patient.ssn == patient.ssn
        assert patient.blood_type == patient.blood_type
        assert patient.height_cm == patient.height_cm
        assert patient.weight_kg == patient.weight_kg
        assert patient.bmi == patient.bmi
        assert patient.allergies == patient.allergies
        assert patient.medications == patient.medications
        assert patient.conditions == patient.conditions
        assert patient.emergency_contact == patient.emergency_contact
        assert patient.insurance_provider == patient.insurance_provider
        assert patient.insurance_policy_number == patient.insurance_policy_number
        assert patient.person_data == patient.person_data

    @pytest.mark.flaky(reruns=3)
    def test_two_different_entities(self):
        patient_service = PatientService()
        patient1 = patient_service.generate()
        patient2 = patient_service.generate()
        assert patient1.patient_id != patient2.patient_id
        assert patient1.given_name != patient2.given_name
        assert patient1.family_name != patient2.family_name
        assert patient1.full_name != patient2.full_name
        assert patient1.ssn != patient2.ssn
        assert patient1.blood_type != patient2.blood_type
        assert patient1.height_cm != patient2.height_cm
        assert patient1.weight_kg != patient2.weight_kg
        assert patient1.bmi != patient2.bmi
        assert patient1.emergency_contact != patient2.emergency_contact
        assert patient1.insurance_provider != patient2.insurance_provider
        assert patient1.insurance_policy_number != patient2.insurance_policy_number
        assert patient1.person_data != patient2.person_data
        assert patient1.birthdate != patient2.birthdate
        assert patient1.age != patient2.age

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        patient_service = PatientService(dataset=dataset)
        patient = patient_service.generate()
        self._test_single_patient(patient)

    def test_not_supported_dataset(self):
        random_dataset = "XX"
        # Fallback to US dataset with a single warning log; should not raise
        patient_service = PatientService(dataset=random_dataset)
        patient = patient_service.generate()
        assert isinstance(patient.to_dict(), dict)

    def test_supported_datasets_static(self):
        codes = PatientService.supported_datasets()
        assert isinstance(codes, set) and len(codes) > 0
        assert "US" in codes and "DE" in codes
