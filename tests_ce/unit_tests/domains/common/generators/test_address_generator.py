# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from unittest import mock

from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.common.models.address import Address


class TestAddressGenerator:
    """Test cases for the AddressGenerator."""

    def test_initialization(self):
        """Test initialization of the AddressGenerator."""
        # Default initialization
        generator = AddressGenerator()
        assert generator.country_code == "US"
        assert generator._data_loader is not None

        # Custom country code
        generator = AddressGenerator(country_code="FR")
        assert generator.country_code == "FR"

        # With custom data loader
        mock_loader = mock.MagicMock()
        generator = AddressGenerator(data_loader=mock_loader)
        assert generator._data_loader == mock_loader

    @mock.patch("datamimic_ce.domains.common.data_loaders.address_loader.AddressDataLoader.get_random_address")
    def test_generate(self, mock_get_random_address):
        """Test generating an address."""
        # Mock address data
        mock_address_data = {
            "street": "Main Street",
            "house_number": "123",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001",
            "country": "United States",
            "country_code": "US",
            "continent": "North America",
            "latitude": 40.7128,
            "longitude": -74.0060,
        }
        mock_get_random_address.return_value = mock_address_data

        # Generate an address
        generator = AddressGenerator()
        address = generator.generate()

        # Check that the address was generated correctly
        assert isinstance(address, Address)
        assert address.street == "Main Street"
        assert address.house_number == "123"
        assert address.city == "New York"
        assert address.state == "NY"
        assert address.postal_code == "10001"
        assert address.country == "United States"
        assert address.country_code == "US"
        assert address.continent == "North America"
        assert address.latitude == 40.7128
        assert address.longitude == -74.0060

        # Check that the data loader was called
        mock_get_random_address.assert_called_once()

    @mock.patch("datamimic_ce.domains.common.data_loaders.address_loader.AddressDataLoader.get_addresses_batch")
    def test_generate_batch(self, mock_get_addresses_batch):
        """Test generating a batch of addresses."""
        # Mock address data
        mock_address_data = [
            {
                "street": "Main Street",
                "house_number": "123",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "United States",
                "country_code": "US",
            },
            {
                "street": "Broadway",
                "house_number": "1500",
                "city": "New York",
                "state": "NY",
                "postal_code": "10019",
                "country": "United States",
                "country_code": "US",
            },
        ]
        mock_get_addresses_batch.return_value = mock_address_data

        # Generate a batch of addresses
        generator = AddressGenerator()
        addresses = generator.generate_batch(2)

        # Check that the addresses were generated correctly
        assert len(addresses) == 2
        assert isinstance(addresses[0], Address)
        assert isinstance(addresses[1], Address)
        assert addresses[0].street == "Main Street"
        assert addresses[1].street == "Broadway"

        # Check that the data loader was called with the correct count
        mock_get_addresses_batch.assert_called_once_with(2)

        # Test with default count
        mock_get_addresses_batch.reset_mock()
        addresses = generator.generate_batch()
        mock_get_addresses_batch.assert_called_once_with(10)  # Default count is 10

    def test_set_country_code(self):
        """Test setting the country code."""
        # Create a generator with a mock data loader
        mock_loader = mock.MagicMock()
        generator = AddressGenerator(data_loader=mock_loader)

        # Set the country code
        generator.set_country_code("FR")

        # Check that the country code was set correctly
        assert generator.country_code == "FR"

        # Check that a new data loader was created
        assert generator._data_loader is not mock_loader
