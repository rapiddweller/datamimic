# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Tests for the HospitalService.

This module contains tests for the HospitalService in the healthcare domain.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from datamimic_ce.domains.healthcare.services.hospital_service import HospitalService


class TestHospitalService(unittest.TestCase):
    """Test cases for the HospitalService."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()

        # Create a sample hospital data
        self.sample_hospital = {
            "hospital_id": "HOSP-12345678",
            "name": "Anytown General Hospital",
            "type": "General",
            "departments": ["Emergency", "Surgery", "Internal Medicine", "Pediatrics"],
            "services": ["Emergency Care", "Surgery", "Outpatient Care", "Diagnostic Imaging"],
            "bed_count": 300,
            "staff_count": 900,
            "founding_year": 1950,
            "accreditation": ["Joint Commission", "American College of Surgeons"],
            "emergency_services": True,
            "teaching_status": False,
            "website": "https://www.anytowngeneral.org",
            "phone": "(123) 456-7890",
            "email": "info@anytowngeneral.org",
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip_code": "12345",
                "country": "USA",
            },
        }

        # Create a HospitalService instance with mocked Hospital
        with patch("datamimic_ce.domains.healthcare.services.hospital_service.Hospital") as mock_hospital_class:
            self.mock_hospital = MagicMock()
            self.mock_hospital.to_dict.return_value = self.sample_hospital
            self.mock_hospital.generate_batch.return_value = [self.sample_hospital] * 5
            mock_hospital_class.return_value = self.mock_hospital

            self.service = HospitalService(locale="en", dataset="US")

    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()

    def test_initialization(self):
        """Test that the HospitalService is initialized correctly."""
        with patch("datamimic_ce.domains.healthcare.services.hospital_service.Hospital") as mock_hospital_class:
            with patch(
                "datamimic_ce.domains.healthcare.services.hospital_service.ClassFactoryUtil"
            ) as mock_class_factory_util_class:
                mock_class_factory_util = MagicMock()
                mock_class_factory_util_class.return_value = mock_class_factory_util

                service = HospitalService(locale="en", dataset="US")

                # Verify that ClassFactoryUtil was initialized
                mock_class_factory_util_class.assert_called_once()

                # Verify that Hospital was initialized with the correct parameters
                mock_hospital_class.assert_called_once_with(
                    class_factory_util=mock_class_factory_util, locale="en", dataset="US"
                )

    def test_generate_hospital(self):
        """Test that generate_hospital returns a hospital dictionary."""
        hospital = self.service.generate_hospital()

        # Verify that the hospital's to_dict method was called
        self.mock_hospital.to_dict.assert_called_once()

        # Verify that the hospital was reset
        self.mock_hospital.reset.assert_called_once()

        # Verify that the returned hospital is the sample hospital
        self.assertEqual(hospital, self.sample_hospital)

    def test_generate_batch(self):
        """Test that generate_batch returns a list of hospital dictionaries."""
        batch_size = 5
        hospitals = self.service.generate_batch(batch_size)

        # Verify that the hospital's generate_batch method was called with the correct batch size
        self.mock_hospital.generate_batch.assert_called_once_with(batch_size)

        # Verify that the returned list has the correct length
        self.assertEqual(len(hospitals), batch_size)

        # Verify that each hospital in the list is the sample hospital
        for hospital in hospitals:
            self.assertEqual(hospital, self.sample_hospital)

    def test_export_to_json(self):
        """Test that export_to_json writes hospital data to a JSON file."""
        # Create a list of hospitals
        hospitals = [self.sample_hospital] * 3

        # Create a file path in the temporary directory
        file_path = os.path.join(self.temp_dir.name, "hospitals.json")

        # Export the hospitals to JSON
        self.service.export_to_json(hospitals, file_path)

        # Verify that the file was created
        self.assertTrue(os.path.exists(file_path))

        # Read the file and verify its contents
        with open(file_path, encoding="utf-8") as f:
            loaded_hospitals = json.load(f)
            self.assertEqual(loaded_hospitals, hospitals)

    def test_export_to_csv(self):
        """Test that export_to_csv writes hospital data to a CSV file."""
        # Create a list of hospitals
        hospitals = [self.sample_hospital] * 3

        # Create a file path in the temporary directory
        file_path = os.path.join(self.temp_dir.name, "hospitals.csv")

        # Export the hospitals to CSV
        self.service.export_to_csv(hospitals, file_path)

        # Verify that the file was created
        self.assertTrue(os.path.exists(file_path))

        # We won't verify the contents of the CSV file in detail,
        # but we'll check that it has the expected number of lines
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
            # Header line + 3 hospital lines
            self.assertEqual(len(lines), 4)

    def test_get_hospitals_by_type(self):
        """Test that get_hospitals_by_type returns hospitals of the specified type."""
        # Mock the generate_hospital method to return hospitals with different types
        general_hospital = dict(self.sample_hospital)
        general_hospital["type"] = "General"

        teaching_hospital = dict(self.sample_hospital)
        teaching_hospital["type"] = "Teaching"

        specialty_hospital = dict(self.sample_hospital)
        specialty_hospital["type"] = "Specialty"

        # Set up the mock to return these hospitals in sequence
        self.service.generate_hospital = MagicMock(
            side_effect=[general_hospital, teaching_hospital, specialty_hospital, general_hospital, teaching_hospital]
        )

        # Get hospitals of type "Teaching"
        hospitals = self.service.get_hospitals_by_type("Teaching", count=2)

        # Verify that the correct number of hospitals was returned
        self.assertEqual(len(hospitals), 2)

        # Verify that all returned hospitals are of type "Teaching"
        for hospital in hospitals:
            self.assertEqual(hospital["type"], "Teaching")

    def test_get_hospitals_by_service(self):
        """Test that get_hospitals_by_service returns hospitals that offer the specified service."""
        # Mock the generate_hospital method to return hospitals with different services
        hospital1 = dict(self.sample_hospital)
        hospital1["services"] = ["Emergency Care", "Surgery", "Outpatient Care"]

        hospital2 = dict(self.sample_hospital)
        hospital2["services"] = ["Surgery", "Outpatient Care", "Diagnostic Imaging"]

        hospital3 = dict(self.sample_hospital)
        hospital3["services"] = ["Outpatient Care", "Diagnostic Imaging", "Laboratory Services"]

        # Set up the mock to return these hospitals in sequence
        self.service.generate_hospital = MagicMock(side_effect=[hospital1, hospital2, hospital3, hospital1, hospital2])

        # Get hospitals that offer "Emergency Care"
        hospitals = self.service.get_hospitals_by_service("Emergency Care", count=2)

        # Verify that the correct number of hospitals was returned
        self.assertEqual(len(hospitals), 2)

        # Verify that all returned hospitals offer "Emergency Care"
        for hospital in hospitals:
            self.assertIn("Emergency Care", hospital["services"])

    def test_get_hospitals_by_department(self):
        """Test that get_hospitals_by_department returns hospitals that have the specified department."""
        # Mock the generate_hospital method to return hospitals with different departments
        hospital1 = dict(self.sample_hospital)
        hospital1["departments"] = ["Emergency", "Surgery", "Internal Medicine"]

        hospital2 = dict(self.sample_hospital)
        hospital2["departments"] = ["Surgery", "Internal Medicine", "Pediatrics"]

        hospital3 = dict(self.sample_hospital)
        hospital3["departments"] = ["Internal Medicine", "Pediatrics", "Cardiology"]

        # Set up the mock to return these hospitals in sequence
        self.service.generate_hospital = MagicMock(side_effect=[hospital1, hospital2, hospital3, hospital1, hospital2])

        # Get hospitals that have the "Emergency" department
        hospitals = self.service.get_hospitals_by_department("Emergency", count=2)

        # Verify that the correct number of hospitals was returned
        self.assertEqual(len(hospitals), 2)

        # Verify that all returned hospitals have the "Emergency" department
        for hospital in hospitals:
            self.assertIn("Emergency", hospital["departments"])

    def test_get_hospitals_by_bed_count_range(self):
        """Test that get_hospitals_by_bed_count_range returns hospitals within the specified bed count range."""
        # Mock the generate_hospital method to return hospitals with different bed counts
        small_hospital = dict(self.sample_hospital)
        small_hospital["bed_count"] = 100

        medium_hospital = dict(self.sample_hospital)
        medium_hospital["bed_count"] = 300

        large_hospital = dict(self.sample_hospital)
        large_hospital["bed_count"] = 800

        # Set up the mock to return these hospitals in sequence
        self.service.generate_hospital = MagicMock(
            side_effect=[small_hospital, medium_hospital, large_hospital, small_hospital, medium_hospital]
        )

        # Get hospitals with 200-500 beds
        hospitals = self.service.get_hospitals_by_bed_count_range(200, 500, count=2)

        # Verify that the correct number of hospitals was returned
        self.assertEqual(len(hospitals), 2)

        # Verify that all returned hospitals have between 200 and 500 beds
        for hospital in hospitals:
            self.assertTrue(200 <= hospital["bed_count"] <= 500)

    def test_get_hospitals_with_emergency_services(self):
        """Test that get_hospitals_with_emergency_services returns hospitals that offer emergency services."""
        # Mock the generate_hospital method to return hospitals with and without emergency services
        hospital_with_emergency = dict(self.sample_hospital)
        hospital_with_emergency["emergency_services"] = True

        hospital_without_emergency = dict(self.sample_hospital)
        hospital_without_emergency["emergency_services"] = False

        # Set up the mock to return these hospitals in sequence
        self.service.generate_hospital = MagicMock(
            side_effect=[
                hospital_with_emergency,
                hospital_without_emergency,
                hospital_with_emergency,
                hospital_without_emergency,
                hospital_with_emergency,
            ]
        )

        # Get hospitals with emergency services
        hospitals = self.service.get_hospitals_with_emergency_services(count=3)

        # Verify that the correct number of hospitals was returned
        self.assertEqual(len(hospitals), 3)

        # Verify that all returned hospitals have emergency services
        for hospital in hospitals:
            self.assertTrue(hospital["emergency_services"])

    def test_get_teaching_hospitals(self):
        """Test that get_teaching_hospitals returns hospitals that are teaching hospitals."""
        # Mock the generate_hospital method to return teaching and non-teaching hospitals
        teaching_hospital = dict(self.sample_hospital)
        teaching_hospital["teaching_status"] = True

        non_teaching_hospital = dict(self.sample_hospital)
        non_teaching_hospital["teaching_status"] = False

        # Set up the mock to return these hospitals in sequence
        self.service.generate_hospital = MagicMock(
            side_effect=[
                teaching_hospital,
                non_teaching_hospital,
                teaching_hospital,
                non_teaching_hospital,
                teaching_hospital,
            ]
        )

        # Get teaching hospitals
        hospitals = self.service.get_teaching_hospitals(count=3)

        # Verify that the correct number of hospitals was returned
        self.assertEqual(len(hospitals), 3)

        # Verify that all returned hospitals are teaching hospitals
        for hospital in hospitals:
            self.assertTrue(hospital["teaching_status"])

    def test_execute_generate_hospital(self):
        """Test that execute with 'generate_hospital' command returns a hospital."""
        result = self.service.execute("generate_hospital")
        self.assertEqual(result, self.sample_hospital)

    def test_execute_generate_batch(self):
        """Test that execute with 'generate_batch' command returns a batch of hospitals."""
        result = self.service.execute("generate_batch", {"count": 5})
        self.assertEqual(len(result), 5)
        for hospital in result:
            self.assertEqual(hospital, self.sample_hospital)

    def test_execute_export_to_json(self):
        """Test that execute with 'export_to_json' command exports hospitals to a JSON file."""
        # Create a file path in the temporary directory
        file_path = os.path.join(self.temp_dir.name, "hospitals.json")

        # Execute the command
        result = self.service.execute(
            "export_to_json", {"hospitals": [self.sample_hospital] * 3, "file_path": file_path}
        )

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
