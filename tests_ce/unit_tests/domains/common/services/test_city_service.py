# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from unittest import mock

import pytest

from datamimic_ce.domains.common.models.city import City
from datamimic_ce.domains.common.services.city_service import CityService


class TestCityService:
    """Test cases for the CityService."""

    def test_initialization(self):
        """Test initialization of the CityService."""
        service = CityService()
        assert service._cities == {}
        assert service._generators == {}
        assert service._default_country_code == "US"

    @mock.patch("datamimic_ce.domains.common.generators.city_generator.CityGenerator.generate")
    @mock.patch("uuid.uuid4")
    def test_create_city(self, mock_uuid4, mock_generate):
        """Test creating a city."""
        # Mock UUID
        mock_uuid4.return_value = "123"

        # Mock city
        mock_city = mock.MagicMock(spec=City)
        mock_generate.return_value = mock_city

        # Create a city
        service = CityService()
        city = service.create_city()

        # Check that the city was created correctly
        assert city == mock_city
        assert service._cities["city-123"] == mock_city
        mock_generate.assert_called_once()

        # Test with a specific country code
        mock_generate.reset_mock()
        mock_uuid4.return_value = "456"
        service.create_city(country_code="FR")
        mock_generate.assert_called_once()
        assert "FR" in service._generators

    @mock.patch("datamimic_ce.domains.common.generators.city_generator.CityGenerator.generate_batch")
    @mock.patch("uuid.uuid4")
    def test_create_cities_batch(self, mock_uuid4, mock_generate_batch):
        """Test creating a batch of cities."""
        # Mock UUIDs
        mock_uuid4.side_effect = ["123", "456"]

        # Mock cities
        mock_city1 = mock.MagicMock(spec=City)
        mock_city2 = mock.MagicMock(spec=City)
        mock_generate_batch.return_value = [mock_city1, mock_city2]

        # Create a batch of cities
        service = CityService()
        cities = service.create_cities_batch(2)

        # Check that the cities were created correctly
        assert cities == [mock_city1, mock_city2]
        assert service._cities["city-123"] == mock_city1
        assert service._cities["city-456"] == mock_city2
        mock_generate_batch.assert_called_once_with(2)

        # Test with default count
        mock_generate_batch.reset_mock()
        mock_uuid4.side_effect = ["789", "012"]
        service.create_cities_batch()
        mock_generate_batch.assert_called_once_with(10)  # Default count is 10

        # Test with a specific country code
        mock_generate_batch.reset_mock()
        mock_uuid4.side_effect = ["345", "678"]
        service.create_cities_batch(country_code="FR")
        mock_generate_batch.assert_called_once_with(10)
        assert "FR" in service._generators

    def test_get_city(self):
        """Test getting a city by ID."""
        # Create a service with a mock city
        service = CityService()
        mock_city = mock.MagicMock(spec=City)
        service._cities["city-123"] = mock_city

        # Get the city
        city = service.get_city("city-123")
        assert city == mock_city

        # Test with a non-existent ID
        with pytest.raises(KeyError):
            service.get_city("non-existent")

    def test_get_all_cities(self):
        """Test getting all cities."""
        # Create a service with mock cities
        service = CityService()
        mock_city1 = mock.MagicMock(spec=City)
        mock_city2 = mock.MagicMock(spec=City)
        service._cities = {"city-123": mock_city1, "city-456": mock_city2}

        # Get all cities
        cities = service.get_all_cities()
        assert len(cities) == 2
        assert mock_city1 in cities
        assert mock_city2 in cities

        # Test with an empty service
        service._cities = {}
        cities = service.get_all_cities()
        assert cities == []

    def test_clear_cities(self):
        """Test clearing all cities."""
        # Create a service with mock cities
        service = CityService()
        mock_city1 = mock.MagicMock(spec=City)
        mock_city2 = mock.MagicMock(spec=City)
        service._cities = {"city-123": mock_city1, "city-456": mock_city2}

        # Clear the cities
        service.clear_cities()
        assert service._cities == {}

    def test_set_default_country_code(self):
        """Test setting the default country code."""
        service = CityService()
        assert service._default_country_code == "US"

        # Set a new default country code
        service.set_default_country_code("FR")
        assert service._default_country_code == "FR"

    def test_get_generator(self):
        """Test getting a generator for a country code."""
        # Create a service
        service = CityService()

        # Get a generator
        generator1 = service._get_generator("US")

        # Check that the generator was created correctly
        assert generator1 is not None
        assert generator1.country_code == "US"
        assert service._generators["US"] == generator1

        # Test getting an existing generator
        generator2 = service._get_generator("US")
        assert generator2 is generator1  # Should be the same instance

        # Test with a different country code
        generator3 = service._get_generator("FR")
        assert generator3 is not None
        assert generator3.country_code == "FR"
        assert service._generators["FR"] == generator3
        assert generator3 is not generator1  # Should be a different instance
