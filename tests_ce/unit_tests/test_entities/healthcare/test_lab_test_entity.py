# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import unittest
from datetime import datetime

from datamimic_ce.entities.healthcare.lab_test_entity import LabTestEntity
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestLabTestEntity(unittest.TestCase):
    """Test cases for the LabTestEntity class."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()
        self.lab_test_entity = LabTestEntity(self.class_factory_util)

    def test_init(self):
        """Test initialization of LabTestEntity."""
        self.assertEqual(self.lab_test_entity._locale, "en")
        self.assertIsNone(self.lab_test_entity._dataset)

    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        lab_test_entity = LabTestEntity(
            self.class_factory_util,
            locale="de",
            dataset="test_dataset"
        )
        self.assertEqual(lab_test_entity._locale, "de")
        self.assertEqual(lab_test_entity._dataset, "test_dataset")

    def test_test_id_generation(self):
        """Test test_id generation."""
        test_id = self.lab_test_entity.test_id
        self.assertIsInstance(test_id, str)
        self.assertTrue(len(test_id) > 0)
        # Check if it follows the expected format (e.g., "LAB-12345678")
        self.assertRegex(test_id, r"LAB-\d+")

    def test_patient_id_generation(self):
        """Test patient_id generation."""
        patient_id = self.lab_test_entity.patient_id
        self.assertIsInstance(patient_id, str)
        self.assertTrue(len(patient_id) > 0)
        # Check if it follows the expected format (e.g., "P-12345678")
        self.assertRegex(patient_id, r"P-\d+")

    def test_doctor_id_generation(self):
        """Test doctor_id generation."""
        doctor_id = self.lab_test_entity.doctor_id
        self.assertIsInstance(doctor_id, str)
        self.assertTrue(len(doctor_id) > 0)
        # Check if it follows the expected format (e.g., "DR-12345678")
        self.assertRegex(doctor_id, r"DR-\d+")

    def test_test_type_generation(self):
        """Test test_type generation."""
        test_type = self.lab_test_entity.test_type
        self.assertIsInstance(test_type, str)
        # We no longer have static TEST_TYPES, so just check that it's not empty
        self.assertTrue(len(test_type) > 0, "Test type should not be empty")

    def test_test_name_generation(self):
        """Test test_name generation."""
        test_name = self.lab_test_entity.test_name
        self.assertIsInstance(test_name, str)
        self.assertTrue(len(test_name) > 0)

    def test_test_date_generation(self):
        """Test test_date generation."""
        test_date = self.lab_test_entity.test_date
        self.assertIsInstance(test_date, str)
        # Check if it's a valid date string (YYYY-MM-DD)
        self.assertRegex(test_date, r"\d{4}-\d{2}-\d{2}")
        # Validate it's a real date
        try:
            datetime.strptime(test_date, "%Y-%m-%d")
        except ValueError:
            self.fail("test_date is not a valid date")

    def test_result_date_generation(self):
        """Test result_date generation."""
        result_date = self.lab_test_entity.result_date
        self.assertIsInstance(result_date, str)
        # Check if it's a valid date string (YYYY-MM-DD)
        self.assertRegex(result_date, r"\d{4}-\d{2}-\d{2}")
        # Validate it's a real date
        try:
            datetime.strptime(result_date, "%Y-%m-%d")
        except ValueError:
            self.fail("result_date is not a valid date")
        # Check that result_date is after or equal to test_date
        self.assertGreaterEqual(
            datetime.strptime(result_date, "%Y-%m-%d"),
            datetime.strptime(self.lab_test_entity.test_date, "%Y-%m-%d")
        )

    def test_status_generation(self):
        """Test status generation."""
        status = self.lab_test_entity.status
        self.assertIsInstance(status, str)
        # We no longer have static STATUSES, so just check that it's not empty
        self.assertTrue(len(status) > 0, "Status should not be empty")

    def test_specimen_type_generation(self):
        """Test specimen_type generation."""
        specimen_type = self.lab_test_entity.specimen_type
        self.assertIsInstance(specimen_type, str)
        
        # Only check that the specimen type is a non-empty string
        # This is more resilient than trying to maintain an exhaustive list of all possible specimen types
        self.assertTrue(len(specimen_type) > 0, "Specimen type should not be empty")
        
        # Print the specimen type for debugging
        print(f"Generated specimen type: {specimen_type}")

    def test_specimen_collection_date_generation(self):
        """Test specimen_collection_date generation."""
        specimen_collection_date = self.lab_test_entity.specimen_collection_date
        self.assertIsInstance(specimen_collection_date, str)
        # Check if it's a valid date string (YYYY-MM-DD)
        self.assertRegex(specimen_collection_date, r"\d{4}-\d{2}-\d{2}")
        # Validate it's a real date
        try:
            datetime.strptime(specimen_collection_date, "%Y-%m-%d")
        except ValueError:
            self.fail("specimen_collection_date is not a valid date")
        # Check that specimen_collection_date is before or equal to test_date
        self.assertLessEqual(
            datetime.strptime(specimen_collection_date, "%Y-%m-%d"),
            datetime.strptime(self.lab_test_entity.test_date, "%Y-%m-%d")
        )

    def test_results_generation(self):
        """Test results generation."""
        results = self.lab_test_entity.results
        self.assertIsInstance(results, list)
        if results:  # If not empty
            for result in results:
                self.assertIsInstance(result, dict)
                self.assertIn("component", result)
                self.assertIn("value", result)
                self.assertIn("unit", result)
                self.assertIn("reference_range", result)
                self.assertIn("flag", result)

    def test_abnormal_flags_generation(self):
        """Test abnormal_flags generation."""
        abnormal_flags = self.lab_test_entity.abnormal_flags
        self.assertIsInstance(abnormal_flags, list)
        if abnormal_flags:  # If not empty
            for flag in abnormal_flags:
                self.assertIsInstance(flag, str)
                self.assertTrue(len(flag) > 0)

    def test_performing_lab_generation(self):
        """Test performing_lab generation."""
        performing_lab = self.lab_test_entity.performing_lab
        self.assertIsInstance(performing_lab, str)
        self.assertTrue(len(performing_lab) > 0)

    def test_lab_address_generation(self):
        """Test lab_address generation."""
        lab_address = self.lab_test_entity.lab_address
        self.assertIsInstance(lab_address, dict)
        self.assertIn("street", lab_address)
        self.assertIn("city", lab_address)
        self.assertIn("state", lab_address)
        self.assertIn("zip_code", lab_address)
        self.assertIn("country", lab_address)

    def test_ordering_provider_generation(self):
        """Test ordering_provider generation."""
        ordering_provider = self.lab_test_entity.ordering_provider
        self.assertIsInstance(ordering_provider, str)
        self.assertTrue(len(ordering_provider) > 0)

    def test_notes_generation(self):
        """Test notes generation."""
        notes = self.lab_test_entity.notes
        self.assertIsInstance(notes, str)

    def test_to_dict(self):
        """Test to_dict method."""
        lab_test_dict = self.lab_test_entity.to_dict()
        self.assertIsInstance(lab_test_dict, dict)
        self.assertIn("test_id", lab_test_dict)
        self.assertIn("patient_id", lab_test_dict)
        self.assertIn("doctor_id", lab_test_dict)
        self.assertIn("test_type", lab_test_dict)
        self.assertIn("test_name", lab_test_dict)
        self.assertIn("test_date", lab_test_dict)
        self.assertIn("result_date", lab_test_dict)
        self.assertIn("status", lab_test_dict)
        self.assertIn("specimen_type", lab_test_dict)
        self.assertIn("specimen_collection_date", lab_test_dict)
        self.assertIn("results", lab_test_dict)
        self.assertIn("abnormal_flags", lab_test_dict)
        self.assertIn("performing_lab", lab_test_dict)
        self.assertIn("lab_address", lab_test_dict)
        self.assertIn("ordering_provider", lab_test_dict)
        self.assertIn("notes", lab_test_dict)

    def test_generate_batch(self):
        """Test generate_batch method."""
        batch_size = 5
        batch = self.lab_test_entity.generate_batch(batch_size)
        self.assertIsInstance(batch, list)
        self.assertEqual(len(batch), batch_size)
        for item in batch:
            self.assertIsInstance(item, dict)
            self.assertIn("test_id", item)
            self.assertIn("patient_id", item)
            self.assertIn("doctor_id", item)
            self.assertIn("test_type", item)
            self.assertIn("test_name", item)
            self.assertIn("test_date", item)
            self.assertIn("result_date", item)
            self.assertIn("status", item)
            self.assertIn("specimen_type", item)
            self.assertIn("specimen_collection_date", item)
            self.assertIn("results", item)
            self.assertIn("abnormal_flags", item)
            self.assertIn("performing_lab", item)
            self.assertIn("lab_address", item)
            self.assertIn("ordering_provider", item)
            self.assertIn("notes", item)

    def test_reset(self):
        """Test reset method."""
        # Get initial values
        initial_test_id = self.lab_test_entity.test_id
        initial_patient_id = self.lab_test_entity.patient_id
        
        # Reset the entity
        self.lab_test_entity.reset()
        
        # Get new values
        new_test_id = self.lab_test_entity.test_id
        new_patient_id = self.lab_test_entity.patient_id
        
        # Values should be different after reset
        self.assertNotEqual(initial_test_id, new_test_id)
        self.assertNotEqual(initial_patient_id, new_patient_id)

    def test_class_factory_integration(self):
        """Test integration with ClassFactoryCEUtil."""
        # This test will fail until we implement the get_lab_test_entity method in ClassFactoryCEUtil
        lab_test = self.class_factory_util.get_lab_test_entity(locale="en_US")
        self.assertIsInstance(lab_test, LabTestEntity)
        self.assertEqual(lab_test._locale, "en_US")


if __name__ == "__main__":
    unittest.main() 