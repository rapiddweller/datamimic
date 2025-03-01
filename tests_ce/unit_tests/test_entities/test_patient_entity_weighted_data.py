"""Test the PatientEntity with weighted data selection."""

import os
import tempfile
from collections import Counter
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock

# Import the PatientEntity class from the healthcare module directly
from datamimic_ce.entities.healthcare.patient_entity import PatientEntity


class TestPatientEntityWeightedData(TestCase):
    """Test the PatientEntity with weighted data selection."""

    def setUp(self):
        """Set up the test environment."""
        # Clear the data cache before each test
        PatientEntity._DATA_CACHE = {}
        
        # Create a mock class_factory_util
        self.mock_class_factory_util = MagicMock()
        self.mock_data_generation_util = MagicMock()
        self.mock_class_factory_util.get_data_generation_util.return_value = self.mock_data_generation_util

    def test_load_simple_csv_with_weights(self):
        """Test that _load_simple_csv correctly handles weighted data."""
        # Create a temporary file with weighted data
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("Male, 100\n")
            temp_file.write("Female, 100\n")
            temp_file.write("Other, 10\n")
            temp_file.write("Unknown, 5\n")
            temp_file.write("NoWeight\n")  # No weight
            temp_file.write("InvalidWeight, invalid\n")  # Invalid weight
            temp_path = temp_file.name
        
        try:
            # Load the file using _load_simple_csv
            result = PatientEntity._load_simple_csv(Path(temp_path))
            
            # Count occurrences of each value
            counter = Counter(result)
            
            # Check that values with weights appear the correct number of times
            assert counter["Male"] == 100
            assert counter["Female"] == 100
            assert counter["Other"] == 10
            assert counter["Unknown"] == 5
            
            # Check that values without weights appear once
            assert counter["NoWeight"] == 1
            
            # Check that values with invalid weights are treated as single values
            assert counter["InvalidWeight, invalid"] == 1
            
            # Check total number of items
            assert len(result) == 100 + 100 + 10 + 5 + 1 + 1
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)

    def test_load_csv_with_header(self):
        """Test that _load_csv_with_header correctly loads CSV data with headers."""
        # Create a temporary file with CSV data
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            # Write header
            temp_file.write("condition,status,weight\n")
            # Write data
            temp_file.write("Hypertension,Chronic,100\n")
            temp_file.write("Diabetes Type 2,Chronic,80\n")
            temp_file.write("Asthma,Chronic,50\n")
            temp_file.write("Arthritis,Chronic,40\n")
            temp_file.write("Coronary Artery Disease,Chronic,30\n")
            temp_file.write("Common Cold,Acute,\n")
            temp_path = temp_file.name
        
        try:
            # Load the file using _load_csv_with_header
            result = PatientEntity._load_csv_with_header(Path(temp_path))
            
            # Check that we have the expected number of items
            assert len(result) == 6
            
            # Check that each item has the correct structure
            for item in result:
                assert "condition" in item
                assert "status" in item
                assert "weight" in item
                
                # Check specific values
                if item["condition"] == "Hypertension":
                    assert item["status"] == "Chronic"
                    assert item["weight"] == "100"
                elif item["condition"] == "Common Cold":
                    assert item["status"] == "Acute"
                    assert item["weight"] == ""
        finally:
            # Clean up the temporary file
            os.unlink(temp_path) 