# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from unittest import mock

from datamimic_ce.domains.common.data_loaders.address_loader import AddressDataLoader


class TestAddressDataLoader:
    """Test cases for the AddressDataLoader."""

    def test_initialization(self):
        """Test initialization of the AddressDataLoader."""
        # Default initialization
        loader = AddressDataLoader()
        assert loader.country_code == "US"
        assert loader._data_cache == {}
        assert loader._current_dataset == "US"
        assert loader._city_loader is not None
        assert loader._country_loader is not None

        # Custom country code
        loader = AddressDataLoader(country_code="fr")
        assert loader.country_code == "FR"
        assert loader._current_dataset == "FR"

    @mock.patch("datamimic_ce.utils.file_util.FileUtil.read_csv_to_list_of_tuples_without_header")
    @mock.patch("pathlib.Path.exists")
    def test_load_street_data(self, mock_exists, mock_read_csv):
        """Test loading street data."""
        # Mock file existence
        mock_exists.return_value = True

        # Mock CSV data - should be a list of tuples
        mock_street_data = [
            ("Main Street",),
            ("Broadway",),
            ("Park Avenue",),
        ]
        mock_read_csv.return_value = mock_street_data

        # Load street data
        loader = AddressDataLoader()
        street_data = loader.load_street_data()

        # Check that the data was loaded correctly
        assert street_data == ["Main Street", "Broadway", "Park Avenue"]

        # Check that the file path was correct
        mock_read_csv.assert_called_once()
        args, kwargs = mock_read_csv.call_args
        assert "street_US.csv" in str(args[0])
        assert kwargs["delimiter"] == ";"

        # Test caching
        mock_read_csv.reset_mock()
        street_data = loader.load_street_data()
        mock_read_csv.assert_not_called()

    def test_load_house_numbers(self):
        """Test loading house numbers."""
        # US format
        loader = AddressDataLoader(country_code="US")
        house_numbers = loader.load_house_numbers()
        assert len(house_numbers) > 0
        assert all(house_numbers[i] == str(2*i + 1) for i in range(min(10, len(house_numbers))))

        # European format
        loader = AddressDataLoader(country_code="DE")
        house_numbers = loader.load_house_numbers()
        assert len(house_numbers) > 0
        assert all(house_numbers[i] == str(i + 1) for i in range(min(10, len(house_numbers))))

        # UK format with letters
        loader = AddressDataLoader(country_code="GB")
        house_numbers = loader.load_house_numbers()
        assert len(house_numbers) > 0
        assert "1A" in house_numbers
        assert "1B" in house_numbers

    def test_get_continent_for_country(self):
        """Test getting the continent for a country code."""
        loader = AddressDataLoader()

        # North America
        assert loader.get_continent_for_country("US") == "North America"
        assert loader.get_continent_for_country("CA") == "North America"

        # Europe
        assert loader.get_continent_for_country("GB") == "Europe"
        assert loader.get_continent_for_country("DE") == "Europe"
        assert loader.get_continent_for_country("FR") == "Europe"

        # Asia
        assert loader.get_continent_for_country("JP") == "Asia"
        assert loader.get_continent_for_country("CN") == "Asia"

        # Unknown
        assert loader.get_continent_for_country("XX") == "Unknown"

        # Test caching
        assert loader._CONTINENT_CACHE["US"] == "North America"

    @mock.patch("datamimic_ce.domains.common.data_loaders.address_loader.AddressDataLoader.load_street_data")
    @mock.patch("datamimic_ce.domains.common.data_loaders.address_loader.AddressDataLoader.load_house_numbers")
    @mock.patch("datamimic_ce.domains.common.data_loaders.city_loader.CityDataLoader.get_random_city")
    @mock.patch("datamimic_ce.domains.common.data_loaders.country_loader.CountryDataLoader.get_country_by_iso_code")
    @mock.patch("random.choice")
    @mock.patch("random.uniform")
    def test_get_random_address(self, mock_uniform, mock_choice, mock_get_country, mock_get_city, mock_load_house_numbers, mock_load_street_data):
        """Test getting a random address."""
        # Mock data
        mock_load_street_data.return_value = ["Main Street", "Broadway", "Park Avenue"]
        mock_load_house_numbers.return_value = ["1", "2", "3", "4", "5"]
        mock_choice.side_effect = ["Main Street", "1"]  # Street, house number
        mock_get_city.return_value = {
            "name": "New York",
            "state": "NY",
            "postal_code": "10001",
        }
        mock_get_country.return_value = {
            "name": "United States",
            "iso_code": "US",
        }
        mock_uniform.side_effect = [40.7128, -74.0060]  # latitude, longitude

        # Get random address
        loader = AddressDataLoader()
        address = loader.get_random_address()

        # Check that the address was generated correctly
        assert address["street"] == "Main Street"
        assert address["house_number"] == "1"
        assert address["city"] == "New York"
        assert address["state"] == "NY"
        assert address["postal_code"] == "10001"
        assert address["country"] == "United States"
        assert address["country_code"] == "US"
        assert address["continent"] == "North America"
        assert address["latitude"] == 40.7128
        assert address["longitude"] == -74.0060
        assert "phone" in address
        assert "mobile_phone" in address
        assert "fax" in address

    @mock.patch("datamimic_ce.domains.common.data_loaders.address_loader.AddressDataLoader.get_random_address")
    def test_get_addresses_batch(self, mock_get_random_address):
        """Test getting a batch of addresses."""
        # Mock data
        mock_address = {
            "street": "Main Street",
            "house_number": "1",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001",
            "country": "United States",
            "country_code": "US",
        }
        mock_get_random_address.return_value = mock_address

        # Get addresses batch
        loader = AddressDataLoader()
        addresses = loader.get_addresses_batch(3)

        # Check that the addresses were generated correctly
        assert len(addresses) == 3
        assert all(address == mock_address for address in addresses)
        assert mock_get_random_address.call_count == 3

    def test_generate_phone_number(self):
        """Test generating a phone number."""
        # US format
        loader = AddressDataLoader(country_code="US")
        phone = loader._generate_phone_number()
        assert phone.startswith("+1 (")
        assert "-" in phone

        # GB format
        loader = AddressDataLoader(country_code="GB")
        phone = loader._generate_phone_number()
        assert phone.startswith("+44 ")

        # DE format
        loader = AddressDataLoader(country_code="DE")
        phone = loader._generate_phone_number()
        assert phone.startswith("+49 ")

        # FR format
        loader = AddressDataLoader(country_code="FR")
        phone = loader._generate_phone_number()
        assert phone.startswith("+33 ")

        # Generic format
        loader = AddressDataLoader(country_code="XX")
        phone = loader._generate_phone_number()
        assert phone.startswith("+")

    def test_generate_mobile_number(self):
        """Test generating a mobile phone number."""
        # US format
        loader = AddressDataLoader(country_code="US")
        phone = loader._generate_mobile_number()
        assert phone.startswith("+1 (")
        assert "-" in phone

        # GB format
        loader = AddressDataLoader(country_code="GB")
        phone = loader._generate_mobile_number()
        assert phone.startswith("+44 7")

        # DE format
        loader = AddressDataLoader(country_code="DE")
        phone = loader._generate_mobile_number()
        assert phone.startswith("+49 ")
        prefix = phone.split(" ")[1]
        assert prefix in ["151", "152", "157", "160", "170", "171", "175"]

        # FR format
        loader = AddressDataLoader(country_code="FR")
        phone = loader._generate_mobile_number()
        assert phone.startswith("+33 6")

        # Generic format
        loader = AddressDataLoader(country_code="XX")
        phone = loader._generate_mobile_number()
        assert phone.startswith("+")

    def test_get_base_path_address(self):
        """Test getting the base path for address data."""
        loader = AddressDataLoader()
        address_path = loader._get_base_path_address()
        assert isinstance(address_path, Path)
        assert address_path.name == "address"
        assert address_path.parent.name == "common"
