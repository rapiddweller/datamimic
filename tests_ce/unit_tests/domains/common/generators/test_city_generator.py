# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from unittest import mock

from datamimic_ce.domains.common.generators.city_generator import CityGenerator
from datamimic_ce.domains.common.models.city import City


class TestCityGenerator:
    """Test cases for the CityGenerator."""

    def test_initialization(self):
        """Test initialization of the CityGenerator."""
        # Default initialization
        generator = CityGenerator()
        assert generator.country_code == "US"
        assert generator._data_loader is not None

        # Custom country code
        generator = CityGenerator(country_code="FR")
        assert generator.country_code == "FR"

        # With custom data loader
        mock_loader = mock.MagicMock()
        generator = CityGenerator(data_loader=mock_loader)
        assert generator._data_loader == mock_loader

    @mock.patch("datamimic_ce.domains.common.data_loaders.city_loader.CityDataLoader.get_random_city")
    def test_generate(self, mock_get_random_city):
        """Test generating a city."""
        # Mock city data
        mock_city_data = {
            "name": "New York",
            "postal_code": "10001",
            "area_code": "212",
            "state_id": "NY",
            "state": "New York",
            "population": "8336817",
            "language": "en_US",
            "name_extension": "City",
            "country": "United States",
            "country_code": "US",
        }
        mock_get_random_city.return_value = mock_city_data

        # Generate a city
        generator = CityGenerator()
        city = generator.generate()

        # Check that the city was generated correctly
        assert isinstance(city, City)
        assert city.name == "New York"
        assert city.postal_code == "10001"
        assert city.area_code == "212"
        assert city.state_id == "NY"
        assert city.state == "New York"
        assert city.population == "8336817"
        assert city.language == "en_US"
        assert city.name_extension == "City"
        assert city.country == "United States"
        assert city.country_code == "US"

        # Check that the data loader was called
        mock_get_random_city.assert_called_once()

    @mock.patch("datamimic_ce.domains.common.data_loaders.city_loader.CityDataLoader.get_cities_batch")
    def test_generate_batch(self, mock_get_cities_batch):
        """Test generating a batch of cities."""
        # Mock city data
        mock_city_data = [
            {
                "name": "New York",
                "postal_code": "10001",
                "area_code": "212",
                "state_id": "NY",
                "state": "New York",
                "population": "8336817",
                "language": "en_US",
                "name_extension": "City",
                "country": "United States",
                "country_code": "US",
            },
            {
                "name": "Los Angeles",
                "postal_code": "90001",
                "area_code": "213",
                "state_id": "CA",
                "state": "California",
                "population": "3979576",
                "language": "en_US",
                "name_extension": "",
                "country": "United States",
                "country_code": "US",
            },
        ]
        mock_get_cities_batch.return_value = mock_city_data

        # Generate a batch of cities
        generator = CityGenerator()
        cities = generator.generate_batch(2)

        # Check that the cities were generated correctly
        assert len(cities) == 2
        assert isinstance(cities[0], City)
        assert isinstance(cities[1], City)
        assert cities[0].name == "New York"
        assert cities[1].name == "Los Angeles"

        # Check that the data loader was called with the correct count
        mock_get_cities_batch.assert_called_once_with(2)

        # Test with default count
        mock_get_cities_batch.reset_mock()
        cities = generator.generate_batch()
        mock_get_cities_batch.assert_called_once_with(10)  # Default count is 10

    @mock.patch("datamimic_ce.domains.common.data_loaders.city_loader.CityDataLoader.get_city_by_index")
    def test_get_by_index(self, mock_get_city_by_index):
        """Test getting a city by index."""
        # Mock city data
        mock_city_data = {
            "name": "New York",
            "postal_code": "10001",
            "area_code": "212",
            "state_id": "NY",
            "state": "New York",
            "population": "8336817",
            "language": "en_US",
            "name_extension": "City",
            "country": "United States",
            "country_code": "US",
        }
        mock_get_city_by_index.return_value = mock_city_data

        # Get city by index
        generator = CityGenerator()
        city = generator.get_by_index(0)

        # Check that the city was retrieved correctly
        assert isinstance(city, City)
        assert city.name == "New York"
        assert city.postal_code == "10001"
        assert city.area_code == "212"
        assert city.state_id == "NY"
        assert city.state == "New York"
        assert city.population == "8336817"
        assert city.language == "en_US"
        assert city.name_extension == "City"
        assert city.country == "United States"
        assert city.country_code == "US"

        # Check that the data loader was called with the correct index
        mock_get_city_by_index.assert_called_once_with(0)

    def test_set_country_code(self):
        """Test setting the country code."""
        # Create a generator with a mock data loader
        mock_loader = mock.MagicMock()
        generator = CityGenerator(data_loader=mock_loader)

        # Set the country code
        generator.set_country_code("FR")

        # Check that the country code was set correctly
        assert generator.country_code == "FR"
        mock_loader.country_code = "FR"  # Check that the data loader's country code was updated
