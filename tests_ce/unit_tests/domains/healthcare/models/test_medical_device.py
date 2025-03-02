# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import re
import unittest
from unittest.mock import MagicMock, patch

from datamimic_ce.domains.healthcare.models.medical_device import MedicalDevice


class TestMedicalDevice(unittest.TestCase):
    """Test case for the MedicalDevice class."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear the data cache before each test
        MedicalDevice._DATA_CACHE = {}

        # Create a mock class factory util
        self.mock_class_factory_util = MagicMock()

        # Create a test instance
        self.device = MedicalDevice(
            class_factory_util=self.mock_class_factory_util, locale="en_US", dataset="test_dataset"
        )

    def test_initialization(self):
        """Test initialization of MedicalDevice."""
        self.assertEqual(self.device._locale, "en_US")
        self.assertEqual(self.device._dataset, "test_dataset")
        self.assertEqual(self.device._country_code, "US")
        self.assertEqual(self.device._class_factory_util, self.mock_class_factory_util)
        self.assertIsInstance(self.device._property_cache, dict)

    def test_determine_country_code_from_dataset(self):
        """Test determining country code from dataset."""
        # Test with dataset containing country code
        device = MedicalDevice(dataset="medical_devices_UK", locale="en")
        self.assertEqual(device._country_code, "UK")

        # Test with dataset not containing country code
        device = MedicalDevice(dataset="medical_devices", locale="en_US")
        self.assertEqual(device._country_code, "US")

    def test_determine_country_code_from_locale(self):
        """Test determining country code from locale."""
        # Test with locale containing country code
        device = MedicalDevice(dataset=None, locale="en_CA")
        self.assertEqual(device._country_code, "CA")

        # Test with locale not containing country code
        device = MedicalDevice(dataset=None, locale="en")
        self.assertEqual(device._country_code, "US")  # Default

    @patch("pathlib.Path.exists")
    @patch("datamimic_ce.domains.healthcare.models.medical_device.MedicalDevice._load_simple_csv")
    def test_load_data(self, mock_load_csv, mock_exists):
        """Test loading data from CSV files."""
        # Setup mocks
        mock_exists.return_value = True
        mock_load_csv.return_value = ["Test1", "Test2", "Test3"]

        # Call the method
        MedicalDevice._load_data("FR")

        # Verify the data cache was populated
        self.assertIn("device_types", MedicalDevice._DATA_CACHE)
        self.assertIn("manufacturers", MedicalDevice._DATA_CACHE)
        self.assertIn("locations", MedicalDevice._DATA_CACHE)
        self.assertIn("statuses", MedicalDevice._DATA_CACHE)

        # Verify the mock was called with the correct paths
        self.assertEqual(mock_load_csv.call_count, 4)

    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data="header\nvalue1\nvalue2\n")
    @patch("pathlib.Path.exists")
    def test_load_simple_csv(self, mock_exists, mock_open):
        """Test loading data from a simple CSV file."""
        # Setup mocks
        mock_exists.return_value = True

        # Call the method
        result = MedicalDevice._load_simple_csv(MagicMock())

        # Verify the result
        self.assertEqual(result, ["value1", "value2"])

        # Test with header that should be skipped
        mock_open.return_value.readlines.return_value = ["name\n", "value1\n", "value2\n"]
        result = MedicalDevice._load_simple_csv(MagicMock())
        self.assertEqual(result, ["value1", "value2"])

    def test_device_id(self):
        """Test generating a device ID."""
        device_id = self.device.device_id

        # Verify format: DEV-XXXXXXXX (where X is a digit)
        self.assertTrue(re.match(r"DEV-\d{8}$", device_id))

        # Verify caching works
        self.assertEqual(device_id, self.device.device_id)

    def test_device_type(self):
        """Test generating a device type."""
        # Setup test data
        MedicalDevice._DATA_CACHE["device_types"] = ["Type1", "Type2", "Type3"]

        # Get the device type
        device_type = self.device.device_type

        # Verify it's one of the expected values
        self.assertIn(device_type, MedicalDevice._DATA_CACHE["device_types"])

        # Verify caching works
        self.assertEqual(device_type, self.device.device_type)

    def test_manufacturer(self):
        """Test generating a manufacturer."""
        # Setup test data
        MedicalDevice._DATA_CACHE["manufacturers"] = ["Mfg1", "Mfg2", "Mfg3"]

        # Get the manufacturer
        manufacturer = self.device.manufacturer

        # Verify it's one of the expected values
        self.assertIn(manufacturer, MedicalDevice._DATA_CACHE["manufacturers"])

        # Verify caching works
        self.assertEqual(manufacturer, self.device.manufacturer)

    def test_model_number(self):
        """Test generating a model number."""
        model_number = self.device.model_number

        # Verify format: XX#### (where X is uppercase letter, # is digit)
        self.assertTrue(re.match(r"[A-Z]{2}\d{4}$", model_number))

        # Verify caching works
        self.assertEqual(model_number, self.device.model_number)

    def test_serial_number(self):
        """Test generating a serial number."""
        serial_number = self.device.serial_number

        # Verify format: MFG-YYYY-XXXXXXXX
        self.assertTrue(re.match(r"MFG-\d{4}-[A-Z0-9]{8}$", serial_number))

        # Verify year is reasonable
        year = int(serial_number.split("-")[1])
        current_year = datetime.datetime.now().year
        self.assertTrue(2010 <= year <= current_year)

        # Verify caching works
        self.assertEqual(serial_number, self.device.serial_number)

    def test_manufacture_date(self):
        """Test generating a manufacture date."""
        manufacture_date = self.device.manufacture_date

        # Verify format: YYYY-MM-DD
        self.assertTrue(re.match(r"\d{4}-\d{2}-\d{2}$", manufacture_date))

        # Verify date is in the past
        date = datetime.datetime.strptime(manufacture_date, "%Y-%m-%d")
        self.assertTrue(date < datetime.datetime.now())

        # Verify caching works
        self.assertEqual(manufacture_date, self.device.manufacture_date)

    def test_expiration_date(self):
        """Test generating an expiration date."""
        expiration_date = self.device.expiration_date

        # Verify format: YYYY-MM-DD
        self.assertTrue(re.match(r"\d{4}-\d{2}-\d{2}$", expiration_date))

        # Verify date is in the future
        date = datetime.datetime.strptime(expiration_date, "%Y-%m-%d")
        self.assertTrue(date > datetime.datetime.now())

        # Verify caching works
        self.assertEqual(expiration_date, self.device.expiration_date)

    def test_maintenance_dates(self):
        """Test generating maintenance dates."""
        last_maintenance = self.device.last_maintenance_date
        next_maintenance = self.device.next_maintenance_date

        # Verify format: YYYY-MM-DD
        self.assertTrue(re.match(r"\d{4}-\d{2}-\d{2}$", last_maintenance))
        self.assertTrue(re.match(r"\d{4}-\d{2}-\d{2}$", next_maintenance))

        # Verify last_maintenance is in the past
        last_date = datetime.datetime.strptime(last_maintenance, "%Y-%m-%d")
        self.assertTrue(last_date < datetime.datetime.now())

        # Verify next_maintenance is in the future
        next_date = datetime.datetime.strptime(next_maintenance, "%Y-%m-%d")
        self.assertTrue(next_date > datetime.datetime.now())

        # Verify caching works
        self.assertEqual(last_maintenance, self.device.last_maintenance_date)
        self.assertEqual(next_maintenance, self.device.next_maintenance_date)

    def test_status(self):
        """Test generating a status."""
        # Setup test data
        MedicalDevice._DATA_CACHE["statuses"] = ["Status1", "Status2", "Status3"]

        # Get the status
        status = self.device.status

        # Verify it's one of the expected values
        self.assertIn(status, MedicalDevice._DATA_CACHE["statuses"])

        # Verify caching works
        self.assertEqual(status, self.device.status)

    def test_location(self):
        """Test generating a location."""
        # Setup test data
        MedicalDevice._DATA_CACHE["locations"] = ["Location1", "Location2", "Location3"]

        # Get the location
        location = self.device.location

        # Verify it's one of the expected values
        self.assertIn(location, MedicalDevice._DATA_CACHE["locations"])

        # Verify caching works
        self.assertEqual(location, self.device.location)

    def test_assigned_to(self):
        """Test generating an assigned person."""
        # Setup mock for Person
        mock_person = MagicMock()
        mock_person.first_name = "John"
        mock_person.last_name = "Doe"
        self.mock_class_factory_util.create_instance.return_value = mock_person

        # Get the assigned person
        assigned_to = self.device.assigned_to

        # Verify it's the expected value
        self.assertEqual(assigned_to, "John Doe")

        # Verify caching works
        self.assertEqual(assigned_to, self.device.assigned_to)

        # Test without class_factory_util
        device = MedicalDevice(class_factory_util=None)
        self.assertEqual(device.assigned_to, "Unassigned")

    def test_specifications(self):
        """Test generating specifications."""
        # Get the specifications
        specs = self.device.specifications

        # Verify it's a dictionary with expected common keys
        self.assertIsInstance(specs, dict)
        self.assertIn("power_supply", specs)
        self.assertIn("weight_kg", specs)
        self.assertIn("dimensions_cm", specs)

        # Verify caching works
        self.assertEqual(specs, self.device.specifications)

    def test_usage_logs(self):
        """Test generating usage logs."""
        # Get the usage logs
        logs = self.device.usage_logs

        # Verify it's a list of dictionaries with expected keys
        self.assertIsInstance(logs, list)
        if logs:  # There might be no logs in rare cases
            log = logs[0]
            self.assertIsInstance(log, dict)
            self.assertIn("date", log)
            self.assertIn("user", log)
            self.assertIn("duration_minutes", log)
            self.assertIn("purpose", log)
            self.assertIn("notes", log)

        # Verify caching works
        self.assertEqual(logs, self.device.usage_logs)

    def test_maintenance_history(self):
        """Test generating maintenance history."""
        # Get the maintenance history
        history = self.device.maintenance_history

        # Verify it's a list of dictionaries with expected keys
        self.assertIsInstance(history, list)
        if history:  # There might be no history in rare cases
            record = history[0]
            self.assertIsInstance(record, dict)
            self.assertIn("date", record)
            self.assertIn("technician", record)
            self.assertIn("type", record)
            self.assertIn("parts_replaced", record)
            self.assertIn("cost", record)
            self.assertIn("duration_hours", record)
            self.assertIn("result", record)
            self.assertIn("notes", record)

        # Verify caching works
        self.assertEqual(history, self.device.maintenance_history)

    def test_reset(self):
        """Test resetting cached properties."""
        # Access some properties to cache them
        device_id = self.device.device_id
        device_type = self.device.device_type

        # Reset the cache
        self.device.reset()

        # Verify the cache is empty
        self.assertEqual(self.device._property_cache, {})

        # Verify new values are generated
        self.assertNotEqual(device_id, self.device.device_id)
        self.assertNotEqual(device_type, self.device.device_type)

    def test_to_dict(self):
        """Test converting to dictionary."""
        # Get the dictionary representation
        device_dict = self.device.to_dict()

        # Verify it contains all expected keys
        expected_keys = [
            "device_id",
            "device_type",
            "manufacturer",
            "model_number",
            "serial_number",
            "manufacture_date",
            "expiration_date",
            "last_maintenance_date",
            "next_maintenance_date",
            "status",
            "location",
            "assigned_to",
            "specifications",
            "usage_logs",
            "maintenance_history",
        ]
        for key in expected_keys:
            self.assertIn(key, device_dict)

    def test_generate_batch(self):
        """Test generating a batch of devices."""
        # Generate a batch
        batch = self.device.generate_batch(count=5)

        # Verify it's a list of dictionaries of the correct length
        self.assertIsInstance(batch, list)
        self.assertEqual(len(batch), 5)
        self.assertIsInstance(batch[0], dict)

        # Verify each device has a unique ID
        device_ids = [device["device_id"] for device in batch]
        self.assertEqual(len(device_ids), len(set(device_ids)))


if __name__ == "__main__":
    unittest.main()
