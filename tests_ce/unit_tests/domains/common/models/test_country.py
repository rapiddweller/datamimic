# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.domains.common.models.country import Country


class TestCountry:
    """Test cases for the Country model."""

    def test_initialization(self):
        """Test initialization of the Country model."""
        # Create a country with all required fields
        country_data = {
            "iso_code": "US",
            "name": "United States",
            "default_language_locale": "en_US",
            "phone_code": "1",
            "population": "331002651",
        }
        country = Country(**country_data)

        # Check that all fields are set correctly
        assert country.iso_code == "US"
        assert country.name == "United States"
        assert country.default_language_locale == "en_US"
        assert country.phone_code == "1"
        assert country.population == "331002651"

    def test_create_method(self):
        """Test the create class method."""
        country_data = {
            "iso_code": "CA",
            "name": "Canada",
            "default_language_locale": "en_CA",
            "phone_code": "1",
            "population": "37742154",
        }
        country = Country.create(country_data)

        assert country.iso_code == "CA"
        assert country.name == "Canada"
        assert country.default_language_locale == "en_CA"
        assert country.phone_code == "1"
        assert country.population == "37742154"

    def test_population_int_property(self):
        """Test the population_int property."""
        # Valid population
        country = Country(
            iso_code="GB",
            name="United Kingdom",
            default_language_locale="en_GB",
            phone_code="44",
            population="67886011",
        )
        assert country.population_int == 67886011

        # Invalid population
        country = Country(
            iso_code="GB",
            name="United Kingdom",
            default_language_locale="en_GB",
            phone_code="44",
            population="N/A",
        )
        assert country.population_int == 0

    def test_to_dict_method(self):
        """Test the to_dict method."""
        country_data = {
            "iso_code": "DE",
            "name": "Germany",
            "default_language_locale": "de_DE",
            "phone_code": "49",
            "population": "83783942",
        }
        country = Country(**country_data)
        country_dict = country.to_dict()

        # Check that all fields are in the dictionary
        assert country_dict["iso_code"] == "DE"
        assert country_dict["name"] == "Germany"
        assert country_dict["default_language_locale"] == "de_DE"
        assert country_dict["phone_code"] == "49"
        assert country_dict["population"] == "83783942"

        # Check that private fields are not in the dictionary
        assert "_property_cache" not in country_dict

    def test_reset_method(self):
        """Test the reset method."""
        country = Country(
            iso_code="FR",
            name="France",
            default_language_locale="fr_FR",
            phone_code="33",
            population="65273511",
        )

        # Access cached properties
        population_int = country.population_int

        # Verify the properties are cached
        assert country._population_int_cache == population_int

        # Reset the cache
        country.reset()

        # Check that the caches are cleared
        assert country._population_int_cache is None
