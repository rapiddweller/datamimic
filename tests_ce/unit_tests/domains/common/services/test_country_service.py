# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from unittest import mock

import pytest

from datamimic_ce.domains.common.models.country import Country
from datamimic_ce.domains.common.services.country_service import CountryService


class TestCountryService:
    """Test cases for the CountryService."""

    def test_initialization(self):
        """Test initialization of the CountryService."""
        service = CountryService()
        assert service._countries == {}
        assert service._generator is not None

    @mock.patch("datamimic_ce.domains.common.generators.country_generator.CountryGenerator.generate")
    @mock.patch("uuid.uuid4")
    def test_create_country(self, mock_uuid4, mock_generate):
        """Test creating a country."""
        # Mock UUID
        mock_uuid4.return_value = "123"

        # Mock country
        mock_country = mock.MagicMock(spec=Country)
        mock_generate.return_value = mock_country

        # Create a country
        service = CountryService()
        country = service.create_country()

        # Check that the country was created correctly
        assert country == mock_country
        assert service._countries["country-123"] == mock_country
        mock_generate.assert_called_once()

    @mock.patch("datamimic_ce.domains.common.generators.country_generator.CountryGenerator.generate_batch")
    @mock.patch("uuid.uuid4")
    def test_create_countries_batch(self, mock_uuid4, mock_generate_batch):
        """Test creating a batch of countries."""
        # Mock UUIDs
        mock_uuid4.side_effect = ["123", "456"]

        # Mock countries
        mock_country1 = mock.MagicMock(spec=Country)
        mock_country2 = mock.MagicMock(spec=Country)
        mock_generate_batch.return_value = [mock_country1, mock_country2]

        # Create a batch of countries
        service = CountryService()
        countries = service.create_countries_batch(2)

        # Check that the countries were created correctly
        assert countries == [mock_country1, mock_country2]
        assert service._countries["country-123"] == mock_country1
        assert service._countries["country-456"] == mock_country2
        mock_generate_batch.assert_called_once_with(2)

        # Test with default count
        mock_generate_batch.reset_mock()
        mock_uuid4.side_effect = ["789", "012"]
        service.create_countries_batch()
        mock_generate_batch.assert_called_once_with(10)  # Default count is 10

    def test_get_country(self):
        """Test getting a country by ID."""
        # Create a service with a mock country
        service = CountryService()
        mock_country = mock.MagicMock(spec=Country)
        service._countries["country-123"] = mock_country

        # Get the country
        country = service.get_country("country-123")
        assert country == mock_country

        # Test with a non-existent ID
        with pytest.raises(KeyError):
            service.get_country("non-existent")

    @mock.patch("datamimic_ce.domains.common.generators.country_generator.CountryGenerator.get_by_iso_code")
    def test_get_country_by_iso_code(self, mock_get_by_iso_code):
        """Test getting a country by ISO code."""
        # Mock country
        mock_country = mock.MagicMock(spec=Country)
        mock_get_by_iso_code.return_value = mock_country

        # Get the country by ISO code
        service = CountryService()
        country = service.get_country_by_iso_code("US")
        assert country == mock_country
        mock_get_by_iso_code.assert_called_once_with("US")

        # Test with a non-existent ISO code
        mock_get_by_iso_code.reset_mock()
        mock_get_by_iso_code.return_value = None
        country = service.get_country_by_iso_code("XYZ")
        assert country is None
        mock_get_by_iso_code.assert_called_once_with("XYZ")

    def test_get_all_countries(self):
        """Test getting all countries."""
        # Create a service with mock countries
        service = CountryService()
        mock_country1 = mock.MagicMock(spec=Country)
        mock_country2 = mock.MagicMock(spec=Country)
        service._countries = {"country-123": mock_country1, "country-456": mock_country2}

        # Get all countries
        countries = service.get_all_countries()
        assert len(countries) == 2
        assert mock_country1 in countries
        assert mock_country2 in countries

        # Test with an empty service
        service._countries = {}
        countries = service.get_all_countries()
        assert countries == []

    def test_clear_countries(self):
        """Test clearing all countries."""
        # Create a service with mock countries
        service = CountryService()
        mock_country1 = mock.MagicMock(spec=Country)
        mock_country2 = mock.MagicMock(spec=Country)
        service._countries = {"country-123": mock_country1, "country-456": mock_country2}

        # Clear the countries
        service.clear_countries()
        assert service._countries == {}
