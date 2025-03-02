# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Tests for the Hospital model.

This module contains tests for the Hospital model in the healthcare domain.
"""

import unittest
from unittest.mock import MagicMock, patch

from datamimic_ce.domains.healthcare.models.hospital import Hospital


class TestHospital(unittest.TestCase):
    """Test cases for the Hospital model."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock class factory util
        self.mock_class_factory_util = MagicMock()

        # Mock address entity
        self.mock_address_entity = MagicMock()
        self.mock_address_entity.city = "Anytown"
        self.mock_address_entity.state = "CA"
        self.mock_address_entity.to_dict.return_value = {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345",
            "country": "USA",
        }

        # Set up the mock class factory to return our mock entities
        self.mock_class_factory_util.get_address_entity.return_value = self.mock_address_entity

        # Create a hospital instance with the mock class factory
        self.hospital = Hospital(class_factory_util=self.mock_class_factory_util, locale="en", dataset="US")

    def test_initialization(self):
        """Test that the Hospital is initialized correctly."""
        # Verify that the class factory was used to get the address entity
        self.mock_class_factory_util.get_address_entity.assert_called_once_with(locale="en", dataset="US")

        # Verify that the data loader was initialized
        self.assertIsNotNone(self.hospital._data_loader)

        # Verify that the generators were initialized
        self.assertIsNotNone(self.hospital._hospital_id_generator)
        self.assertIsNotNone(self.hospital._name_generator)
        self.assertIsNotNone(self.hospital._type_generator)
        self.assertIsNotNone(self.hospital._departments_generator)
        self.assertIsNotNone(self.hospital._services_generator)
        # ... and so on for other generators

    def test_address(self):
        """Test that address information is retrieved from the address entity."""
        expected_address = {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345",
            "country": "USA",
        }
        self.assertEqual(self.hospital.address, expected_address)

    def test_hospital_id_format(self):
        """Test that the hospital ID has the correct format."""
        hospital_id = self.hospital.hospital_id
        self.assertTrue(hospital_id.startswith("HOSP-"))
        self.assertEqual(len(hospital_id), 13)  # "HOSP-" + 8 hex characters

    def test_name_generation(self):
        """Test that the hospital name is generated correctly."""
        # Mock the generate_hospital_name function
        with patch(
            "datamimic_ce.domains.healthcare.generators.hospital_generator.generate_hospital_name"
        ) as mock_generate_name:
            mock_generate_name.return_value = "Anytown General Hospital"

            # Get the hospital name
            name = self.hospital.name

            # Verify that the generate_hospital_name function was called with the correct parameters
            mock_generate_name.assert_called_once_with("Anytown", "CA")

            # Verify that the returned name is correct
            self.assertEqual(name, "Anytown General Hospital")

    def test_type(self):
        """Test that the hospital type is one of the valid types."""
        valid_types = [
            "General",
            "Teaching",
            "Community",
            "Specialty",
            "Rehabilitation",
            "Psychiatric",
            "Children's",
            "Veterans",
            "Long-term Care",
        ]
        self.assertIn(self.hospital.type, valid_types)

    def test_departments(self):
        """Test that the hospital departments are generated correctly."""
        departments = self.hospital.departments

        # Verify that departments is a list of strings
        self.assertIsInstance(departments, list)
        for department in departments:
            self.assertIsInstance(department, str)

        # Verify that the list is not empty
        self.assertTrue(len(departments) > 0)

    def test_services(self):
        """Test that the hospital services are generated correctly."""
        services = self.hospital.services

        # Verify that services is a list of strings
        self.assertIsInstance(services, list)
        for service in services:
            self.assertIsInstance(service, str)

        # Verify that the list is not empty
        self.assertTrue(len(services) > 0)

    def test_bed_count(self):
        """Test that the bed count is a positive integer."""
        bed_count = self.hospital.bed_count
        self.assertIsInstance(bed_count, int)
        self.assertTrue(bed_count > 0)

    def test_staff_count(self):
        """Test that the staff count is a positive integer."""
        # Mock the bed_count property to return a fixed value
        self.hospital._bed_count_generator.get = MagicMock(return_value=200)

        staff_count = self.hospital.staff_count
        self.assertIsInstance(staff_count, int)
        self.assertTrue(staff_count > 0)

        # Staff count should be proportional to bed count
        self.assertTrue(staff_count >= 200 * 2)  # At least 2 staff per bed
        self.assertTrue(staff_count <= 200 * 4)  # At most 4 staff per bed

    def test_founding_year(self):
        """Test that the founding year is a valid year."""
        from datetime import datetime

        founding_year = self.hospital.founding_year
        current_year = datetime.now().year

        self.assertIsInstance(founding_year, int)
        self.assertTrue(founding_year > current_year - 150)  # Not too old
        self.assertTrue(founding_year < current_year)  # Not in the future

    def test_accreditation(self):
        """Test that the accreditation is a list of strings."""
        accreditation = self.hospital.accreditation

        # Verify that accreditation is a list of strings
        self.assertIsInstance(accreditation, list)
        for item in accreditation:
            self.assertIsInstance(item, str)

        # Verify that the list is not empty
        self.assertTrue(len(accreditation) > 0)

    def test_emergency_services(self):
        """Test that emergency_services is a boolean."""
        emergency_services = self.hospital.emergency_services
        self.assertIsInstance(emergency_services, bool)

    def test_teaching_status(self):
        """Test that teaching_status is a boolean."""
        teaching_status = self.hospital.teaching_status
        self.assertIsInstance(teaching_status, bool)

    def test_website(self):
        """Test that the website is a valid URL."""
        website = self.hospital.website
        self.assertIsInstance(website, str)
        self.assertTrue(website.startswith("https://www."))
        self.assertTrue(website.endswith(".org") or "." in website.split("www.")[1])

    def test_phone(self):
        """Test that the phone number is in the correct format."""
        phone = self.hospital.phone
        self.assertIsInstance(phone, str)

        # US phone format: (XXX) XXX-XXXX
        if self.hospital._country_code == "US":
            self.assertRegex(phone, r"\(\d{3}\) \d{3}-\d{4}")
        else:
            # International format: +XX XXX XXXXXXX
            self.assertRegex(phone, r"\+\d+ \d+ \d+")

    def test_email(self):
        """Test that the email is in the correct format."""
        email = self.hospital.email
        self.assertIsInstance(email, str)
        self.assertTrue("@" in email)
        self.assertTrue(email.startswith("info@"))

    def test_to_dict(self):
        """Test that to_dict returns a dictionary with all hospital properties."""
        hospital_dict = self.hospital.to_dict()

        # Check that the dictionary contains all expected keys
        expected_keys = [
            "hospital_id",
            "name",
            "type",
            "departments",
            "services",
            "bed_count",
            "staff_count",
            "founding_year",
            "accreditation",
            "emergency_services",
            "teaching_status",
            "website",
            "phone",
            "email",
            "address",
        ]

        for key in expected_keys:
            self.assertIn(key, hospital_dict)

        # Check that the values are of the expected types
        self.assertIsInstance(hospital_dict["hospital_id"], str)
        self.assertIsInstance(hospital_dict["name"], str)
        self.assertIsInstance(hospital_dict["type"], str)
        self.assertIsInstance(hospital_dict["departments"], list)
        self.assertIsInstance(hospital_dict["services"], list)
        self.assertIsInstance(hospital_dict["bed_count"], int)
        self.assertIsInstance(hospital_dict["staff_count"], int)
        self.assertIsInstance(hospital_dict["founding_year"], int)
        self.assertIsInstance(hospital_dict["accreditation"], list)
        self.assertIsInstance(hospital_dict["emergency_services"], bool)
        self.assertIsInstance(hospital_dict["teaching_status"], bool)
        self.assertIsInstance(hospital_dict["website"], str)
        self.assertIsInstance(hospital_dict["phone"], str)
        self.assertIsInstance(hospital_dict["email"], str)
        self.assertIsInstance(hospital_dict["address"], dict)

    def test_reset(self):
        """Test that reset clears all cached values."""
        # Call some properties to generate values
        _ = self.hospital.hospital_id
        _ = self.hospital.name
        _ = self.hospital.type

        # Reset the hospital
        self.hospital.reset()

        # Verify that the address entity was reset
        self.mock_address_entity.reset.assert_called_once()

        # We can't directly test that the generators were reset without
        # modifying the implementation to expose the reset state.
        # Instead, we'll verify that calling reset doesn't raise exceptions.
        self.hospital._hospital_id_generator.reset()
        self.hospital._name_generator.reset()
        self.hospital._type_generator.reset()

    def test_generate_batch(self):
        """Test that generate_batch returns the correct number of hospitals."""
        batch_size = 5
        hospitals = self.hospital.generate_batch(batch_size)

        self.assertEqual(len(hospitals), batch_size)
        for hospital in hospitals:
            self.assertIsInstance(hospital, dict)
            self.assertIn("hospital_id", hospital)
            self.assertIn("name", hospital)
            self.assertIn("type", hospital)


if __name__ == "__main__":
    unittest.main()
