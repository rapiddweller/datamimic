# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Test cases for the DoctorEntity class.
"""

import unittest
from pathlib import Path

from datamimic_ce.entities.healthcare.doctor_entity import DoctorEntity
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestDoctorEntity(unittest.TestCase):
    """Test cases for the DoctorEntity class."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()
        self.doctor_entity = DoctorEntity(self.class_factory_util)

    def test_init(self):
        """Test initialization of DoctorEntity."""
        self.assertEqual(self.doctor_entity._locale, "en")
        self.assertIsNone(self.doctor_entity._dataset)

    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        doctor_entity = DoctorEntity(
            self.class_factory_util,
            locale="de",
            dataset="test_dataset"
        )
        self.assertEqual(doctor_entity._locale, "de")
        self.assertEqual(doctor_entity._dataset, "test_dataset")

    def test_doctor_id_generation(self):
        """Test doctor_id generation."""
        doctor_id = self.doctor_entity.doctor_id
        self.assertIsInstance(doctor_id, str)
        self.assertTrue(len(doctor_id) > 0)
        # Check if it follows the expected format (e.g., "DR-12345678")
        self.assertRegex(doctor_id, r"DR-\d+")

    def test_first_name_generation(self):
        """Test first_name generation."""
        first_name = self.doctor_entity.first_name
        self.assertIsInstance(first_name, str)
        self.assertTrue(len(first_name) > 0)

    def test_last_name_generation(self):
        """Test last_name generation."""
        last_name = self.doctor_entity.last_name
        self.assertIsInstance(last_name, str)
        self.assertTrue(len(last_name) > 0)

    def test_specialty_generation(self):
        """Test specialty generation."""
        specialty = self.doctor_entity.specialty
        self.assertIsInstance(specialty, str)
        self.assertTrue(len(specialty) > 0)
        
        # Check if the specialties CSV file exists and contains the specialty
        specialties = []
        data_dir = Path(__file__).parent.parent.parent.parent.parent / "datamimic_ce" / "entities" / "data" / "medical"
        
        # Try different files in order of preference
        specialty_files = [
            data_dir / f"specialties_{self.doctor_entity._country_code}.csv",
            data_dir / "specialties_US.csv",
            data_dir / "specialties.csv"
        ]
        
        for file_path in specialty_files:
            if file_path.exists():
                try:
                    with open(file_path, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if "," in line:
                                parts = line.split(",", 1)
                                if parts[0].strip():
                                    specialties.append(parts[0].strip())
                            elif line:
                                specialties.append(line)
                except Exception:
                    pass
                break
        
        # If we found specialties in the CSV file, check that the generated specialty is among them
        if specialties:
            self.assertIn(specialty, specialties)

    def test_license_number_generation(self):
        """Test license_number generation."""
        license_number = self.doctor_entity.license_number
        self.assertIsInstance(license_number, str)
        self.assertTrue(len(license_number) > 0)
        # Check if it follows the expected format (now state code followed by dash and number)
        self.assertRegex(license_number, r"[A-Z]{2}-\d{6}")

    def test_npi_number_generation(self):
        """Test npi_number generation."""
        npi_number = self.doctor_entity.npi_number
        self.assertIsInstance(npi_number, str)
        self.assertTrue(len(npi_number) > 0)
        # Check if it's a 10-digit number
        self.assertRegex(npi_number, r"\d{10}")

    def test_contact_number_generation(self):
        """Test contact_number generation."""
        contact_number = self.doctor_entity.contact_number
        self.assertIsInstance(contact_number, str)
        self.assertTrue(len(contact_number) > 0)
        # Check if it follows a phone number pattern
        self.assertRegex(contact_number, r"\(\d{3}\) \d{3}-\d{4}")

    def test_email_generation(self):
        """Test email generation."""
        email = self.doctor_entity.email
        self.assertIsInstance(email, str)
        self.assertIn("@", email)
        self.assertIn(".", email)
        # Check if it follows a basic email pattern
        self.assertRegex(email, r"[^@]+@[^@]+\.[^@]+")

    def test_hospital_affiliation_generation(self):
        """Test hospital_affiliation generation."""
        hospital_affiliation = self.doctor_entity.hospital_affiliation
        self.assertIsInstance(hospital_affiliation, str)
        self.assertTrue(len(hospital_affiliation) > 0)

    def test_office_address_generation(self):
        """Test office_address generation."""
        office_address = self.doctor_entity.office_address
        self.assertIsInstance(office_address, dict)
        self.assertIn("street", office_address)
        self.assertIn("city", office_address)
        self.assertIn("state", office_address)
        self.assertIn("zip_code", office_address)
        self.assertIn("country", office_address)

    def test_education_generation(self):
        """Test education generation."""
        education = self.doctor_entity.education
        self.assertIsInstance(education, list)
        if education:  # If not empty
            for edu in education:
                self.assertIsInstance(edu, dict)
                self.assertIn("degree", edu)
                self.assertIn("institution", edu)
                self.assertIn("year", edu)
                # May or may not have honors
                if "honors" in edu:
                    self.assertIsInstance(edu["honors"], str)

    def test_certifications_generation(self):
        """Test certifications generation."""
        certifications = self.doctor_entity.certifications
        self.assertIsInstance(certifications, list)
        if certifications:  # If not empty
            for cert in certifications:
                self.assertIsInstance(cert, dict)
                self.assertIn("name", cert)
                self.assertIn("issue_date", cert)
                self.assertIn("expiry_date", cert)
                # Verify dates are ISO format (YYYY-MM-DD)
                self.assertRegex(cert["issue_date"], r"\d{4}-\d{2}-\d{2}")
                self.assertRegex(cert["expiry_date"], r"\d{4}-\d{2}-\d{2}")

    def test_languages_generation(self):
        """Test languages generation."""
        languages = self.doctor_entity.languages
        self.assertIsInstance(languages, list)
        if languages:  # If not empty
            for lang in languages:
                self.assertIsInstance(lang, str)
                self.assertTrue(len(lang) > 0)

    def test_schedule_generation(self):
        """Test schedule generation."""
        schedule = self.doctor_entity.schedule
        self.assertIsInstance(schedule, dict)
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in days:
            self.assertIn(day, schedule)
            self.assertIsInstance(schedule[day], list)
            for time_slot in schedule[day]:
                self.assertIsInstance(time_slot, str)
                # Should either be a time range (e.g., "9:00 AM - 5:00 PM") or "Not Available"
                if time_slot != "Not Available":
                    self.assertRegex(time_slot, r"\d{1,2}:\d{2} [AP]M - \d{1,2}:\d{2} [AP]M")

    def test_accepting_new_patients_generation(self):
        """Test accepting_new_patients generation."""
        accepting_new_patients = self.doctor_entity.accepting_new_patients
        self.assertIsInstance(accepting_new_patients, bool)

    def test_to_dict(self):
        """Test to_dict method."""
        doctor_dict = self.doctor_entity.to_dict()
        self.assertIsInstance(doctor_dict, dict)
        self.assertIn("doctor_id", doctor_dict)
        self.assertIn("first_name", doctor_dict)
        self.assertIn("last_name", doctor_dict)
        self.assertIn("specialty", doctor_dict)
        self.assertIn("license_number", doctor_dict)
        self.assertIn("npi_number", doctor_dict)
        self.assertIn("contact_number", doctor_dict)
        self.assertIn("email", doctor_dict)
        self.assertIn("hospital_affiliation", doctor_dict)
        self.assertIn("office_address", doctor_dict)
        self.assertIn("education", doctor_dict)
        self.assertIn("certifications", doctor_dict)
        self.assertIn("languages", doctor_dict)
        self.assertIn("schedule", doctor_dict)
        self.assertIn("accepting_new_patients", doctor_dict)

    def test_generate_batch(self):
        """Test generate_batch method."""
        batch_size = 5
        batch = self.doctor_entity.generate_batch(batch_size)
        self.assertIsInstance(batch, list)
        self.assertEqual(len(batch), batch_size)
        for item in batch:
            self.assertIsInstance(item, dict)
            self.assertIn("doctor_id", item)
            self.assertIn("first_name", item)
            self.assertIn("last_name", item)
            self.assertIn("specialty", item)
            self.assertIn("license_number", item)
            self.assertIn("npi_number", item)
            self.assertIn("contact_number", item)
            self.assertIn("email", item)
            self.assertIn("hospital_affiliation", item)
            self.assertIn("office_address", item)
            self.assertIn("education", item)
            self.assertIn("certifications", item)
            self.assertIn("languages", item)
            self.assertIn("schedule", item)
            self.assertIn("accepting_new_patients", item)

    def test_reset(self):
        """Test reset method."""
        # Get initial values
        initial_doctor_id = self.doctor_entity.doctor_id
        initial_first_name = self.doctor_entity.first_name
        
        # Reset the entity
        self.doctor_entity.reset()
        
        # Get new values
        new_doctor_id = self.doctor_entity.doctor_id
        new_first_name = self.doctor_entity.first_name
        
        # Values should be different after reset
        self.assertNotEqual(initial_doctor_id, new_doctor_id)
        self.assertNotEqual(initial_first_name, new_first_name)

    def test_class_factory_integration(self):
        """Test integration with ClassFactoryCEUtil."""
        # This test will fail until we implement the get_doctor_entity method in ClassFactoryCEUtil
        doctor = self.class_factory_util.get_doctor_entity(locale="en_US")
        self.assertIsInstance(doctor, DoctorEntity)
        # The locale is stored as the base language code
        self.assertEqual(doctor._locale.split('_')[0], "en")


if __name__ == "__main__":
    unittest.main() 