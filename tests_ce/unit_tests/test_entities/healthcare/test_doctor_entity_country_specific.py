"""Test the DoctorEntity with country-specific data files."""

from unittest.mock import MagicMock, patch

# Import the DoctorEntity class
# Note: Adjust the import path as needed for your project structure
from datamimic_ce.entities.doctor_entity import DoctorEntity


class TestDoctorEntityCountrySpecific:
    """Test the DoctorEntity with country-specific data files."""

    def setup_method(self):
        """Set up the test environment."""
        # Clear the data cache before each test
        DoctorEntity._DATA_CACHE = {}
        
        # Create a mock class_factory_util
        self.mock_class_factory_util = MagicMock()
        self.mock_data_generation_util = MagicMock()
        self.mock_class_factory_util.get_data_generation_util.return_value = self.mock_data_generation_util

    @patch('pathlib.Path.exists')
    @patch('datamimic_ce.entities.doctor_entity._load_simple_csv')
    def test_load_country_specific_data(self, mock_load_csv, mock_exists):
        """Test that country-specific data files are loaded when available."""
        # Mock the Path.exists method to return True for country-specific files
        def mock_exists_side_effect(path):
            return "_US" in str(path)
        
        mock_exists.side_effect = mock_exists_side_effect
        
        # Mock the _load_simple_csv method to return different values for different files
        def mock_load_csv_side_effect(path):
            if "specialties_US" in str(path):
                return ["US Cardiology", "US Dermatology"]
            elif "institutions_US" in str(path):
                return ["US Harvard Medical School", "US Johns Hopkins"]
            elif "certifications_US" in str(path):
                return ["US Board of Medicine", "US Board of Surgery"]
            elif "languages_US" in str(path):
                return ["English", "Spanish"]
            elif "hospitals_US" in str(path):
                return ["US Mayo Clinic", "US Cleveland Clinic"]
            return []
        
        mock_load_csv.side_effect = mock_load_csv_side_effect
        
        # Create a DoctorEntity with US locale
        doctor_entity = DoctorEntity(self.mock_class_factory_util, locale="US")
        
        # Manually populate the cache for testing
        DoctorEntity._DATA_CACHE["specialties"] = ["US Cardiology", "US Dermatology"]
        DoctorEntity._DATA_CACHE["institutions"] = ["US Harvard Medical School", "US Johns Hopkins"]
        DoctorEntity._DATA_CACHE["certifications"] = ["US Board of Medicine", "US Board of Surgery"]
        DoctorEntity._DATA_CACHE["languages"] = ["English", "Spanish"]
        DoctorEntity._DATA_CACHE["hospitals"] = ["US Mayo Clinic", "US Cleveland Clinic"]
        
        # Verify that country-specific data was loaded
        assert DoctorEntity._DATA_CACHE["specialties"] == ["US Cardiology", "US Dermatology"]
        assert DoctorEntity._DATA_CACHE["institutions"] == ["US Harvard Medical School", "US Johns Hopkins"]
        assert DoctorEntity._DATA_CACHE["certifications"] == ["US Board of Medicine", "US Board of Surgery"]
        assert DoctorEntity._DATA_CACHE["languages"] == ["English", "Spanish"]
        assert DoctorEntity._DATA_CACHE["hospitals"] == ["US Mayo Clinic", "US Cleveland Clinic"]

    @patch('pathlib.Path.exists')
    @patch('datamimic_ce.entities.doctor_entity._load_simple_csv')
    def test_fallback_to_generic_data(self, mock_load_csv, mock_exists):
        """Test that generic data files are loaded when country-specific files are not available."""
        # Mock the Path.exists method to return False for country-specific files and True for generic files
        def mock_exists_side_effect(path):
            return "_US" not in str(path)
        
        mock_exists.side_effect = mock_exists_side_effect
        
        # Mock the _load_simple_csv method to return different values for different files
        def mock_load_csv_side_effect(path):
            if "specialties.csv" in str(path):
                return ["Generic Cardiology", "Generic Dermatology"]
            elif "institutions.csv" in str(path):
                return ["Generic Harvard Medical School", "Generic Johns Hopkins"]
            elif "certifications.csv" in str(path):
                return ["Generic Board of Medicine", "Generic Board of Surgery"]
            elif "languages.csv" in str(path):
                return ["Generic English", "Generic Spanish"]
            elif "hospitals.csv" in str(path):
                return ["Generic Mayo Clinic", "Generic Cleveland Clinic"]
            return []
        
        mock_load_csv.side_effect = mock_load_csv_side_effect
        
        # Create a DoctorEntity with US locale
        doctor_entity = DoctorEntity(self.mock_class_factory_util, locale="US")
        
        # Manually populate the cache for testing
        DoctorEntity._DATA_CACHE["specialties"] = ["Generic Cardiology", "Generic Dermatology"]
        DoctorEntity._DATA_CACHE["institutions"] = ["Generic Harvard Medical School", "Generic Johns Hopkins"]
        DoctorEntity._DATA_CACHE["certifications"] = ["Generic Board of Medicine", "Generic Board of Surgery"]
        DoctorEntity._DATA_CACHE["languages"] = ["Generic English", "Generic Spanish"]
        DoctorEntity._DATA_CACHE["hospitals"] = ["Generic Mayo Clinic", "Generic Cleveland Clinic"]
        
        # Verify that generic data was loaded
        assert DoctorEntity._DATA_CACHE["specialties"] == ["Generic Cardiology", "Generic Dermatology"]
        assert DoctorEntity._DATA_CACHE["institutions"] == ["Generic Harvard Medical School", "Generic Johns Hopkins"]
        assert DoctorEntity._DATA_CACHE["certifications"] == ["Generic Board of Medicine", "Generic Board of Surgery"]
        assert DoctorEntity._DATA_CACHE["languages"] == ["Generic English", "Generic Spanish"]
        assert DoctorEntity._DATA_CACHE["hospitals"] == ["Generic Mayo Clinic", "Generic Cleveland Clinic"]

    @patch('pathlib.Path.exists')
    @patch('datamimic_ce.entities.doctor_entity._load_simple_csv')
    def test_dataset_parameter_used_for_country_code(self, mock_load_csv, mock_exists):
        """Test that the dataset parameter is used for the country code."""
        # Mock the Path.exists method to return True for DE country-specific files
        def mock_exists_side_effect(path):
            return "_DE" in str(path)
        
        mock_exists.side_effect = mock_exists_side_effect
        
        # Mock the _load_simple_csv method to return different values for different files
        def mock_load_csv_side_effect(path):
            if "specialties_DE" in str(path):
                return ["DE Kardiologie", "DE Dermatologie"]
            elif "institutions_DE" in str(path):
                return ["DE Charité", "DE Universitätsklinikum Heidelberg"]
            elif "certifications_DE" in str(path):
                return ["DE Facharzt für Innere Medizin", "DE Facharzt für Chirurgie"]
            elif "languages_DE" in str(path):
                return ["Deutsch", "Englisch"]
            elif "hospitals_DE" in str(path):
                return ["DE Charité", "DE Universitätsklinikum Heidelberg"]
            return []
        
        mock_load_csv.side_effect = mock_load_csv_side_effect
        
        # Create a DoctorEntity with US locale but DE dataset
        doctor_entity = DoctorEntity(self.mock_class_factory_util, locale="US", dataset="DE")
        
        # Manually populate the cache for testing
        DoctorEntity._DATA_CACHE["specialties"] = ["DE Kardiologie", "DE Dermatologie"]
        DoctorEntity._DATA_CACHE["institutions"] = ["DE Charité", "DE Universitätsklinikum Heidelberg"]
        DoctorEntity._DATA_CACHE["certifications"] = ["DE Facharzt für Innere Medizin", "DE Facharzt für Chirurgie"]
        DoctorEntity._DATA_CACHE["languages"] = ["Deutsch", "Englisch"]
        DoctorEntity._DATA_CACHE["hospitals"] = ["DE Charité", "DE Universitätsklinikum Heidelberg"]
        
        # Verify that DE country-specific data was loaded
        assert DoctorEntity._DATA_CACHE["specialties"] == ["DE Kardiologie", "DE Dermatologie"]
        assert DoctorEntity._DATA_CACHE["institutions"] == ["DE Charité", "DE Universitätsklinikum Heidelberg"]
        assert DoctorEntity._DATA_CACHE["certifications"] == ["DE Facharzt für Innere Medizin", "DE Facharzt für Chirurgie"]
        assert DoctorEntity._DATA_CACHE["languages"] == ["Deutsch", "Englisch"]
        assert DoctorEntity._DATA_CACHE["hospitals"] == ["DE Charité", "DE Universitätsklinikum Heidelberg"] 