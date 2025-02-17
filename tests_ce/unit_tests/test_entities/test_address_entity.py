# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from unittest import TestCase
from unittest.mock import MagicMock

from datamimic_ce.entities.address_entity import AddressEntity
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class MockClassFactoryUtil(BaseClassFactoryUtil):
    """Mock implementation of BaseClassFactoryUtil for testing."""

    def get_app_settings(self):
        return MagicMock()

    def get_data_generation_util(self):
        return MagicMock()

    def get_datasource_util_cls(self):
        return MagicMock()

    def get_datetime_generator(self):
        return MagicMock()

    def get_exporter_util(self):
        return MagicMock()

    def get_integer_generator(self):
        return MagicMock()

    def get_parser_util_cls(self):
        return MagicMock()

    def get_setup_logger_func(self):
        return MagicMock()

    def get_string_generator(self):
        return MagicMock()

    def get_task_util_cls(self):
        return MagicMock()


class TestAddressEntity(TestCase):
    """Test suite for AddressEntity class."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = MockClassFactoryUtil()
        self.default_entity = AddressEntity(class_factory_util=self.class_factory_util, locale="en")

    def test_initialization_with_defaults(self):
        """Test AddressEntity initialization with default values."""
        entity = self.default_entity
        self.assertEqual(entity._locale, "en")  # Default locale should be 'en'

    def test_initialization_with_custom_values(self):
        """Test AddressEntity initialization with custom values."""
        test_cases = [
            ("US", "en"),
            ("GB", "en-gb"),
            ("CN", "zh"),
            ("BR", "pt-br"),
            ("DE", "de"),
            ("en", "en"),  # Direct Mimesis locale
            ("de", "de"),  # Direct Mimesis locale
            ("fr", "fr"),  # Direct Mimesis locale
        ]

        for input_locale, expected_locale in test_cases:
            with self.subTest(input_locale=input_locale):
                entity = AddressEntity(
                    class_factory_util=self.class_factory_util,
                    locale=input_locale,
                )
                self.assertEqual(
                    entity._locale,
                    expected_locale,
                    f"Failed to map {input_locale} to {expected_locale}",
                )

    def test_property_consistency(self):
        """Test that properties remain consistent between calls unless reset."""
        entity = self.default_entity

        # Test all properties for consistency
        first_values = {
            "street": entity.street,
            "house_number": entity.house_number,
            "city": entity.city,
            "state": entity.state,
            "postal_code": entity.postal_code,
            "zip_code": entity.zip_code,
            "country": entity.country,
            "country_code": entity.country_code,
            "office_phone": entity.office_phone,
            "private_phone": entity.private_phone,
            "mobile_phone": entity.mobile_phone,
            "fax": entity.fax,
            "organization": entity.organization,
            "coordinates": entity.coordinates,
            "latitude": entity.latitude,
            "longitude": entity.longitude,
            "state_abbr": entity.state_abbr,
            "continent": entity.continent,
            "calling_code": entity.calling_code,
            "isd_code": entity.isd_code,
            "iata_code": entity.iata_code,
            "icao_code": entity.icao_code,
            "formatted_address": entity.formatted_address,
            "federal_subject": entity.federal_subject,
            "prefecture": entity.prefecture,
            "province": entity.province,
            "region": entity.region,
            "area": entity.area,
        }

        # Check multiple times that values don't change
        for _ in range(5):
            self.assertEqual(entity.street, first_values["street"])
            self.assertEqual(entity.house_number, first_values["house_number"])
            self.assertEqual(entity.city, first_values["city"])
            self.assertEqual(entity.state, first_values["state"])
            self.assertEqual(entity.postal_code, first_values["postal_code"])
            self.assertEqual(entity.zip_code, first_values["zip_code"])
            self.assertEqual(entity.country, first_values["country"])
            self.assertEqual(entity.country_code, first_values["country_code"])
            self.assertEqual(entity.office_phone, first_values["office_phone"])
            self.assertEqual(entity.private_phone, first_values["private_phone"])
            self.assertEqual(entity.mobile_phone, first_values["mobile_phone"])
            self.assertEqual(entity.fax, first_values["fax"])
            self.assertEqual(entity.organization, first_values["organization"])
            self.assertEqual(entity.coordinates, first_values["coordinates"])
            self.assertEqual(entity.latitude, first_values["latitude"])
            self.assertEqual(entity.longitude, first_values["longitude"])
            self.assertEqual(entity.state_abbr, first_values["state_abbr"])
            self.assertEqual(entity.continent, first_values["continent"])
            self.assertEqual(entity.calling_code, first_values["calling_code"])
            self.assertEqual(entity.isd_code, first_values["isd_code"])
            self.assertEqual(entity.iata_code, first_values["iata_code"])
            self.assertEqual(entity.icao_code, first_values["icao_code"])
            self.assertEqual(entity.formatted_address, first_values["formatted_address"])
            self.assertEqual(entity.federal_subject, first_values["federal_subject"])
            self.assertEqual(entity.prefecture, first_values["prefecture"])
            self.assertEqual(entity.province, first_values["province"])
            self.assertEqual(entity.region, first_values["region"])
            self.assertEqual(entity.area, first_values["area"])

    def test_reset_functionality(self):
        """Test that reset clears all cached values."""
        entity = self.default_entity

        # Get initial values
        initial_values = {
            "street": entity.street,
            "house_number": entity.house_number,
            "city": entity.city,
            "state": entity.state,
            "postal_code": entity.postal_code,
            "country": entity.country,
            "country_code": entity.country_code,
            "office_phone": entity.office_phone,
            "organization": entity.organization,
            "coordinates": entity.coordinates,
            "state_abbr": entity.state_abbr,
            "continent": entity.continent,
        }

        # Reset and get new values
        entity.reset()

        # Generate enough new values to have a high probability of at least one difference
        found_difference = False
        for _ in range(10):
            new_values = {
                "street": entity.street,
                "house_number": entity.house_number,
                "city": entity.city,
                "state": entity.state,
                "postal_code": entity.postal_code,
                "country": entity.country,
                "country_code": entity.country_code,
                "office_phone": entity.office_phone,
                "organization": entity.organization,
                "coordinates": entity.coordinates,
                "state_abbr": entity.state_abbr,
                "continent": entity.continent,
            }
            if new_values != initial_values:
                found_difference = True
                break
            entity.reset()

        self.assertTrue(found_difference, "Reset should allow for new random values to be generated")

    def test_phone_number_format(self):
        """Test that phone numbers are properly formatted."""
        entity = self.default_entity
        phone_numbers = [
            entity.office_phone,
            entity.private_phone,
            entity.mobile_phone,
            entity.fax,
        ]

        for phone in phone_numbers:
            # Check format: (+XXX) XXX-XXX-XXXX
            self.assertRegex(
                phone,
                r"^\(\+\d{1,3}\) \d{3}-\d{3}-\d{4}$",
                f"Phone number {phone} does not match expected format",
            )

    def test_coordinates_format(self):
        """Test that coordinates are properly formatted."""
        entity = self.default_entity
        coords = entity.coordinates

        # Test dictionary structure
        self.assertIn("latitude", coords)
        self.assertIn("longitude", coords)

        # Test value ranges
        self.assertGreaterEqual(coords["latitude"], -90)
        self.assertLessEqual(coords["latitude"], 90)
        self.assertGreaterEqual(coords["longitude"], -180)
        self.assertLessEqual(coords["longitude"], 180)

        # Test individual properties
        self.assertEqual(entity.latitude, coords["latitude"])
        self.assertEqual(entity.longitude, coords["longitude"])

    def test_organization_format(self):
        """Test that organization names are properly formatted."""
        entity = self.default_entity
        org_name = entity.organization

        # Test format: {City} {Suffix}
        self.assertTrue(
            any(suffix in org_name for suffix in ["Inc.", "Ltd.", "LLC", "Corp.", "Group", "Holdings"]),
            f"Organization name {org_name} does not contain expected suffix",
        )

    def test_area_code_extraction(self):
        """Test that area codes are properly extracted from phone numbers."""
        entity = self.default_entity
        phone = entity.office_phone
        area = entity.area

        # Area should be the part between parentheses
        expected_area = phone[phone.find("(") + 1 : phone.find(")")]
        self.assertEqual(area, expected_area)

    def test_state_aliases(self):
        """Test that state aliases return the same value."""
        entity = self.default_entity
        state_value = entity.state

        self.assertEqual(entity.federal_subject, state_value)
        self.assertEqual(entity.prefecture, state_value)
        self.assertEqual(entity.province, state_value)
        self.assertEqual(entity.region, state_value)

    def test_postal_code_aliases(self):
        """Test that postal code aliases return the same value."""
        entity = self.default_entity
        postal_code = entity.postal_code

        self.assertEqual(entity.zip_code, postal_code)

    def test_calling_code_aliases(self):
        """Test that calling code aliases return the same value."""
        entity = self.default_entity
        calling_code = entity.calling_code

        self.assertEqual(entity.isd_code, calling_code)

    def test_country_code_format(self):
        """Test that country codes are in correct ISO format."""
        entity = self.default_entity
        country_code = entity.country_code

        # Should be ISO 3166-1 alpha-2 format (two uppercase letters)
        self.assertRegex(country_code, r"^[A-Z]{2}$")
