# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Tests for the PatientService.

This module contains tests for the PatientService in the healthcare domain.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from datamimic_ce.domains.healthcare.services.patient_service import PatientService


class TestPatientService(unittest.TestCase):
    """Test cases for the PatientService."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()

        # Create a sample patient data
        self.sample_patient = {
            "patient_id": "PAT-12345678",
            "medical_record_number": "MRN-1234567",
            "ssn": "123-45-6789",
            "first_name": "John",
            "last_name": "Doe",
            "full_name": "John Doe",
            "gender": "Male",
            "date_of_birth": "1980-01-01",
            "age": 43,
            "blood_type": "O+",
            "height_cm": 180.0,
            "weight_kg": 80.0,
            "bmi": 24.7,
            "allergies": ["Penicillin", "Peanuts"],
            "medications": ["Lisinopril", "Atorvastatin"],
            "conditions": ["Hypertension", "Hyperlipidemia"],
            "emergency_contact": {"name": "Jane Doe", "relationship": "Spouse", "phone": "(123) 456-7890"},
            "insurance_provider": "Blue Cross Blue Shield",
            "insurance_policy_number": "ABC-12345678",
            "primary_care_physician": "Dr. Sarah Smith",
            "last_visit_date": "2023-01-15",
            "next_appointment": "2023-07-15",
            "email": "john.doe@example.com",
            "phone": "(987) 654-3210",
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip_code": "12345",
                "country": "USA",
            },
        }

        # Create a PatientService instance with mocked Patient
        with patch("datamimic_ce.domains.healthcare.services.patient_service.Patient") as mock_patient_class:
            self.mock_patient = MagicMock()
            self.mock_patient.to_dict.return_value = self.sample_patient
            self.mock_patient.generate_batch.return_value = [self.sample_patient] * 5
            mock_patient_class.return_value = self.mock_patient

            self.service = PatientService(locale="en", dataset="US")

    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()

    def test_initialization(self):
        """Test that the PatientService is initialized correctly."""
        with patch("datamimic_ce.domains.healthcare.services.patient_service.Patient") as mock_patient_class:
            with patch(
                "datamimic_ce.domains.healthcare.services.patient_service.ClassFactoryUtil"
            ) as mock_class_factory_util_class:
                mock_class_factory_util = MagicMock()
                mock_class_factory_util_class.return_value = mock_class_factory_util

                service = PatientService(locale="en", dataset="US")

                # Verify that ClassFactoryUtil was initialized
                mock_class_factory_util_class.assert_called_once()

                # Verify that Patient was initialized with the correct parameters
                mock_patient_class.assert_called_once_with(
                    class_factory_util=mock_class_factory_util, locale="en", dataset="US"
                )

    def test_generate_patient(self):
        """Test that generate_patient returns a patient dictionary."""
        patient = self.service.generate_patient()

        # Verify that the patient's to_dict method was called
        self.mock_patient.to_dict.assert_called_once()

        # Verify that the patient was reset
        self.mock_patient.reset.assert_called_once()

        # Verify that the returned patient is the sample patient
        self.assertEqual(patient, self.sample_patient)

    def test_generate_batch(self):
        """Test that generate_batch returns a list of patient dictionaries."""
        batch_size = 5
        patients = self.service.generate_batch(batch_size)

        # Verify that the patient's generate_batch method was called with the correct batch size
        self.mock_patient.generate_batch.assert_called_once_with(batch_size)

        # Verify that the returned list has the correct length
        self.assertEqual(len(patients), batch_size)

        # Verify that each patient in the list is the sample patient
        for patient in patients:
            self.assertEqual(patient, self.sample_patient)

    def test_export_to_json(self):
        """Test that export_to_json writes patient data to a JSON file."""
        # Create a list of patients
        patients = [self.sample_patient] * 3

        # Create a file path in the temporary directory
        file_path = os.path.join(self.temp_dir.name, "patients.json")

        # Export the patients to JSON
        self.service.export_to_json(patients, file_path)

        # Verify that the file was created
        self.assertTrue(os.path.exists(file_path))

        # Read the file and verify its contents
        with open(file_path, encoding="utf-8") as f:
            loaded_patients = json.load(f)
            self.assertEqual(loaded_patients, patients)

    def test_export_to_csv(self):
        """Test that export_to_csv writes patient data to a CSV file."""
        # Create a list of patients
        patients = [self.sample_patient] * 3

        # Create a file path in the temporary directory
        file_path = os.path.join(self.temp_dir.name, "patients.csv")

        # Export the patients to CSV
        self.service.export_to_csv(patients, file_path)

        # Verify that the file was created
        self.assertTrue(os.path.exists(file_path))

        # We won't verify the contents of the CSV file in detail,
        # but we'll check that it has the expected number of lines
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
            # Header line + 3 patient lines
            self.assertEqual(len(lines), 4)

    def test_get_patients_by_condition(self):
        """Test that get_patients_by_condition returns patients with the specified condition."""
        # Mock the generate_patient method to return patients with different conditions
        hypertension_patient = dict(self.sample_patient)
        hypertension_patient["conditions"] = ["Hypertension"]

        diabetes_patient = dict(self.sample_patient)
        diabetes_patient["conditions"] = ["Type 2 Diabetes"]

        asthma_patient = dict(self.sample_patient)
        asthma_patient["conditions"] = ["Asthma"]

        # Set up the mock to return these patients in sequence
        self.service.generate_patient = MagicMock(
            side_effect=[hypertension_patient, diabetes_patient, asthma_patient, hypertension_patient, diabetes_patient]
        )

        # Get patients with hypertension
        patients = self.service.get_patients_by_condition("Hypertension", count=2)

        # Verify that the correct number of patients was returned
        self.assertEqual(len(patients), 2)

        # Verify that all returned patients have hypertension
        for patient in patients:
            self.assertIn("Hypertension", patient["conditions"])

    def test_get_patients_by_age_range(self):
        """Test that get_patients_by_age_range returns patients within the specified age range."""
        # Mock the generate_patient method to return patients with different ages
        young_patient = dict(self.sample_patient)
        young_patient["age"] = 25

        middle_aged_patient = dict(self.sample_patient)
        middle_aged_patient["age"] = 45

        elderly_patient = dict(self.sample_patient)
        elderly_patient["age"] = 75

        # Set up the mock to return these patients in sequence
        self.service.generate_patient = MagicMock(
            side_effect=[young_patient, middle_aged_patient, elderly_patient, young_patient, middle_aged_patient]
        )

        # Get patients between 40 and 60 years old
        patients = self.service.get_patients_by_age_range(40, 60, count=2)

        # Verify that the correct number of patients was returned
        self.assertEqual(len(patients), 2)

        # Verify that all returned patients are within the age range
        for patient in patients:
            self.assertTrue(40 <= patient["age"] <= 60)

    def test_get_patients_by_insurance(self):
        """Test that get_patients_by_insurance returns patients with the specified insurance provider."""
        # Mock the generate_patient method to return patients with different insurance providers
        bcbs_patient = dict(self.sample_patient)
        bcbs_patient["insurance_provider"] = "Blue Cross Blue Shield"

        aetna_patient = dict(self.sample_patient)
        aetna_patient["insurance_provider"] = "Aetna"

        cigna_patient = dict(self.sample_patient)
        cigna_patient["insurance_provider"] = "Cigna"

        # Set up the mock to return these patients in sequence
        self.service.generate_patient = MagicMock(
            side_effect=[bcbs_patient, aetna_patient, cigna_patient, bcbs_patient, aetna_patient]
        )

        # Get patients with Aetna insurance
        patients = self.service.get_patients_by_insurance("Aetna", count=2)

        # Verify that the correct number of patients was returned
        self.assertEqual(len(patients), 2)

        # Verify that all returned patients have Aetna insurance
        for patient in patients:
            self.assertEqual(patient["insurance_provider"], "Aetna")

    def test_execute_generate_patient(self):
        """Test that execute with 'generate_patient' command returns a patient."""
        result = self.service.execute("generate_patient")
        self.assertEqual(result, self.sample_patient)

    def test_execute_generate_batch(self):
        """Test that execute with 'generate_batch' command returns a batch of patients."""
        result = self.service.execute("generate_batch", {"count": 5})
        self.assertEqual(len(result), 5)
        for patient in result:
            self.assertEqual(patient, self.sample_patient)

    def test_execute_export_to_json(self):
        """Test that execute with 'export_to_json' command exports patients to a JSON file."""
        # Create a file path in the temporary directory
        file_path = os.path.join(self.temp_dir.name, "patients.json")

        # Execute the command
        result = self.service.execute("export_to_json", {"patients": [self.sample_patient] * 3, "file_path": file_path})

        # Verify that the command returned success
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["file_path"], file_path)

        # Verify that the file was created
        self.assertTrue(os.path.exists(file_path))

    def test_execute_unsupported_command(self):
        """Test that execute with an unsupported command raises a ValueError."""
        with self.assertRaises(ValueError):
            self.service.execute("unsupported_command")


if __name__ == "__main__":
    unittest.main()
