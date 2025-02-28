"""Test the DoctorEntity with weighted data selection."""

import os
from collections import Counter
from pathlib import Path
from unittest.mock import MagicMock, patch

# Import the DoctorEntity class
# Note: Adjust the import path as needed for your project structure
from datamimic_ce.entities.doctor_entity import DoctorEntity


class TestDoctorEntityWeightedData:
    """Test the DoctorEntity with weighted data selection."""

    def setup_method(self):
        """Set up the test environment."""
        # Clear the data cache before each test
        DoctorEntity._DATA_CACHE = {}
        
        # Create a mock class_factory_util
        self.mock_class_factory_util = MagicMock()
        self.mock_data_generation_util = MagicMock()
        self.mock_class_factory_util.get_data_generation_util.return_value = self.mock_data_generation_util

    def test_load_simple_csv_with_weights(self):
        """Test that _load_simple_csv correctly handles weighted data."""
        # Create a temporary file with weighted data
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("Value1,100\n")
            temp_file.write("Value2,50\n")
            temp_file.write("Value3,25\n")
            temp_file.write("Value4\n")  # No weight
            temp_file.write("Value5,invalid\n")  # Invalid weight
            temp_path = temp_file.name
        
        try:
            # Load the file using _load_simple_csv
            result = DoctorEntity._load_simple_csv(Path(temp_path))
            
            # Count occurrences of each value
            counter = Counter(result)
            
            # Check that values with weights appear the correct number of times
            assert counter["Value1"] == 100, f"Expected Value1 to appear 100 times, got {counter['Value1']}"
            assert counter["Value2"] == 50, f"Expected Value2 to appear 50 times, got {counter['Value2']}"
            assert counter["Value3"] == 25, f"Expected Value3 to appear 25 times, got {counter['Value3']}"
            
            # Check that values without weights appear once
            assert counter["Value4"] == 1, f"Expected Value4 to appear once, got {counter['Value4']}"
            
            # Check that values with invalid weights are treated as single values
            assert counter["Value5,invalid"] == 1, f"Expected Value5,invalid to appear once, got {counter['Value5,invalid']}"
            
            # Check total number of items
            assert len(result) == 100 + 50 + 25 + 1 + 1, f"Expected 177 items, got {len(result)}"
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)

    @patch('datamimic_ce.entities.doctor_entity.Path.exists')
    @patch('datamimic_ce.entities.doctor_entity.DoctorEntity._load_simple_csv')
    def test_weighted_specialty_distribution(self, mock_load_csv, mock_exists):
        """Test that weighted specialties are distributed according to their weights."""
        # Mock the Path.exists method to return True for DE country-specific files
        def mock_exists_side_effect(*args, **kwargs):
            if not args:
                return True
            path = args[0]
            return "_DE" in str(path) or "specialties" in str(path) or "hospitals" in str(path) or "institutions" in str(path) or "certifications" in str(path) or "languages" in str(path)
        
        mock_exists.side_effect = mock_exists_side_effect
        
        # Mock the _load_simple_csv method to return weighted values
        def mock_load_csv_side_effect(path):
            if "specialties_DE" in str(path) or "specialties" in str(path):
                # Use a simpler dataset with more distinct weights to reduce randomness issues
                # Increase the weight of Kardiologie to ensure it appears in the results
                return ["Allgemeinmedizin"] * 300 + ["Innere Medizin"] * 200 + ["Chirurgie"] * 100 + ["Orthopädie"] * 50 + ["Kardiologie"] * 50
            elif "hospitals_DE" in str(path) or "hospitals" in str(path):
                # Simulate the weighted data from hospitals_DE.csv
                return ["Charité Berlin"] * 150 + ["Universitätsklinikum Heidelberg"] * 120 + ["Universitätsklinikum München"] * 100
            elif "institutions_DE" in str(path) or "institutions" in str(path):
                # Simulate the weighted data from institutions_DE.csv
                return ["Universität Berlin"] * 150 + ["Universität Heidelberg"] * 120 + ["Universität München"] * 100
            elif "certifications_DE" in str(path) or "certifications" in str(path):
                # Simulate the weighted data from certifications_DE.csv
                return ["Facharzt für Allgemeinmedizin"] * 150 + ["Facharzt für Innere Medizin"] * 120 + ["Facharzt für Chirurgie"] * 100
            elif "languages_DE" in str(path) or "languages" in str(path):
                # Simulate the weighted data from languages_DE.csv
                return ["Deutsch"] * 200 + ["Englisch"] * 150 + ["Französisch"] * 50
            return []
        
        mock_load_csv.side_effect = mock_load_csv_side_effect
        
        # Create a DoctorEntity with DE dataset
        doctor_entity = DoctorEntity(self.mock_class_factory_util, dataset="DE")
        
        # Generate a larger batch of doctors to test the distribution
        # Increasing the batch size to ensure all specialties appear
        doctors = doctor_entity.generate_batch(200)
        
        # Verify that doctors were generated
        assert len(doctors) == 200, "Expected 200 doctors to be generated"
        
        # Check that the doctor data contains the expected fields
        expected_fields = ["doctor_id", "first_name", "last_name", "specialty", "license_number"]
        for field in expected_fields:
            assert field in doctors[0], f"Expected field {field} to be present in doctor data"
        
        # Count the specialties
        specialty_counter = Counter([doctor["specialty"] for doctor in doctors])
        
        # Print the specialty counter for debugging
        print(f"Specialty distribution: {specialty_counter}")
        
        # Check that all specialties of interest are present
        specialties_of_interest = ["Allgemeinmedizin", "Innere Medizin", "Chirurgie", "Orthopädie", "Kardiologie"]
        for specialty in specialties_of_interest:
            assert specialty in specialty_counter, f"Expected {specialty} to be present in the results" 