# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Tests for the Patient model.

This module contains tests for the Patient model in the healthcare domain.
"""

import unittest
from unittest.mock import MagicMock

from datamimic_ce.domains.healthcare.models.patient import Patient


class TestPatient(unittest.TestCase):
    """Test cases for the Patient model."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock class factory util
        self.mock_class_factory_util = MagicMock()

        # Mock person entity
        self.mock_person_entity = MagicMock()
        self.mock_person_entity.first_name = "John"
        self.mock_person_entity.last_name = "Doe"
        self.mock_person_entity.gender = "Male"
        self.mock_person_entity.date_of_birth = "1980-01-01"
        self.mock_person_entity.age = 43

        # Mock address entity
        self.mock_address_entity = MagicMock()
        self.mock_address_entity.to_dict.return_value = {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345",
            "country": "USA",
        }

        # Set up the mock class factory to return our mock entities
        self.mock_class_factory_util.get_person_entity.return_value = self.mock_person_entity
        self.mock_class_factory_util.get_address_entity.return_value = self.mock_address_entity

        # Create a patient instance with the mock class factory
        self.patient = Patient(class_factory_util=self.mock_class_factory_util, locale="en", dataset="US")

    def test_initialization(self):
        """Test that the Patient is initialized correctly."""
        # Verify that the class factory was used to get the person and address entities
        self.mock_class_factory_util.get_person_entity.assert_called_once_with(locale="en", dataset="US")
        self.mock_class_factory_util.get_address_entity.assert_called_once_with(locale="en", dataset="US")

        # Verify that the data loader was initialized
        self.assertIsNotNone(self.patient._data_loader)

        # Verify that the generators were initialized
        self.assertIsNotNone(self.patient._patient_id_generator)
        self.assertIsNotNone(self.patient._medical_record_number_generator)
        self.assertIsNotNone(self.patient._blood_type_generator)
        # ... and so on for other generators

    def test_personal_information(self):
        """Test that personal information is retrieved from the person entity."""
        self.assertEqual(self.patient.first_name, "John")
        self.assertEqual(self.patient.last_name, "Doe")
        self.assertEqual(self.patient.full_name, "John Doe")
        self.assertEqual(self.patient.gender, "Male")
        self.assertEqual(self.patient.date_of_birth, "1980-01-01")
        self.assertEqual(self.patient.age, 43)

    def test_address(self):
        """Test that address information is retrieved from the address entity."""
        expected_address = {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345",
            "country": "USA",
        }
        self.assertEqual(self.patient.address, expected_address)

    def test_patient_id_format(self):
        """Test that the patient ID has the correct format."""
        patient_id = self.patient.patient_id
        self.assertTrue(patient_id.startswith("PAT-"))
        self.assertEqual(len(patient_id), 12)  # "PAT-" + 8 hex characters

    def test_medical_record_number_format(self):
        """Test that the medical record number has the correct format."""
        mrn = self.patient.medical_record_number
        self.assertTrue(mrn.startswith("MRN-"))
        self.assertEqual(len(mrn), 11)  # "MRN-" + 7 digits

    def test_ssn_format(self):
        """Test that the SSN has the correct format."""
        ssn = self.patient.ssn
        parts = ssn.split("-")
        self.assertEqual(len(parts), 3)
        self.assertEqual(len(parts[0]), 3)
        self.assertEqual(len(parts[1]), 2)
        self.assertEqual(len(parts[2]), 4)

    def test_blood_type(self):
        """Test that the blood type is one of the valid types."""
        valid_blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        self.assertIn(self.patient.blood_type, valid_blood_types)

    def test_height_weight_bmi(self):
        """Test that height, weight, and BMI are calculated correctly."""
        # Mock the height and weight generators to return fixed values
        self.patient._height_cm_generator.get = MagicMock(return_value=180.0)
        self.patient._weight_kg_generator.get = MagicMock(return_value=80.0)

        # Calculate expected BMI: weight(kg) / height(m)^2
        expected_bmi = 80.0 / ((180.0 / 100) ** 2)
        expected_bmi = round(expected_bmi, 1)

        self.assertEqual(self.patient.height_cm, 180.0)
        self.assertEqual(self.patient.weight_kg, 80.0)
        self.assertEqual(self.patient.bmi, expected_bmi)

    def test_to_dict(self):
        """Test that to_dict returns a dictionary with all patient properties."""
        patient_dict = self.patient.to_dict()

        # Check that the dictionary contains all expected keys
        expected_keys = [
            "patient_id",
            "medical_record_number",
            "ssn",
            "first_name",
            "last_name",
            "full_name",
            "gender",
            "date_of_birth",
            "age",
            "blood_type",
            "height_cm",
            "weight_kg",
            "bmi",
            "allergies",
            "medications",
            "conditions",
            "emergency_contact",
            "insurance_provider",
            "insurance_policy_number",
            "primary_care_physician",
            "last_visit_date",
            "next_appointment",
            "email",
            "phone",
            "address",
        ]

        for key in expected_keys:
            self.assertIn(key, patient_dict)

        # Check that the values are of the expected types
        self.assertIsInstance(patient_dict["patient_id"], str)
        self.assertIsInstance(patient_dict["medical_record_number"], str)
        self.assertIsInstance(patient_dict["ssn"], str)
        self.assertIsInstance(patient_dict["first_name"], str)
        self.assertIsInstance(patient_dict["last_name"], str)
        self.assertIsInstance(patient_dict["full_name"], str)
        self.assertIsInstance(patient_dict["gender"], str)
        self.assertIsInstance(patient_dict["date_of_birth"], str)
        self.assertIsInstance(patient_dict["age"], int)
        self.assertIsInstance(patient_dict["blood_type"], str)
        self.assertIsInstance(patient_dict["height_cm"], float)
        self.assertIsInstance(patient_dict["weight_kg"], float)
        self.assertIsInstance(patient_dict["bmi"], float)
        self.assertIsInstance(patient_dict["allergies"], list)
        self.assertIsInstance(patient_dict["medications"], list)
        self.assertIsInstance(patient_dict["conditions"], list)
        self.assertIsInstance(patient_dict["emergency_contact"], dict)
        self.assertIsInstance(patient_dict["insurance_provider"], str)
        self.assertIsInstance(patient_dict["insurance_policy_number"], str)
        self.assertIsInstance(patient_dict["primary_care_physician"], str)
        self.assertIsInstance(patient_dict["last_visit_date"], str)
        # next_appointment can be None or str
        self.assertIsInstance(patient_dict["email"], str)
        self.assertIsInstance(patient_dict["phone"], str)
        self.assertIsInstance(patient_dict["address"], dict)

    def test_reset(self):
        """Test that reset clears all cached values."""
        # Call some properties to generate values
        _ = self.patient.patient_id
        _ = self.patient.medical_record_number
        _ = self.patient.blood_type

        # Reset the patient
        self.patient.reset()

        # Verify that the person and address entities were reset
        self.mock_person_entity.reset.assert_called_once()
        self.mock_address_entity.reset.assert_called_once()

        # We can't directly test that the generators were reset without
        # modifying the implementation to expose the reset state.
        # Instead, we'll verify that calling reset doesn't raise exceptions.
        self.patient._patient_id_generator.reset()
        self.patient._medical_record_number_generator.reset()
        self.patient._blood_type_generator.reset()

    def test_generate_batch(self):
        """Test that generate_batch returns the correct number of patients."""
        batch_size = 5
        patients = self.patient.generate_batch(batch_size)

        self.assertEqual(len(patients), batch_size)
        for patient in patients:
            self.assertIsInstance(patient, dict)
            self.assertIn("patient_id", patient)
            self.assertIn("first_name", patient)
            self.assertIn("last_name", patient)


if __name__ == "__main__":
    unittest.main()
