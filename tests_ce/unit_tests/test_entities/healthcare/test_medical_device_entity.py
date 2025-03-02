# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import unittest
from pathlib import Path

from datamimic_ce.entities.healthcare.medical_device_entity import MedicalDeviceEntity
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestMedicalDeviceEntity(unittest.TestCase):
    """Test cases for the MedicalDeviceEntity class."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()
        self.device_entity = MedicalDeviceEntity(self.class_factory_util)

    def test_init(self):
        """Test initialization of MedicalDeviceEntity."""
        self.assertEqual(self.device_entity._country_code, "US")
        self.assertIsNone(self.device_entity._dataset)

    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        device_entity = MedicalDeviceEntity(
            self.class_factory_util,
            locale="de",
            dataset="test_dataset"
        )
        self.assertEqual(device_entity._country_code, "DE")
        self.assertEqual(device_entity._dataset, "test_dataset")

    def test_device_id_generation(self):
        """Test device_id generation."""
        device_id = self.device_entity.device_id
        self.assertIsInstance(device_id, str)
        self.assertTrue(len(device_id) > 0)
        # Check if it follows the expected format (e.g., "DEV-12345678")
        self.assertRegex(device_id, r"DEV-\d+")

    def test_device_type_generation(self):
        """Test device_type generation."""
        device_type = self.device_entity.device_type
        self.assertIsInstance(device_type, str)
        self.assertTrue(len(device_type) > 0)
        
        # Check if the device types CSV file exists and contains the device type
        device_types = []
        data_dir = Path(__file__).parent.parent.parent.parent.parent / "datamimic_ce" / "entities" / "data" / "medical"
        
        # Try different files in order of preference
        device_type_files = [
            data_dir / f"device_types_{self.device_entity._country_code}.csv",
            data_dir / "device_types_US.csv",
            data_dir / "device_types.csv"
        ]
        
        for file_path in device_type_files:
            if file_path.exists():
                try:
                    with open(file_path, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if "," in line:
                                parts = line.split(",", 1)
                                if parts[0].strip():
                                    device_types.append(parts[0].strip())
                            elif line:
                                device_types.append(line)
                except Exception:
                    pass
                break
        
        # If we found device types in the CSV file, check that the generated device type is among them
        if device_types:
            self.assertIn(device_type, device_types)

    def test_manufacturer_generation(self):
        """Test manufacturer generation."""
        manufacturer = self.device_entity.manufacturer
        self.assertIsInstance(manufacturer, str)
        self.assertTrue(len(manufacturer) > 0)

    def test_model_number_generation(self):
        """Test model_number generation."""
        model_number = self.device_entity.model_number
        self.assertIsInstance(model_number, str)
        self.assertTrue(len(model_number) > 0)
        # Check if it follows the expected format (e.g., "XYZ-12345")
        self.assertRegex(model_number, r"[A-Z]+-\d+[A-Z]*")

    def test_serial_number_generation(self):
        """Test serial_number generation."""
        serial_number = self.device_entity.serial_number
        self.assertIsInstance(serial_number, str)
        self.assertTrue(len(serial_number) > 0)
        # Check if it follows the expected format (e.g., "ABC230000000")
        self.assertRegex(serial_number, r"[A-Z]{3}\d{8}")

    def test_manufacture_date_generation(self):
        """Test manufacture_date generation."""
        manufacture_date = self.device_entity.manufacture_date
        self.assertIsInstance(manufacture_date, str)
        # Check if it's a valid date in ISO format (YYYY-MM-DD)
        self.assertRegex(manufacture_date, r"\d{4}-\d{2}-\d{2}")

    def test_expiration_date_generation(self):
        """Test expiration_date generation."""
        expiration_date = self.device_entity.expiration_date
        self.assertIsInstance(expiration_date, str)
        # Check if it's a valid date in ISO format (YYYY-MM-DD)
        self.assertRegex(expiration_date, r"\d{4}-\d{2}-\d{2}")
        
        # Expiration date should be after manufacture date
        manufacture_date = self.device_entity.manufacture_date
        self.assertGreater(expiration_date, manufacture_date)

    def test_last_maintenance_date_generation(self):
        """Test last_maintenance_date generation."""
        last_maintenance_date = self.device_entity.last_maintenance_date
        self.assertIsInstance(last_maintenance_date, str)
        # Check if it's a valid date in ISO format (YYYY-MM-DD)
        self.assertRegex(last_maintenance_date, r"\d{4}-\d{2}-\d{2}")
        
        # Last maintenance date should be after or equal to manufacture date
        manufacture_date = self.device_entity.manufacture_date
        self.assertGreaterEqual(last_maintenance_date, manufacture_date)

    def test_next_maintenance_date_generation(self):
        """Test next_maintenance_date generation."""
        next_maintenance_date = self.device_entity.next_maintenance_date
        self.assertIsInstance(next_maintenance_date, str)
        # Check if it's a valid date in ISO format (YYYY-MM-DD)
        self.assertRegex(next_maintenance_date, r"\d{4}-\d{2}-\d{2}")
        
        # Next maintenance date should be after last maintenance date
        last_maintenance_date = self.device_entity.last_maintenance_date
        self.assertGreater(next_maintenance_date, last_maintenance_date)

    def test_status_generation(self):
        """Test status generation."""
        status = self.device_entity.status
        self.assertIsInstance(status, str)
        self.assertTrue(len(status) > 0)

    def test_location_generation(self):
        """Test location generation."""
        location = self.device_entity.location
        self.assertIsInstance(location, str)
        self.assertTrue(len(location) > 0)

    def test_assigned_to_generation(self):
        """Test assigned_to generation."""
        assigned_to = self.device_entity.assigned_to
        self.assertIsInstance(assigned_to, str)
        # assigned_to can be empty if device is not assigned

    def test_specifications_generation(self):
        """Test specifications generation."""
        specifications = self.device_entity.specifications
        self.assertIsInstance(specifications, dict)
        # Check for common specification keys
        self.assertIn("dimensions", specifications)
        self.assertIn("weight", specifications)
        self.assertIn("power_supply", specifications)
        self.assertIn("voltage", specifications)
        self.assertIn("certification", specifications)

    def test_usage_logs_generation(self):
        """Test usage_logs generation."""
        usage_logs = self.device_entity.usage_logs
        self.assertIsInstance(usage_logs, list)
        # If there are usage logs, check their structure
        if usage_logs:
            log = usage_logs[0]
            self.assertIsInstance(log, dict)
            self.assertIn("date", log)
            self.assertIn("user", log)
            self.assertIn("action", log)
            self.assertIn("details", log)
            
            # Check date format
            self.assertRegex(log["date"], r"\d{4}-\d{2}-\d{2}")

    def test_maintenance_history_generation(self):
        """Test maintenance_history generation."""
        maintenance_history = self.device_entity.maintenance_history
        self.assertIsInstance(maintenance_history, list)
        # If there are maintenance records, check their structure
        if maintenance_history:
            record = maintenance_history[0]
            self.assertIsInstance(record, dict)
            self.assertIn("date", record)
            self.assertIn("technician", record)
            self.assertIn("actions", record)
            self.assertIn("notes", record)
            
            # Check date format
            self.assertRegex(record["date"], r"\d{4}-\d{2}-\d{2}")
            
            # Check actions is a list of strings
            self.assertIsInstance(record["actions"], list)
            if record["actions"]:
                self.assertIsInstance(record["actions"][0], str)

    def test_to_dict(self):
        """Test to_dict method."""
        device_dict = self.device_entity.to_dict()
        self.assertIsInstance(device_dict, dict)
        self.assertIn("device_id", device_dict)
        self.assertIn("device_type", device_dict)
        self.assertIn("manufacturer", device_dict)
        self.assertIn("model_number", device_dict)
        self.assertIn("serial_number", device_dict)
        self.assertIn("manufacture_date", device_dict)
        self.assertIn("expiration_date", device_dict)
        self.assertIn("last_maintenance_date", device_dict)
        self.assertIn("next_maintenance_date", device_dict)
        self.assertIn("status", device_dict)
        self.assertIn("location", device_dict)
        self.assertIn("assigned_to", device_dict)
        self.assertIn("specifications", device_dict)
        self.assertIn("usage_logs", device_dict)
        self.assertIn("maintenance_history", device_dict)

    def test_generate_batch(self):
        """Test generate_batch method."""
        batch_size = 5
        batch = self.device_entity.generate_batch(batch_size)
        self.assertIsInstance(batch, list)
        self.assertEqual(len(batch), batch_size)
        for item in batch:
            self.assertIsInstance(item, dict)
            self.assertIn("device_id", item)
            self.assertIn("device_type", item)
            self.assertIn("manufacturer", item)
            self.assertIn("model_number", item)
            self.assertIn("serial_number", item)
            self.assertIn("manufacture_date", item)
            self.assertIn("expiration_date", item)
            self.assertIn("last_maintenance_date", item)
            self.assertIn("next_maintenance_date", item)
            self.assertIn("status", item)
            self.assertIn("location", item)
            self.assertIn("assigned_to", item)
            self.assertIn("specifications", item)
            self.assertIn("usage_logs", item)
            self.assertIn("maintenance_history", item)

    def test_reset(self):
        """Test reset method."""
        # Get initial values
        initial_device_id = self.device_entity.device_id
        initial_device_type = self.device_entity.device_type
        
        # Reset the entity
        self.device_entity.reset()
        
        # Get new values
        new_device_id = self.device_entity.device_id
        new_device_type = self.device_entity.device_type
        
        # Values should be different after reset
        self.assertNotEqual(initial_device_id, new_device_id)
        # Device type might be the same after reset due to random choice from a small set
        # so we don't assert inequality for it

    def test_determine_country_code(self):
        """Test the _determine_country_code method."""
        # Test with dataset provided
        self.assertEqual(self.device_entity._determine_country_code("DE", "en"), "DE")
        
        # Test with locale in format 'en_US'
        self.assertEqual(self.device_entity._determine_country_code(None, "en_US"), "US")
        
        # Test with locale in format 'de-DE'
        self.assertEqual(self.device_entity._determine_country_code(None, "de-DE"), "DE")
        
        # Test with 2-letter locale
        self.assertEqual(self.device_entity._determine_country_code(None, "de"), "DE")
        
        # Test with language code that maps to a country
        self.assertEqual(self.device_entity._determine_country_code(None, "fr"), "FR")
        
        # Test with unrecognized locale, should default to US
        self.assertEqual(self.device_entity._determine_country_code(None, "xx"), "US")


if __name__ == "__main__":
    unittest.main() 