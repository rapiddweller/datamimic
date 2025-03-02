# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from unittest import mock

from datamimic_ce.domains.common.generators.country_generator import CountryGenerator
from datamimic_ce.domains.common.models.country import Country


class TestCountryGenerator:
    """Test cases for the CountryGenerator."""

    def test_initialization(self):
        """Test initialization of the CountryGenerator."""
        # Default initialization
        generator = CountryGenerator()
        assert generator._data_loader is not None

        # With custom data loader
        mock_loader = mock.MagicMock()
        generator = CountryGenerator(data_loader=mock_loader)
        assert generator._data_loader == mock_loader

    @mock.patch("datamimic_ce.domains.common.data_loaders.country_loader.CountryDataLoader.get_random_country")
    def test_generate(self, mock_get_random_country):
        """Test generating a country."""
        # Mock country data
        mock_country_data = {
            "iso_code": "US",
            "name": "United States",
            "default_language_locale": "en_US",
            "phone_code": "1",
            "population": "331002651",
        }
        mock_get_random_country.return_value = mock_country_data

        # Generate a country
        generator = CountryGenerator()
        country = generator.generate()

        # Check that the country was generated correctly
        assert isinstance(country, Country)
        assert country.iso_code == "US"
        assert country.name == "United States"
        assert country.default_language_locale == "en_US"
        assert country.phone_code == "1"
        assert country.population == "331002651"

        # Check that the data loader was called
        mock_get_random_country.assert_called_once()

    @mock.patch("datamimic_ce.domains.common.data_loaders.country_loader.CountryDataLoader.get_countries_batch")
    def test_generate_batch(self, mock_get_countries_batch):
        """Test generating a batch of countries."""
        # Mock country data
        mock_country_data = [
            {
                "iso_code": "US",
                "name": "United States",
                "default_language_locale": "en_US",
                "phone_code": "1",
                "population": "331002651",
            },
            {
                "iso_code": "CA",
                "name": "Canada",
                "default_language_locale": "en_CA",
                "phone_code": "1",
                "population": "37742154",
            },
        ]
        mock_get_countries_batch.return_value = mock_country_data

        # Generate a batch of countries
        generator = CountryGenerator()
        countries = generator.generate_batch(2)

        # Check that the countries were generated correctly
        assert len(countries) == 2
        assert isinstance(countries[0], Country)
        assert isinstance(countries[1], Country)
        assert countries[0].iso_code == "US"
        assert countries[1].iso_code == "CA"

        # Check that the data loader was called with the correct count
        mock_get_countries_batch.assert_called_once_with(2)

        # Test with default count
        mock_get_countries_batch.reset_mock()
        countries = generator.generate_batch()
        mock_get_countries_batch.assert_called_once_with(10)  # Default count is 10

    @mock.patch("datamimic_ce.domains.common.data_loaders.country_loader.CountryDataLoader.get_country_by_iso_code")
    def test_get_by_iso_code(self, mock_get_country_by_iso_code):
        """Test getting a country by ISO code."""
        # Mock country data
        mock_country_data = {
            "iso_code": "US",
            "name": "United States",
            "default_language_locale": "en_US",
            "phone_code": "1",
            "population": "331002651",
        }
        mock_get_country_by_iso_code.return_value = mock_country_data

        # Get country by ISO code
        generator = CountryGenerator()
        country = generator.get_by_iso_code("US")

        # Check that the country was retrieved correctly
        assert isinstance(country, Country)
        assert country.iso_code == "US"
        assert country.name == "United States"
        assert country.default_language_locale == "en_US"
        assert country.phone_code == "1"
        assert country.population == "331002651"

        # Check that the data loader was called with the correct ISO code
        mock_get_country_by_iso_code.assert_called_once_with("US")

        # Test with a non-existent ISO code
        mock_get_country_by_iso_code.reset_mock()
        mock_get_country_by_iso_code.return_value = None
        country = generator.get_by_iso_code("XYZ")
        assert country is None
        mock_get_country_by_iso_code.assert_called_once_with("XYZ")
