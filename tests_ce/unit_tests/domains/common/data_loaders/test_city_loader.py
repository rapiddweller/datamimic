# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from unittest import mock

from datamimic_ce.domains.common.data_loaders.city_loader import CityDataLoader


class TestCityDataLoader:
    """Test cases for the CityDataLoader."""

    def test_initialization(self):
        """Test initialization of the CityDataLoader."""
        # Default initialization
        loader = CityDataLoader()
        assert loader._country_code == "US"

        # Custom country code
        loader = CityDataLoader(country_code="fr")
        assert loader._country_code == "FR"

    @mock.patch("datamimic_ce.domains.common.data_loaders.city_loader.Path.exists")
    @mock.patch("datamimic_ce.utils.file_util.FileUtil.read_csv_to_dict_of_tuples_with_header")
    def test_load_city_data(self, mock_read_csv, mock_exists):
        """Test loading city data."""
        # Mock file existence
        mock_exists.return_value = True

        # Mock CSV data
        mock_header_dict = {"name": 0, "postalCode": 1, "areaCode": 2, "state.id": 3, "population": 4}
        mock_city_data = [
            ("New York", "10001", "212", "NY", "8336817"),
            ("Los Angeles", "90001", "213", "CA", "3979576"),
        ]
        mock_read_csv.return_value = (mock_header_dict, mock_city_data)

        # Load city data
        loader = CityDataLoader()
        header_dict, city_data = loader._load_city_data()

        # Check that the data was loaded correctly
        assert header_dict == mock_header_dict
        assert city_data == mock_city_data

        # Check that the file path was correct
        mock_read_csv.assert_called_once()
        args, kwargs = mock_read_csv.call_args
        assert "city_US.csv" in str(args[0])
        assert kwargs["delimiter"] == ";"

        # Test caching
        mock_read_csv.reset_mock()
        header_dict, city_data = loader._load_city_data()
        mock_read_csv.assert_not_called()

    @mock.patch("datamimic_ce.domains.common.data_loaders.city_loader.Path.exists")
    @mock.patch("datamimic_ce.utils.file_util.FileUtil.read_csv_to_dict_of_tuples_with_header")
    def test_load_city_data_fallback(self, mock_read_csv, mock_exists):
        """Test fallback when loading city data."""
        # Mock file existence for fallback
        mock_exists.side_effect = [False, True]  # First file doesn't exist, fallback does

        # Mock CSV data for fallback
        mock_header_dict = {"name": 0, "postalCode": 1, "areaCode": 2, "state.id": 3, "population": 4}
        mock_city_data = [
            ("London", "SW1A", "020", "LDN", "8908081"),
            ("Manchester", "M1", "0161", "MAN", "547627"),
        ]
        mock_read_csv.return_value = (mock_header_dict, mock_city_data)

        # Load city data with fallback
        loader = CityDataLoader(country_code="XYZ")  # Non-existent country code
        header_dict, city_data = loader._load_city_data()

        # Check that the data was loaded correctly
        assert header_dict == mock_header_dict
        assert city_data == mock_city_data

        # Check that the file path was correct for the fallback
        mock_read_csv.assert_called_once()
        args, kwargs = mock_read_csv.call_args
        assert "city_US.csv" in str(args[0])
        assert kwargs["delimiter"] == ";"

    @mock.patch("datamimic_ce.domains.common.data_loaders.city_loader.Path.exists")
    @mock.patch("datamimic_ce.utils.file_util.FileUtil.read_csv_to_dict_of_tuples_with_header")
    def test_load_state_data(self, mock_read_csv, mock_exists):
        """Test loading state data."""
        # Mock file existence
        mock_exists.return_value = True

        # Mock city data first (needed to set _current_dataset)
        mock_city_header = {"name": 0, "postalCode": 1, "areaCode": 2, "state.id": 3, "population": 4}
        mock_city_data = [
            ("New York", "10001", "212", "NY", "8336817"),
            ("Los Angeles", "90001", "213", "CA", "3979576"),
        ]

        # Mock state data
        mock_state_header = {"id": 0, "name": 1}
        mock_state_data = [
            ("NY", "New York"),
            ("CA", "California"),
        ]

        # Set up the mock to return different values for different calls
        mock_read_csv.side_effect = [
            (mock_city_header, mock_city_data),
            (mock_state_header, mock_state_data),
        ]

        # Load city data first to set _current_dataset
        loader = CityDataLoader()
        loader._load_city_data()

        # Reset the mock to clear the call count
        mock_read_csv.reset_mock()
        mock_read_csv.side_effect = [(mock_state_header, mock_state_data)]

        # Load state data
        state_dict = loader.load_state_data()

        # Check that the data was loaded correctly
        assert state_dict == {"NY": "New York", "CA": "California"}

        # Check that the file path was correct
        mock_read_csv.assert_called_once()
        args, kwargs = mock_read_csv.call_args
        assert "state_US.csv" in str(args[0])

        # Test caching
        mock_read_csv.reset_mock()
        state_dict = loader.load_state_data()
        mock_read_csv.assert_not_called()

    @mock.patch("datamimic_ce.utils.file_util.FileUtil.read_csv_to_list_of_tuples_without_header")
    def test_load_country_name(self, mock_read_csv):
        """Test loading country name."""
        # Mock country data
        mock_country_data = [
            ("US", "en_US", "1", "United States", "331002651"),
            ("CA", "en_CA", "1", "Canada", "37742154"),
        ]
        mock_read_csv.return_value = mock_country_data

        # Load country name
        loader = CityDataLoader()
        country_name = loader.load_country_name()

        # Check that the data was loaded correctly
        assert country_name == "United States"

        # Check that the file path was correct
        mock_read_csv.assert_called_once()
        args, kwargs = mock_read_csv.call_args
        assert "country.csv" in str(args[0])
        assert kwargs["delimiter"] == ","

        # Test caching
        mock_read_csv.reset_mock()
        country_name = loader.load_country_name()
        mock_read_csv.assert_not_called()

    @mock.patch("datamimic_ce.domains.common.data_loaders.city_loader.CityDataLoader.load_city_data")
    @mock.patch("datamimic_ce.domains.common.data_loaders.city_loader.CityDataLoader.load_state_data")
    @mock.patch("datamimic_ce.domains.common.data_loaders.city_loader.CityDataLoader.load_country_name")
    def test_get_city_by_index(self, mock_load_country, mock_load_state, mock_load_city):
        """Test getting a city by index."""
        # Mock data
        mock_header_dict = {
            "name": 0,
            "postalCode": 1,
            "areaCode": 2,
            "state.id": 3,
            "population": 4,
            "language": 5,
            "nameExtension": 6,
        }
        mock_city_data = [
            ("New York", "10001", "212", "NY", "8336817", "en_US", "City"),
            ("Los Angeles", "90001", "213", "CA", "3979576", "en_US", ""),
        ]
        mock_state_dict = {"NY": "New York", "CA": "California"}
        mock_country_name = "United States"

        # Set up the mocks
        mock_load_city.return_value = (mock_header_dict, mock_city_data)
        mock_load_state.return_value = mock_state_dict
        mock_load_country.return_value = mock_country_name

        # Get city by index
        loader = CityDataLoader()
        city = loader._get_city_by_index(0)

        # Check that the city was loaded correctly
        assert city["name"] == "New York"
        assert city["postal_code"] == "10001"
        assert city["area_code"] == "212"
        assert city["state_id"] == "NY"
        assert city["state"] == "New York"
        assert city["population"] == "8336817"
        assert city["language"] == "en_US"
        assert city["name_extension"] == "City"
        assert city["country"] == "United States"
        assert city["country_code"] == "US"

        # Test with a different index
        city = loader._get_city_by_index(1)
        assert city["name"] == "Los Angeles"
        assert city["state"] == "California"

        # Test with an invalid index
        city = loader._get_city_by_index(999)
        assert city["name"] == "New York"  # Should default to index 0

    @mock.patch("datamimic_ce.domains.common.data_loaders.city_loader.CityDataLoader.load_city_data")
    @mock.patch("datamimic_ce.domains.common.data_loaders.city_loader.CityDataLoader.get_city_by_index")
    @mock.patch("random.randint")
    def test_get_random_city(self, mock_randint, mock_get_city, mock_load_city):
        """Test getting a random city."""
        # Mock data
        mock_header_dict = {"name": 0, "postalCode": 1, "areaCode": 2, "state.id": 3, "population": 4}
        mock_city_data = [
            ("New York", "10001", "212", "NY", "8336817"),
            ("Los Angeles", "90001", "213", "CA", "3979576"),
        ]
        mock_city = {
            "name": "New York",
            "postal_code": "10001",
            "area_code": "212",
            "state_id": "NY",
            "state": "New York",
            "population": "8336817",
            "country": "United States",
            "country_code": "US",
        }

        # Set up the mocks
        mock_load_city.return_value = (mock_header_dict, mock_city_data)
        mock_randint.return_value = 0
        mock_get_city.return_value = mock_city

        # Get random city
        loader = CityDataLoader()
        city = loader.get_random_city()

        # Check that the city was loaded correctly
        assert city == mock_city
        mock_randint.assert_called_once_with(0, 1)  # Should be called with (0, len(city_data) - 1)
        mock_get_city.assert_called_once_with(0)

    @mock.patch("datamimic_ce.domains.common.data_loaders.city_loader.CityDataLoader.load_city_data")
    @mock.patch("datamimic_ce.domains.common.data_loaders.city_loader.CityDataLoader.get_city_by_index")
    @mock.patch("random.sample")
    def test_get_cities_batch(self, mock_sample, mock_get_city, mock_load_city):
        """Test getting a batch of cities."""
        # Mock data
        mock_header_dict = {"name": 0, "postalCode": 1, "areaCode": 2, "state.id": 3, "population": 4}
        mock_city_data = [
            ("New York", "10001", "212", "NY", "8336817"),
            ("Los Angeles", "90001", "213", "CA", "3979576"),
        ]
        mock_city1 = {
            "name": "New York",
            "postal_code": "10001",
            "area_code": "212",
            "state_id": "NY",
            "state": "New York",
            "population": "8336817",
            "country": "United States",
            "country_code": "US",
        }
        mock_city2 = {
            "name": "Los Angeles",
            "postal_code": "90001",
            "area_code": "213",
            "state_id": "CA",
            "state": "California",
            "population": "3979576",
            "country": "United States",
            "country_code": "US",
        }

        # Set up the mocks
        mock_load_city.return_value = (mock_header_dict, mock_city_data)
        mock_sample.return_value = [0, 1]
        mock_get_city.side_effect = [mock_city1, mock_city2]

        # Get cities batch
        loader = CityDataLoader()
        cities = loader.get_cities_batch(2)

        # Check that the cities were loaded correctly
        assert cities == [mock_city1, mock_city2]
        mock_sample.assert_called_once_with(range(2), 2)  # Should be called with (range(len(city_data)), count)
        assert mock_get_city.call_count == 2
        mock_get_city.assert_has_calls([mock.call(0), mock.call(1)])

    def test_get_base_paths(self):
        """Test getting base paths."""
        loader = CityDataLoader()

        # Test city path
        city_path = loader._get_base_path_city()
        assert isinstance(city_path, Path)
        assert city_path.name == "city"
        assert city_path.parent.name == "common"

        # Test state path
        state_path = loader._get_base_path_state()
        assert isinstance(state_path, Path)
        assert state_path.name == "state"
        assert state_path.parent.name == "common"

        # Test country path
        country_path = loader._get_base_path_country()
        assert isinstance(country_path, Path)
        assert country_path.name == "common"
