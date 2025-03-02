# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.domains.common.models.city import City


class TestCity:
    """Test cases for the City model."""

    def test_initialization(self):
        """Test initialization of the City model."""
        # Create a city with all required fields
        city_data = {
            "name": "New York",
            "postal_code": "10001",
            "area_code": "212",
            "state_id": "NY",
            "state": "New York",
            "population": "8336817",
            "country": "United States",
            "country_code": "US",
        }
        city = City(**city_data)

        # Check that all fields are set correctly
        assert city.name == "New York"
        assert city.postal_code == "10001"
        assert city.area_code == "212"
        assert city.state_id == "NY"
        assert city.state == "New York"
        assert city.population == "8336817"
        assert city.country == "United States"
        assert city.country_code == "US"
        assert city.name_extension == ""  # Default value
        assert city.language is None  # Default value

        # Test with optional fields
        city_data["name_extension"] = "City"
        city_data["language"] = "en_US"
        city = City(**city_data)

        assert city.name == "New York"
        assert city.name_extension == "City"
        assert city.language == "en_US"

    def test_create_method(self):
        """Test the create class method."""
        city_data = {
            "name": "Los Angeles",
            "postal_code": "90001",
            "area_code": "213",
            "state_id": "CA",
            "state": "California",
            "population": "3979576",
            "country": "United States",
            "country_code": "US",
        }
        city = City.create(city_data)

        assert city.name == "Los Angeles"
        assert city.postal_code == "90001"
        assert city.area_code == "213"
        assert city.state_id == "CA"
        assert city.state == "California"
        assert city.population == "3979576"
        assert city.country == "United States"
        assert city.country_code == "US"

    def test_full_name_property(self):
        """Test the full_name property."""
        # Without name extension
        city = City(
            name="Chicago",
            postal_code="60601",
            area_code="312",
            state_id="IL",
            state="Illinois",
            population="2693976",
            country="United States",
            country_code="US",
        )
        assert city.full_name == "Chicago"

        # With name extension
        city = City(
            name="Chicago",
            postal_code="60601",
            area_code="312",
            state_id="IL",
            state="Illinois",
            population="2693976",
            country="United States",
            country_code="US",
            name_extension="City",
        )
        assert city.full_name == "Chicago City"

    def test_location_string_property(self):
        """Test the location_string property."""
        # With state and country
        city = City(
            name="Houston",
            postal_code="77001",
            area_code="713",
            state_id="TX",
            state="Texas",
            population="2320268",
            country="United States",
            country_code="US",
        )
        assert city.location_string == "Houston, Texas, United States"

        # Without state
        city = City(
            name="Houston",
            postal_code="77001",
            area_code="713",
            state_id="TX",
            state="",
            population="2320268",
            country="United States",
            country_code="US",
        )
        assert city.location_string == "Houston, United States"

        # Without country
        city = City(
            name="Houston",
            postal_code="77001",
            area_code="713",
            state_id="TX",
            state="Texas",
            population="2320268",
            country="",
            country_code="US",
        )
        assert city.location_string == "Houston, Texas"

        # Without state and country
        city = City(
            name="Houston",
            postal_code="77001",
            area_code="713",
            state_id="TX",
            state="",
            population="2320268",
            country="",
            country_code="US",
        )
        assert city.location_string == "Houston"

    def test_population_int_property(self):
        """Test the population_int property."""
        # Valid population
        city = City(
            name="Phoenix",
            postal_code="85001",
            area_code="602",
            state_id="AZ",
            state="Arizona",
            population="1680992",
            country="United States",
            country_code="US",
        )
        assert city.population_int == 1680992

        # Invalid population
        city = City(
            name="Phoenix",
            postal_code="85001",
            area_code="602",
            state_id="AZ",
            state="Arizona",
            population="N/A",
            country="United States",
            country_code="US",
        )
        assert city.population_int == 0

    def test_to_dict_method(self):
        """Test the to_dict method."""
        city_data = {
            "name": "Philadelphia",
            "postal_code": "19101",
            "area_code": "215",
            "state_id": "PA",
            "state": "Pennsylvania",
            "population": "1584064",
            "country": "United States",
            "country_code": "US",
            "name_extension": "City",
            "language": "en_US",
        }
        city = City(**city_data)
        city_dict = city.to_dict()

        # Check that all fields are in the dictionary
        assert city_dict["name"] == "Philadelphia"
        assert city_dict["postal_code"] == "19101"
        assert city_dict["area_code"] == "215"
        assert city_dict["state_id"] == "PA"
        assert city_dict["state"] == "Pennsylvania"
        assert city_dict["population"] == "1584064"
        assert city_dict["country"] == "United States"
        assert city_dict["country_code"] == "US"
        assert city_dict["name_extension"] == "City"
        assert city_dict["language"] == "en_US"

        # Check that private fields are not in the dictionary
        assert "_property_cache" not in city_dict
        assert "_dataset" not in city_dict

    def test_reset_method(self):
        """Test the reset method."""
        city = City(
            name="San Antonio",
            postal_code="78201",
            area_code="210",
            state_id="TX",
            state="Texas",
            population="1547253",
            country="United States",
            country_code="US",
        )

        # Access cached properties
        full_name = city.full_name
        location_string = city.location_string
        population_int = city.population_int

        # Verify the properties are cached
        assert city._full_name_cache == full_name
        assert city._location_string_cache == location_string
        assert city._population_int_cache == population_int

        # Reset the cache
        city.reset()

        # Check that the caches are cleared
        assert city._full_name_cache is None
        assert city._location_string_cache is None
        assert city._population_int_cache is None
