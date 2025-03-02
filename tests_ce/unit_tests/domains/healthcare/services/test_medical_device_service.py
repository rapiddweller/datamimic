# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import unittest
from unittest.mock import MagicMock, patch

from datamimic_ce.domains.healthcare.generators.medical_device_generator import MedicalDeviceGenerator
from datamimic_ce.domains.healthcare.models.medical_device import MedicalDevice
from datamimic_ce.domains.healthcare.services.medical_device_service import MedicalDeviceService


class TestMedicalDeviceService(unittest.TestCase):
    """Test case for the MedicalDeviceService class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock class factory util
        self.mock_class_factory_util = MagicMock()

        # Create a test instance
        self.service = MedicalDeviceService(class_factory_util=self.mock_class_factory_util)

    def test_initialization(self):
        """Test initialization of MedicalDeviceService."""
        self.assertEqual(self.service.class_factory_util, self.mock_class_factory_util)
        self.assertIsInstance(self.service.generator, MedicalDeviceGenerator)
        self.assertIsInstance(self.service._devices, dict)
        self.assertEqual(len(self.service._devices), 0)

    @patch("datamimic_ce.domains.healthcare.generators.medical_device_generator.MedicalDeviceGenerator.generate_device")
    def test_create_device(self, mock_generate_device):
        """Test creating a device."""
        # Setup mock
        mock_device = MagicMock(spec=MedicalDevice)
        mock_device.device_id = "DEV-12345678"
        mock_generate_device.return_value = mock_device

        # Call the method
        device = self.service.create_device(locale="en_US", dataset="test_dataset")

        # Verify the result
        self.assertEqual(device, mock_device)
        self.assertEqual(self.service._devices["DEV-12345678"], mock_device)
        mock_generate_device.assert_called_once_with(locale="en_US", dataset="test_dataset")

    def test_get_device(self):
        """Test getting a device by ID."""
        # Setup test data
        mock_device = MagicMock(spec=MedicalDevice)
        mock_device.device_id = "DEV-12345678"
        self.service._devices["DEV-12345678"] = mock_device

        # Call the method
        device = self.service.get_device("DEV-12345678")

        # Verify the result
        self.assertEqual(device, mock_device)

        # Test with non-existent ID
        device = self.service.get_device("DEV-99999999")
        self.assertIsNone(device)

    def test_get_all_devices(self):
        """Test getting all devices."""
        # Setup test data
        mock_device1 = MagicMock(spec=MedicalDevice)
        mock_device1.device_id = "DEV-12345678"
        mock_device2 = MagicMock(spec=MedicalDevice)
        mock_device2.device_id = "DEV-87654321"

        self.service._devices["DEV-12345678"] = mock_device1
        self.service._devices["DEV-87654321"] = mock_device2

        # Call the method
        devices = self.service.get_all_devices()

        # Verify the result
        self.assertEqual(len(devices), 2)
        self.assertIn(mock_device1, devices)
        self.assertIn(mock_device2, devices)

    @patch("datamimic_ce.domains.healthcare.generators.medical_device_generator.MedicalDeviceGenerator.generate_batch")
    def test_create_batch(self, mock_generate_batch):
        """Test creating a batch of devices."""
        # Setup mock
        mock_batch = [
            {"device_id": "DEV-12345678", "device_type": "Ventilator"},
            {"device_id": "DEV-87654321", "device_type": "MRI Scanner"},
        ]
        mock_generate_batch.return_value = mock_batch

        # Call the method without storing devices
        batch = self.service.create_batch(
            count=2,
            locale="en_US",
            dataset="test_dataset",
            device_types=["Ventilator", "MRI Scanner"],
            store_devices=False,
        )

        # Verify the result
        self.assertEqual(batch, mock_batch)
        self.assertEqual(len(self.service._devices), 0)  # No devices stored

        # Call the method with storing devices
        batch = self.service.create_batch(
            count=2,
            locale="en_US",
            dataset="test_dataset",
            device_types=["Ventilator", "MRI Scanner"],
            store_devices=True,
        )

        # Verify the result
        self.assertEqual(batch, mock_batch)
        self.assertEqual(len(self.service._devices), 2)  # Devices stored
        self.assertIn("DEV-12345678", self.service._devices)
        self.assertIn("DEV-87654321", self.service._devices)

    @patch(
        "datamimic_ce.domains.healthcare.generators.medical_device_generator.MedicalDeviceGenerator.generate_related_devices"
    )
    def test_create_related_devices(self, mock_generate_related):
        """Test creating related devices."""
        # Setup mock
        mock_related = [
            {"device_id": "DEV-12345678", "manufacturer": "MedTech Inc."},
            {"device_id": "DEV-87654321", "manufacturer": "MedTech Inc."},
        ]
        mock_generate_related.return_value = mock_related

        # Call the method without storing devices
        related = self.service.create_related_devices(
            count=2, locale="en_US", dataset="test_dataset", same_manufacturer=True, store_devices=False
        )

        # Verify the result
        self.assertEqual(related, mock_related)
        self.assertEqual(len(self.service._devices), 0)  # No devices stored

        # Call the method with storing devices
        related = self.service.create_related_devices(
            count=2, locale="en_US", dataset="test_dataset", same_manufacturer=True, store_devices=True
        )

        # Verify the result
        self.assertEqual(related, mock_related)
        self.assertEqual(len(self.service._devices), 2)  # Devices stored
        self.assertIn("DEV-12345678", self.service._devices)
        self.assertIn("DEV-87654321", self.service._devices)

    @patch(
        "datamimic_ce.domains.healthcare.generators.medical_device_generator.MedicalDeviceGenerator.generate_device_family"
    )
    def test_create_device_family(self, mock_generate_family):
        """Test creating a device family."""
        # Setup mock
        mock_family = [
            {"device_id": "DEV-12345678", "model_number": "AB1000"},
            {"device_id": "DEV-87654321", "model_number": "AB1001"},
        ]
        mock_generate_family.return_value = mock_family

        # Call the method without storing devices
        family = self.service.create_device_family(
            family_size=2, locale="en_US", dataset="test_dataset", device_type="Ventilator", store_devices=False
        )

        # Verify the result
        self.assertEqual(family, mock_family)
        self.assertEqual(len(self.service._devices), 0)  # No devices stored

        # Call the method with storing devices
        family = self.service.create_device_family(
            family_size=2, locale="en_US", dataset="test_dataset", device_type="Ventilator", store_devices=True
        )

        # Verify the result
        self.assertEqual(family, mock_family)
        self.assertEqual(len(self.service._devices), 2)  # Devices stored
        self.assertIn("DEV-12345678", self.service._devices)
        self.assertIn("DEV-87654321", self.service._devices)

    def test_filter_devices_by_type(self):
        """Test filtering devices by type."""
        # Setup test data
        mock_device1 = MagicMock(spec=MedicalDevice)
        mock_device1.device_id = "DEV-12345678"
        mock_device1.device_type = "Ventilator"

        mock_device2 = MagicMock(spec=MedicalDevice)
        mock_device2.device_id = "DEV-87654321"
        mock_device2.device_type = "MRI Scanner"

        mock_device3 = MagicMock(spec=MedicalDevice)
        mock_device3.device_id = "DEV-11111111"
        mock_device3.device_type = "Ventilator"

        self.service._devices = {
            "DEV-12345678": mock_device1,
            "DEV-87654321": mock_device2,
            "DEV-11111111": mock_device3,
        }

        # Call the method
        ventilators = self.service.filter_devices_by_type("Ventilator")
        mri_scanners = self.service.filter_devices_by_type("MRI Scanner")
        ultrasounds = self.service.filter_devices_by_type("Ultrasound")

        # Verify the results
        self.assertEqual(len(ventilators), 2)
        self.assertIn(mock_device1, ventilators)
        self.assertIn(mock_device3, ventilators)

        self.assertEqual(len(mri_scanners), 1)
        self.assertIn(mock_device2, mri_scanners)

        self.assertEqual(len(ultrasounds), 0)

    def test_filter_devices_by_manufacturer(self):
        """Test filtering devices by manufacturer."""
        # Setup test data
        mock_device1 = MagicMock(spec=MedicalDevice)
        mock_device1.device_id = "DEV-12345678"
        mock_device1.manufacturer = "MedTech Inc."

        mock_device2 = MagicMock(spec=MedicalDevice)
        mock_device2.device_id = "DEV-87654321"
        mock_device2.manufacturer = "HealthCare Systems"

        mock_device3 = MagicMock(spec=MedicalDevice)
        mock_device3.device_id = "DEV-11111111"
        mock_device3.manufacturer = "MedTech Inc."

        self.service._devices = {
            "DEV-12345678": mock_device1,
            "DEV-87654321": mock_device2,
            "DEV-11111111": mock_device3,
        }

        # Call the method
        medtech_devices = self.service.filter_devices_by_manufacturer("MedTech Inc.")
        healthcare_devices = self.service.filter_devices_by_manufacturer("HealthCare Systems")
        biomed_devices = self.service.filter_devices_by_manufacturer("BioMed Solutions")

        # Verify the results
        self.assertEqual(len(medtech_devices), 2)
        self.assertIn(mock_device1, medtech_devices)
        self.assertIn(mock_device3, medtech_devices)

        self.assertEqual(len(healthcare_devices), 1)
        self.assertIn(mock_device2, healthcare_devices)

        self.assertEqual(len(biomed_devices), 0)

    def test_filter_devices_by_status(self):
        """Test filtering devices by status."""
        # Setup test data
        mock_device1 = MagicMock(spec=MedicalDevice)
        mock_device1.device_id = "DEV-12345678"
        mock_device1.status = "Active"

        mock_device2 = MagicMock(spec=MedicalDevice)
        mock_device2.device_id = "DEV-87654321"
        mock_device2.status = "Maintenance"

        mock_device3 = MagicMock(spec=MedicalDevice)
        mock_device3.device_id = "DEV-11111111"
        mock_device3.status = "Active"

        self.service._devices = {
            "DEV-12345678": mock_device1,
            "DEV-87654321": mock_device2,
            "DEV-11111111": mock_device3,
        }

        # Call the method
        active_devices = self.service.filter_devices_by_status("Active")
        maintenance_devices = self.service.filter_devices_by_status("Maintenance")
        retired_devices = self.service.filter_devices_by_status("Retired")

        # Verify the results
        self.assertEqual(len(active_devices), 2)
        self.assertIn(mock_device1, active_devices)
        self.assertIn(mock_device3, active_devices)

        self.assertEqual(len(maintenance_devices), 1)
        self.assertIn(mock_device2, maintenance_devices)

        self.assertEqual(len(retired_devices), 0)

    def test_filter_devices_by_location(self):
        """Test filtering devices by location."""
        # Setup test data
        mock_device1 = MagicMock(spec=MedicalDevice)
        mock_device1.device_id = "DEV-12345678"
        mock_device1.location = "Operating Room"

        mock_device2 = MagicMock(spec=MedicalDevice)
        mock_device2.device_id = "DEV-87654321"
        mock_device2.location = "ICU"

        mock_device3 = MagicMock(spec=MedicalDevice)
        mock_device3.device_id = "DEV-11111111"
        mock_device3.location = "Operating Room"

        self.service._devices = {
            "DEV-12345678": mock_device1,
            "DEV-87654321": mock_device2,
            "DEV-11111111": mock_device3,
        }

        # Call the method
        or_devices = self.service.filter_devices_by_location("Operating Room")
        icu_devices = self.service.filter_devices_by_location("ICU")
        er_devices = self.service.filter_devices_by_location("Emergency Department")

        # Verify the results
        self.assertEqual(len(or_devices), 2)
        self.assertIn(mock_device1, or_devices)
        self.assertIn(mock_device3, or_devices)

        self.assertEqual(len(icu_devices), 1)
        self.assertIn(mock_device2, icu_devices)

        self.assertEqual(len(er_devices), 0)

    @patch(
        "datamimic_ce.domains.healthcare.data_loaders.medical_device_loader.MedicalDeviceDataLoader.load_device_types"
    )
    def test_get_device_types(self, mock_load_device_types):
        """Test getting device types."""
        # Setup mock
        mock_load_device_types.return_value = ["Ventilator", "MRI Scanner", "X-Ray Machine"]

        # Call the method
        device_types = self.service.get_device_types(country_code="US")

        # Verify the result
        self.assertEqual(device_types, ["Ventilator", "MRI Scanner", "X-Ray Machine"])
        mock_load_device_types.assert_called_once()

    @patch(
        "datamimic_ce.domains.healthcare.data_loaders.medical_device_loader.MedicalDeviceDataLoader.load_manufacturers"
    )
    def test_get_manufacturers(self, mock_load_manufacturers):
        """Test getting manufacturers."""
        # Setup mock
        mock_load_manufacturers.return_value = ["MedTech Inc.", "HealthCare Systems"]

        # Call the method
        manufacturers = self.service.get_manufacturers(country_code="US")

        # Verify the result
        self.assertEqual(manufacturers, ["MedTech Inc.", "HealthCare Systems"])
        mock_load_manufacturers.assert_called_once()

    @patch("datamimic_ce.domains.healthcare.data_loaders.medical_device_loader.MedicalDeviceDataLoader.load_locations")
    def test_get_locations(self, mock_load_locations):
        """Test getting locations."""
        # Setup mock
        mock_load_locations.return_value = ["Operating Room", "ICU", "Emergency Department"]

        # Call the method
        locations = self.service.get_locations(country_code="US")

        # Verify the result
        self.assertEqual(locations, ["Operating Room", "ICU", "Emergency Department"])
        mock_load_locations.assert_called_once()

    @patch("datamimic_ce.domains.healthcare.data_loaders.medical_device_loader.MedicalDeviceDataLoader.load_statuses")
    def test_get_statuses(self, mock_load_statuses):
        """Test getting statuses."""
        # Setup mock
        mock_load_statuses.return_value = ["Active", "Maintenance", "Retired", "Defective"]

        # Call the method
        statuses = self.service.get_statuses()

        # Verify the result
        self.assertEqual(statuses, ["Active", "Maintenance", "Retired", "Defective"])
        mock_load_statuses.assert_called_once()

    def test_clear_devices(self):
        """Test clearing devices."""
        # Setup test data
        mock_device1 = MagicMock(spec=MedicalDevice)
        mock_device1.device_id = "DEV-12345678"

        mock_device2 = MagicMock(spec=MedicalDevice)
        mock_device2.device_id = "DEV-87654321"

        self.service._devices = {"DEV-12345678": mock_device1, "DEV-87654321": mock_device2}

        # Verify initial state
        self.assertEqual(len(self.service._devices), 2)

        # Call the method
        self.service.clear_devices()

        # Verify the result
        self.assertEqual(len(self.service._devices), 0)


if __name__ == "__main__":
    unittest.main()
