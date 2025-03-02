# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from unittest import mock

from datamimic_ce.domains.common.data_loaders.country_loader import CountryDataLoader


class TestCountryDataLoader:
    """Test cases for the CountryDataLoader."""

    def test_initialization(self):
        """Test initialization of the CountryDataLoader."""
        loader = CountryDataLoader()
        assert loader._data_cache == {}

    @mock.patch("datamimic_ce.utils.file_util.FileUtil.read_csv_to_list_of_tuples_without_header")
    def test_load_country_data(self, mock_read_csv):
        """Test loading country data."""
        # Mock CSV data
        mock_country_data = [
            ("US", "en_US", "1", "United States", "331002651"),
            ("CA", "en_CA", "1", "Canada", "37742154"),
        ]
        mock_read_csv.return_value = mock_country_data

        # Load country data
        loader = CountryDataLoader()
        country_data = loader.load_country_data()

        # Check that the data was loaded correctly
        assert country_data == mock_country_data

        # Check that the file path was correct
        mock_read_csv.assert_called_once()
        args, kwargs = mock_read_csv.call_args
        assert "country.csv" in str(args[0])
        assert kwargs["delimiter"] == ","

        # Test caching
        mock_read_csv.reset_mock()
        country_data = loader.load_country_data()
        mock_read_csv.assert_not_called()

    @mock.patch("datamimic_ce.domains.common.data_loaders.country_loader.CountryDataLoader.load_country_data")
    def test_get_country_by_iso_code(self, mock_load_country):
        """Test getting a country by ISO code."""
        # Mock country data
        mock_country_data = [
            ("US", "en_US", "1", "United States", "331002651"),
            ("CA", "en_CA", "1", "Canada", "37742154"),
        ]
        mock_load_country.return_value = mock_country_data

        # Set up the index
        loader = CountryDataLoader()
        loader._COUNTRY_CODE_INDEX = {"US": 0, "CA": 1}

        # Get country by ISO code
        country = loader.get_country_by_iso_code("US")

        # Check that the country was loaded correctly
        assert country["iso_code"] == "US"
        assert country["default_language_locale"] == "en_US"
        assert country["phone_code"] == "1"
        assert country["name"] == "United States"
        assert country["population"] == "331002651"

        # Test with a different ISO code
        country = loader.get_country_by_iso_code("CA")
        assert country["name"] == "Canada"

        # Test with a non-existent ISO code
        country = loader.get_country_by_iso_code("XYZ")
        assert country is None

    @mock.patch("datamimic_ce.domains.common.data_loaders.country_loader.CountryDataLoader.load_country_data")
    @mock.patch("random.randint")
    def test_get_random_country(self, mock_randint, mock_load_country):
        """Test getting a random country."""
        # Mock country data
        mock_country_data = [
            ("US", "en_US", "1", "United States", "331002651"),
            ("CA", "en_CA", "1", "Canada", "37742154"),
        ]
        mock_load_country.return_value = mock_country_data
        mock_randint.return_value = 0

        # Get random country
        loader = CountryDataLoader()
        country = loader.get_random_country()

        # Check that the country was loaded correctly
        assert country["iso_code"] == "US"
        assert country["default_language_locale"] == "en_US"
        assert country["phone_code"] == "1"
        assert country["name"] == "United States"
        assert country["population"] == "331002651"
        mock_randint.assert_called_once_with(0, 1)  # Should be called with (0, len(country_data) - 1)

    @mock.patch("datamimic_ce.domains.common.data_loaders.country_loader.CountryDataLoader.load_country_data")
    @mock.patch("random.sample")
    def test_get_countries_batch(self, mock_sample, mock_load_country):
        """Test getting a batch of countries."""
        # Mock country data
        mock_country_data = [
            ("US", "en_US", "1", "United States", "331002651"),
            ("CA", "en_CA", "1", "Canada", "37742154"),
        ]
        mock_load_country.return_value = mock_country_data
        mock_sample.return_value = [0, 1]

        # Get countries batch
        loader = CountryDataLoader()
        countries = loader.get_countries_batch(2)

        # Check that the countries were loaded correctly
        assert len(countries) == 2
        assert countries[0]["iso_code"] == "US"
        assert countries[1]["iso_code"] == "CA"
        mock_sample.assert_called_once_with(range(2), 2)  # Should be called with (range(len(country_data)), count)

    def test_get_base_path_country(self):
        """Test getting the base path for country data."""
        loader = CountryDataLoader()
        country_path = loader._get_base_path_country()
        assert isinstance(country_path, Path)
        assert country_path.name == "common"
