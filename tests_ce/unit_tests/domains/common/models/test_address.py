# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.domains.common.models.address import Address


class TestAddress:
    """Test cases for the Address model."""

    def test_initialization(self):
        """Test initialization of the Address model."""
        # Create an address with all required fields
        address_data = {
            "street": "Main Street",
            "house_number": "123",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001",
            "country": "United States",
            "country_code": "US",
        }
        address = Address(**address_data)

        # Check that all fields are set correctly
        assert address.street == "Main Street"
        assert address.house_number == "123"
        assert address.city == "New York"
        assert address.state == "NY"
        assert address.postal_code == "10001"
        assert address.country == "United States"
        assert address.country_code == "US"
        assert address.continent is None  # Default value
        assert address.latitude is None  # Default value
        assert address.longitude is None  # Default value
        assert address.organization is None  # Default value
        assert address.phone is None  # Default value
        assert address.mobile_phone is None  # Default value
        assert address.fax is None  # Default value

        # Test with optional fields
        address_data.update(
            {
                "continent": "North America",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "organization": "ACME Corp",
                "phone": "+1 (212) 555-1234",
                "mobile_phone": "+1 (917) 555-5678",
                "fax": "+1 (212) 555-9876",
            }
        )
        address = Address(**address_data)

        assert address.continent == "North America"
        assert address.latitude == 40.7128
        assert address.longitude == -74.0060
        assert address.organization == "ACME Corp"
        assert address.phone == "+1 (212) 555-1234"
        assert address.mobile_phone == "+1 (917) 555-5678"
        assert address.fax == "+1 (212) 555-9876"

    def test_create_method(self):
        """Test the create class method."""
        address_data = {
            "street": "Broadway",
            "house_number": "1500",
            "city": "New York",
            "state": "NY",
            "postal_code": "10019",
            "country": "United States",
            "country_code": "US",
            "continent": "North America",
            "latitude": 40.7589,
            "longitude": -73.9851,
        }
        address = Address.create(address_data)

        assert address.street == "Broadway"
        assert address.house_number == "1500"
        assert address.city == "New York"
        assert address.state == "NY"
        assert address.postal_code == "10019"
        assert address.country == "United States"
        assert address.country_code == "US"
        assert address.continent == "North America"
        assert address.latitude == 40.7589
        assert address.longitude == -73.9851

    def test_formatted_address_property(self):
        """Test the formatted_address property."""
        # US format
        us_address = Address(
            street="Main Street",
            house_number="123",
            city="New York",
            state="NY",
            postal_code="10001",
            country="United States",
            country_code="US",
        )
        expected_us_format = "123 Main Street\nNew York, NY 10001\nUnited States"
        assert us_address.formatted_address == expected_us_format

        # UK format
        uk_address = Address(
            street="High Street",
            house_number="45",
            city="London",
            state="Greater London",
            postal_code="SW1A 1AA",
            country="United Kingdom",
            country_code="GB",
        )
        expected_uk_format = "45 High Street\nLondon\nGreater London\nSW1A 1AA\nUnited Kingdom"
        assert uk_address.formatted_address == expected_uk_format

        # German format
        de_address = Address(
            street="Hauptstraße",
            house_number="10",
            city="Berlin",
            state="Berlin",
            postal_code="10115",
            country="Germany",
            country_code="DE",
        )
        expected_de_format = "Hauptstraße 10\n10115 Berlin\nBerlin\nGermany"
        assert de_address.formatted_address == expected_de_format

        # French format
        fr_address = Address(
            street="Rue de Rivoli",
            house_number="1",
            city="Paris",
            state="Île-de-France",
            postal_code="75001",
            country="France",
            country_code="FR",
        )
        expected_fr_format = "1 Rue de Rivoli\n75001 Paris\nÎle-de-France\nFrance"
        assert fr_address.formatted_address == expected_fr_format

    def test_coordinates_property(self):
        """Test the coordinates property."""
        # With coordinates
        address = Address(
            street="Fifth Avenue",
            house_number="350",
            city="New York",
            state="NY",
            postal_code="10118",
            country="United States",
            country_code="US",
            latitude=40.7484,
            longitude=-73.9857,
        )
        expected_coordinates = {"latitude": 40.7484, "longitude": -73.9857}
        assert address.coordinates == expected_coordinates

        # Without coordinates
        address = Address(
            street="Fifth Avenue",
            house_number="350",
            city="New York",
            state="NY",
            postal_code="10118",
            country="United States",
            country_code="US",
        )
        expected_coordinates = {"latitude": 0.0, "longitude": 0.0}
        assert address.coordinates == expected_coordinates

    def test_zip_code_property(self):
        """Test the zip_code property."""
        address = Address(
            street="Pennsylvania Avenue",
            house_number="1600",
            city="Washington",
            state="DC",
            postal_code="20500",
            country="United States",
            country_code="US",
        )
        assert address.zip_code == "20500"
        assert address.zip_code == address.postal_code

    def test_to_dict_method(self):
        """Test the to_dict method."""
        address_data = {
            "street": "Wall Street",
            "house_number": "11",
            "city": "New York",
            "state": "NY",
            "postal_code": "10005",
            "country": "United States",
            "country_code": "US",
            "continent": "North America",
            "latitude": 40.7069,
            "longitude": -74.0113,
            "organization": "Stock Exchange",
            "phone": "+1 (212) 555-1000",
        }
        address = Address(**address_data)
        address_dict = address.to_dict()

        # Check that all fields are in the dictionary
        assert address_dict["street"] == "Wall Street"
        assert address_dict["house_number"] == "11"
        assert address_dict["city"] == "New York"
        assert address_dict["state"] == "NY"
        assert address_dict["postal_code"] == "10005"
        assert address_dict["country"] == "United States"
        assert address_dict["country_code"] == "US"
        assert address_dict["continent"] == "North America"
        assert address_dict["latitude"] == 40.7069
        assert address_dict["longitude"] == -74.0113
        assert address_dict["organization"] == "Stock Exchange"
        assert address_dict["phone"] == "+1 (212) 555-1000"

        # Check that private fields are not in the dictionary
        assert "_property_cache" not in address_dict

    def test_reset_method(self):
        """Test the reset method."""
        address = Address(
            street="Broadway",
            house_number="1500",
            city="New York",
            state="NY",
            postal_code="10019",
            country="United States",
            country_code="US",
            latitude=40.7589,
            longitude=-73.9851,
        )

        # Access cached properties
        formatted_address = address.formatted_address
        coordinates = address.coordinates

        # Verify the properties are cached
        assert address._formatted_address_cache == formatted_address
        assert address._coordinates_cache == coordinates

        # Reset the cache
        address.reset()

        # Check that the caches are cleared
        assert address._formatted_address_cache is None
        assert address._coordinates_cache is None
