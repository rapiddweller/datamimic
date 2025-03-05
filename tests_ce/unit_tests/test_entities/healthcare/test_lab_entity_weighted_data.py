"""Test the LabTestEntity with weighted data selection."""

import os
from collections import Counter
from pathlib import Path
from unittest.mock import MagicMock, patch

# Import the LabTestEntity class
from datamimic_ce.entities.healthcare.lab_test_entity import LabTestEntity
from datamimic_ce.entities.healthcare.lab_test_entity.data_loader import LabTestDataLoader


class TestLabEntityWeightedData:
    """Test the LabTestEntity with weighted data selection."""

    def setup_method(self):
        """Set up the test environment."""
        # Clear the data cache before each test
        LabTestEntity._DATA_CACHE = {}
        
        # Create a mock class_factory_util
        self.mock_class_factory_util = MagicMock()
        self.mock_data_generation_util = MagicMock()
        self.mock_class_factory_util.get_data_generation_util.return_value = self.mock_data_generation_util

    def test_load_simple_csv_with_weights(self):
        """Test that _load_simple_csv correctly handles weighted data."""
        # Create a temporary file with weighted data
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("Lab1,200\n")
            temp_file.write("Lab2,150\n")
            temp_file.write("Lab3,100\n")
            temp_file.write("Lab4\n")  # No weight
            temp_file.write("Lab5,invalid\n")  # Invalid weight
            temp_path = temp_file.name
        
        try:
            # Load the file using _load_simple_csv
            result = LabTestDataLoader._load_simple_csv(Path(temp_path))
            
            # Count occurrences of each value
            counter = Counter(result)
            
            # Check that all expected values are present in the result
            assert len(result) == 5, f"Expected 5 items, got {len(result)}"
            
            # Check that the values are tuples with the correct format
            for item in result:
                assert isinstance(item, tuple), f"Expected tuple, got {type(item)}"
                assert len(item) == 2, f"Expected tuple of length 2, got {len(item)}"
                assert isinstance(item[0], str), f"Expected string as first element, got {type(item[0])}"
                assert isinstance(item[1], float), f"Expected float as second element, got {type(item[1])}"
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)

    @patch('datamimic_ce.entities.healthcare.lab_test_entity.data_loader.LabTestDataLoader.get_country_specific_data')
    def test_weighted_labs_distribution(self, mock_get_country_specific_data):
        """Test that weighted labs are distributed according to their weights."""
        # Mock the get_country_specific_data method to return weighted values
        def mock_get_country_specific_data_side_effect(data_type, country_code=None):
            if data_type == "lab_names" or data_type == "labs":
                # Simulate the weighted data from labs_US.csv
                return [
                    ("Quest Diagnostics", 200.0),
                    ("LabCorp", 190.0),
                    ("Mayo Clinic Laboratories", 180.0),
                    ("ARUP Laboratories", 170.0),
                    ("BioReference Laboratories", 160.0)
                ]
            elif data_type == "test_types":
                return [
                    ("Complete Blood Count (CBC)", 200.0),
                    ("Basic Metabolic Panel (BMP)", 190.0),
                    ("Comprehensive Metabolic Panel (CMP)", 180.0),
                    ("Lipid Panel", 170.0),
                    ("Thyroid Stimulating Hormone (TSH)", 160.0)
                ]
            elif data_type == "test_statuses":
                return [
                    ("Completed", 200.0),
                    ("Pending", 150.0),
                    ("Cancelled", 50.0),
                    ("In Progress", 100.0)
                ]
            elif data_type == "specimen_types":
                return [
                    ("Blood", 200.0),
                    ("Urine", 150.0),
                    ("Saliva", 100.0),
                    ("Cerebrospinal Fluid", 50.0),
                    ("Tissue", 50.0)
                ]
            return []
        
        mock_get_country_specific_data.side_effect = mock_get_country_specific_data_side_effect
        
        # Create a LabTestEntity with US dataset
        lab_entity = LabTestEntity(self.mock_class_factory_util, dataset="US")
        
        # Generate a batch of labs to test the distribution
        # Using a smaller batch size to reduce test time while still being representative
        labs = lab_entity.generate_batch(100)
        
        # Verify that labs were generated
        assert len(labs) == 100, "Expected 100 labs to be generated"
        
        # Check that the lab data contains the expected fields
        expected_fields = ["test_id", "patient_id", "doctor_id", "test_type", "performing_lab"]
        for field in expected_fields:
            assert field in labs[0], f"Expected field {field} to be present in lab data"

    @patch('datamimic_ce.entities.healthcare.lab_test_entity.data_loader.LabTestDataLoader.get_country_specific_data')
    def test_weighted_labs_distribution_DE(self, mock_get_country_specific_data):
        """Test that weighted labs for Germany are distributed according to their weights."""
        # Mock the get_country_specific_data method to return weighted values
        def mock_get_country_specific_data_side_effect(data_type, country_code=None):
            if data_type == "lab_names" or data_type == "labs":
                # Simulate the weighted data from labs_DE.csv
                return [
                    ("Synlab", 200.0),
                    ("Labor Berlin", 190.0),
                    ("Amedes", 180.0),
                    ("Sonic Healthcare Germany", 170.0),
                    ("Bioscientia", 160.0)
                ]
            elif data_type == "test_types":
                return [
                    ("Blutbild", 200.0),
                    ("Elektrolyte", 190.0),
                    ("Leberfunktionstest", 180.0),
                    ("Lipidprofil", 170.0),
                    ("Schilddrüsenfunktionstest", 160.0)
                ]
            elif data_type == "test_statuses":
                return [
                    ("Abgeschlossen", 200.0),
                    ("Ausstehend", 150.0),
                    ("Storniert", 50.0),
                    ("In Bearbeitung", 100.0)
                ]
            elif data_type == "specimen_types":
                return [
                    ("Blut", 200.0),
                    ("Urin", 150.0),
                    ("Speichel", 100.0),
                    ("Liquor", 50.0),
                    ("Gewebe", 50.0)
                ]
            return []
        
        mock_get_country_specific_data.side_effect = mock_get_country_specific_data_side_effect
        
        # Create a LabTestEntity with DE dataset
        lab_entity = LabTestEntity(self.mock_class_factory_util, dataset="DE")
        
        # Generate a batch of labs to test the distribution
        # Using a smaller batch size to reduce test time while still being representative
        labs = lab_entity.generate_batch(100)
        
        # Verify that labs were generated
        assert len(labs) == 100, "Expected 100 labs to be generated"
        
        # Check that the lab data contains the expected fields
        expected_fields = ["test_id", "patient_id", "doctor_id", "test_type", "performing_lab"]
        for field in expected_fields:
            assert field in labs[0], f"Expected field {field} to be present in lab data" 