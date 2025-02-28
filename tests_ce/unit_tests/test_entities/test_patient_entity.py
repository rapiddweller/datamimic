# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import unittest
from datetime import datetime

from datamimic_ce.entities.patient_entity import PatientEntity
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestPatientEntity(unittest.TestCase):
    """Test cases for the PatientEntity class."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()
        self.patient_entity = PatientEntity(self.class_factory_util)

    def test_init(self):
        """Test initialization of PatientEntity."""
        self.assertEqual(self.patient_entity._locale, "en")
        self.assertIsNone(self.patient_entity._dataset)

    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        patient_entity = PatientEntity(
            self.class_factory_util,
            locale="de",
            dataset="test_dataset"
        )
        self.assertEqual(patient_entity._locale, "de")
        self.assertEqual(patient_entity._dataset, "test_dataset")

    def test_patient_id_generation(self):
        """Test patient_id generation."""
        patient_id = self.patient_entity.patient_id
        self.assertIsInstance(patient_id, str)
        self.assertTrue(len(patient_id) > 0)
        # Check if it follows the expected format (e.g., "P-12345678")
        self.assertRegex(patient_id, r"P-\d+")

    def test_first_name_generation(self):
        """Test first_name generation."""
        first_name = self.patient_entity.first_name
        self.assertIsInstance(first_name, str)
        self.assertTrue(len(first_name) > 0)

    def test_last_name_generation(self):
        """Test last_name generation."""
        last_name = self.patient_entity.last_name
        self.assertIsInstance(last_name, str)
        self.assertTrue(len(last_name) > 0)

    def test_date_of_birth_generation(self):
        """Test date_of_birth generation."""
        date_of_birth = self.patient_entity.date_of_birth
        self.assertIsInstance(date_of_birth, str)
        # Check if it's a valid date string (YYYY-MM-DD)
        self.assertRegex(date_of_birth, r"\d{4}-\d{2}-\d{2}")
        # Validate it's a real date
        try:
            datetime.strptime(date_of_birth, "%Y-%m-%d")
        except ValueError:
            self.fail("date_of_birth is not a valid date")

    def test_gender_generation(self):
        """Test gender generation."""
        gender = self.patient_entity.gender
        self.assertIsInstance(gender, str)
        self.assertIn(gender, PatientEntity.GENDERS)

    def test_blood_type_generation(self):
        """Test blood_type generation."""
        blood_type = self.patient_entity.blood_type
        self.assertIsInstance(blood_type, str)
        self.assertIn(blood_type, PatientEntity.BLOOD_TYPES)

    def test_contact_number_generation(self):
        """Test contact_number generation."""
        contact_number = self.patient_entity.contact_number
        self.assertIsInstance(contact_number, str)
        self.assertTrue(len(contact_number) > 0)
        # Check if it follows a phone number pattern
        self.assertRegex(contact_number, r"\(\d{3}\) \d{3}-\d{4}")

    def test_email_generation(self):
        """Test email generation."""
        email = self.patient_entity.email
        self.assertIsInstance(email, str)
        self.assertIn("@", email)
        self.assertIn(".", email)
        # Check if it follows a basic email pattern
        self.assertRegex(email, r"[^@]+@[^@]+\.[^@]+")

    def test_address_generation(self):
        """Test address generation."""
        address = self.patient_entity.address
        self.assertIsInstance(address, dict)
        self.assertIn("street", address)
        self.assertIn("city", address)
        self.assertIn("state", address)
        self.assertIn("zip_code", address)
        self.assertIn("country", address)

    def test_insurance_provider_generation(self):
        """Test insurance_provider generation."""
        insurance_provider = self.patient_entity.insurance_provider
        self.assertIsInstance(insurance_provider, str)
        self.assertTrue(len(insurance_provider) > 0)

    def test_insurance_policy_number_generation(self):
        """Test insurance_policy_number generation."""
        insurance_policy_number = self.patient_entity.insurance_policy_number
        self.assertIsInstance(insurance_policy_number, str)
        self.assertTrue(len(insurance_policy_number) > 0)

    def test_emergency_contact_generation(self):
        """Test emergency_contact generation."""
        emergency_contact = self.patient_entity.emergency_contact
        self.assertIsInstance(emergency_contact, dict)
        self.assertIn("name", emergency_contact)
        self.assertIn("relationship", emergency_contact)
        self.assertIn("phone", emergency_contact)

    def test_medical_history_generation(self):
        """Test medical_history generation."""
        medical_history = self.patient_entity.medical_history
        self.assertIsInstance(medical_history, list)
        if medical_history:  # If not empty
            for condition in medical_history:
                self.assertIsInstance(condition, dict)
                self.assertIn("condition", condition)
                self.assertIn("diagnosed_date", condition)
                self.assertIn("status", condition)

    def test_allergies_generation(self):
        """Test allergies generation."""
        allergies = self.patient_entity.allergies
        self.assertIsInstance(allergies, list)
        if allergies:  # If not empty
            for allergy in allergies:
                self.assertIsInstance(allergy, dict)
                self.assertIn("allergen", allergy)
                self.assertIn("severity", allergy)
                self.assertIn("reaction", allergy)

    def test_medications_generation(self):
        """Test medications generation."""
        medications = self.patient_entity.medications
        self.assertIsInstance(medications, list)
        if medications:  # If not empty
            for medication in medications:
                self.assertIsInstance(medication, dict)
                self.assertIn("name", medication)
                self.assertIn("dosage", medication)
                self.assertIn("frequency", medication)
                self.assertIn("start_date", medication)

    def test_to_dict(self):
        """Test to_dict method."""
        patient_dict = self.patient_entity.to_dict()
        self.assertIsInstance(patient_dict, dict)
        self.assertIn("patient_id", patient_dict)
        self.assertIn("first_name", patient_dict)
        self.assertIn("last_name", patient_dict)
        self.assertIn("date_of_birth", patient_dict)
        self.assertIn("gender", patient_dict)
        self.assertIn("blood_type", patient_dict)
        self.assertIn("contact_number", patient_dict)
        self.assertIn("email", patient_dict)
        self.assertIn("address", patient_dict)
        self.assertIn("insurance_provider", patient_dict)
        self.assertIn("insurance_policy_number", patient_dict)
        self.assertIn("emergency_contact", patient_dict)
        self.assertIn("medical_history", patient_dict)
        self.assertIn("allergies", patient_dict)
        self.assertIn("medications", patient_dict)

    def test_generate_batch(self):
        """Test generate_batch method."""
        batch_size = 5
        batch = self.patient_entity.generate_batch(batch_size)
        self.assertIsInstance(batch, list)
        self.assertEqual(len(batch), batch_size)
        for item in batch:
            self.assertIsInstance(item, dict)
            self.assertIn("patient_id", item)
            self.assertIn("first_name", item)
            self.assertIn("last_name", item)
            self.assertIn("date_of_birth", item)
            self.assertIn("gender", item)
            self.assertIn("blood_type", item)
            self.assertIn("contact_number", item)
            self.assertIn("email", item)
            self.assertIn("address", item)
            self.assertIn("insurance_provider", item)
            self.assertIn("insurance_policy_number", item)
            self.assertIn("emergency_contact", item)
            self.assertIn("medical_history", item)
            self.assertIn("allergies", item)
            self.assertIn("medications", item)

    def test_reset(self):
        """Test reset method."""
        # Get initial values
        initial_patient_id = self.patient_entity.patient_id
        initial_first_name = self.patient_entity.first_name
        
        # Reset the entity
        self.patient_entity.reset()
        
        # Get new values
        new_patient_id = self.patient_entity.patient_id
        new_first_name = self.patient_entity.first_name
        
        # Values should be different after reset
        self.assertNotEqual(initial_patient_id, new_patient_id)
        self.assertNotEqual(initial_first_name, new_first_name)

    def test_class_factory_integration(self):
        """Test integration with ClassFactoryCEUtil."""
        # This test will fail until we implement the get_patient_entity method in ClassFactoryCEUtil
        patient = self.class_factory_util.get_patient_entity(locale="en_US")
        self.assertIsInstance(patient, PatientEntity)
        # The locale is stored as the base language code
        self.assertEqual(patient._locale.split('_')[0], "en")


if __name__ == "__main__":
    unittest.main() 