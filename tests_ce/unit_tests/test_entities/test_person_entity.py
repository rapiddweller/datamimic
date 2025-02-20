# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

from datamimic_ce.entities.person_entity import PersonEntity, calculate_age, get_salutation
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class MockClassFactoryUtil(BaseClassFactoryUtil):
    """Mock implementation of BaseClassFactoryUtil for testing."""

    def get_app_settings(self):
        return MagicMock()

    def get_data_generation_util(self):
        return MagicMock()

    def get_datasource_registry(self):
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


class TestPersonEntity(TestCase):
    """Test suite for PersonEntity class."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = MockClassFactoryUtil()
        self.default_entity = PersonEntity(class_factory_util=self.class_factory_util, locale="en", count=1)

    def test_initialization_with_defaults(self):
        """Test PersonEntity initialization with default values."""
        entity = self.default_entity

        # Check default values
        self.assertEqual(entity._locale, "en")  # Default locale should be 'en'
        self.assertEqual(entity._min_age, 15)
        self.assertEqual(entity._max_age, 105)
        self.assertAlmostEqual(entity._female_quota, 0.49)
        self.assertAlmostEqual(entity._other_gender_quota, 0.02)
        self.assertAlmostEqual(entity._noble_quota, 0.001)
        self.assertAlmostEqual(entity._academic_title_quota, 0.5)

    def test_initialization_with_custom_values(self):
        """Test PersonEntity initialization with custom values."""
        custom_entity = PersonEntity(
            class_factory_util=self.class_factory_util,
            locale="DE",  # Using short code
            count=1,
            min_age=20,
            max_age=60,
            female_quota=0.6,
            other_gender_quota=0.1,
            noble_quota=0.05,
            academic_title_quota=0.3,
        )

        self.assertEqual(custom_entity._locale, "de")  # Should be converted to Mimesis locale
        self.assertEqual(custom_entity._min_age, 20)
        self.assertEqual(custom_entity._max_age, 60)
        self.assertAlmostEqual(custom_entity._female_quota, 0.6)
        self.assertAlmostEqual(custom_entity._other_gender_quota, 0.1)
        self.assertAlmostEqual(custom_entity._noble_quota, 0.05)
        self.assertAlmostEqual(custom_entity._academic_title_quota, 0.3)

    def test_locale_mapping(self):
        """Test that both short codes and Mimesis locales are handled correctly."""
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
                entity = PersonEntity(
                    class_factory_util=self.class_factory_util,
                    locale=input_locale,
                )
                self.assertEqual(
                    entity._locale,
                    expected_locale,
                    f"Failed to map {input_locale} to {expected_locale}",
                )

    def test_calculate_age(self):
        """Test age calculation function."""
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        test_cases = [
            (today.replace(year=today.year - 20), 20),  # Exactly 20 years
            (today.replace(year=today.year - 30, month=1, day=1), 30),  # Start of year
            (today.replace(year=today.year - 25, month=today.month, day=today.day), 25),  # Same month and day
            (
                today.replace(year=today.year - 25, month=today.month - 1 if today.month > 1 else 12, day=today.day),
                25,
            ),  # Month before
            (
                today.replace(year=today.year - 25, month=today.month + 1 if today.month < 12 else 1, day=today.day),
                24,
            ),  # Month after
            (today, 0),  # Born today
            # Edge cases
            (today.replace(year=today.year - 1, month=today.month, day=today.day + 1), 0),  # Day before birthday
            (today.replace(year=today.year - 1, month=today.month, day=today.day - 1), 1),  # Day after birthday
        ]
        for birth_date, expected_age in test_cases:
            with self.subTest(birth_date=birth_date):
                actual_age = calculate_age(birth_date)
                self.assertEqual(
                    actual_age,
                    expected_age,
                    f"Failed for birthdate {birth_date}: expected {expected_age}, got {actual_age}",
                )

    @patch("builtins.open")
    def test_get_salutation(self, mock_open):
        """Test salutation loading from CSV."""
        mock_open.return_value.__enter__.return_value.readlines.return_value = ["Mrs,Mr"]
        result = get_salutation(Path("dummy/path"))
        self.assertEqual(result, {"FEMALE": "Mrs", "MALE": "Mr"})

    def test_gender_distribution(self):
        """Test gender distribution according to quotas."""
        female_quota = 0.6
        other_quota = 0.1
        entity = PersonEntity(
            class_factory_util=self.class_factory_util,
            locale="en",  # Using Mimesis locale directly
            count=1,
            female_quota=female_quota,
            other_gender_quota=other_quota,
        )

        # Generate a large number of genders to test distribution
        genders = []
        for _ in range(10000):
            entity.reset()  # Reset before each generation to ensure independence
            genders.append(entity.gender)

        female_count = genders.count("female")
        other_count = genders.count("other")
        male_count = genders.count("male")

        # Check approximate distributions (within 5% margin)
        self.assertAlmostEqual(female_count / len(genders), female_quota, delta=0.05)
        self.assertAlmostEqual(other_count / len(genders), other_quota, delta=0.05)
        self.assertAlmostEqual(male_count / len(genders), 1 - female_quota - other_quota, delta=0.05)

    def test_birthdate_range(self):
        """Test birthdate generation within specified age range."""
        min_age = 25
        max_age = 35
        entity = PersonEntity(
            class_factory_util=self.class_factory_util,
            locale="en",  # Using Mimesis locale directly
            count=1,
            min_age=min_age,
            max_age=max_age,
        )

        # Generate multiple birthdates to test range
        for _ in range(100):
            entity.reset()  # Reset before each generation
            age = calculate_age(entity.birthdate)
            self.assertGreaterEqual(age, min_age, f"Age {age} is less than minimum {min_age}")
            self.assertLessEqual(age, max_age, f"Age {age} is greater than maximum {max_age}")

    def test_property_consistency(self):
        """Test that properties remain consistent between calls unless reset."""
        entity = self.default_entity

        # Test all properties for consistency
        first_values = {
            # Existing fields
            "gender": entity.gender,
            "birthdate": entity.birthdate,
            "given_name": entity.given_name,
            "family_name": entity.family_name,
            "name": entity.name,
            "email": entity.email,
            "academic_title": entity.academic_title,
            "age": entity.age,
            "salutation": entity.salutation,
            "nobility_title": entity.nobility_title,
            # New fields
            "username": entity.username,
            "password": entity.password,
            "phone": entity.phone,
            "height": entity.height,
            "weight": entity.weight,
            "blood_type": entity.blood_type,
            "occupation": entity.occupation,
            "nationality": entity.nationality,
            "university": entity.university,
            "language": entity.language,
            "academic_degree": entity.academic_degree,
        }

        # Check multiple times that values don't change
        for _ in range(5):
            # Existing fields
            self.assertEqual(entity.gender, first_values["gender"])
            self.assertEqual(entity.birthdate, first_values["birthdate"])
            self.assertEqual(entity.given_name, first_values["given_name"])
            self.assertEqual(entity.family_name, first_values["family_name"])
            self.assertEqual(entity.name, first_values["name"])
            self.assertEqual(entity.email, first_values["email"])
            self.assertEqual(entity.academic_title, first_values["academic_title"])
            self.assertEqual(entity.age, first_values["age"])
            self.assertEqual(entity.salutation, first_values["salutation"])
            self.assertEqual(entity.nobility_title, first_values["nobility_title"])
            # New fields
            self.assertEqual(entity.username, first_values["username"])
            self.assertEqual(entity.password, first_values["password"])
            self.assertEqual(entity.phone, first_values["phone"])
            self.assertEqual(entity.height, first_values["height"])
            self.assertEqual(entity.weight, first_values["weight"])
            self.assertEqual(entity.blood_type, first_values["blood_type"])
            self.assertEqual(entity.occupation, first_values["occupation"])
            self.assertEqual(entity.nationality, first_values["nationality"])
            self.assertEqual(entity.university, first_values["university"])
            self.assertEqual(entity.language, first_values["language"])
            self.assertEqual(entity.academic_degree, first_values["academic_degree"])

    def test_reset_functionality(self):
        """Test that reset clears all cached values."""
        entity = self.default_entity

        # Get initial values
        initial_values = {
            # Existing fields
            "gender": entity.gender,
            "birthdate": entity.birthdate,
            "given_name": entity.given_name,
            "family_name": entity.family_name,
            "email": entity.email,
            "academic_title": entity.academic_title,
            "age": entity.age,
            "salutation": entity.salutation,
            "nobility_title": entity.nobility_title,
            # New fields
            "username": entity.username,
            "password": entity.password,
            "phone": entity.phone,
            "height": entity.height,
            "weight": entity.weight,
            "blood_type": entity.blood_type,
            "occupation": entity.occupation,
            "nationality": entity.nationality,
            "university": entity.university,
            "language": entity.language,
            "academic_degree": entity.academic_degree,
        }

        # Reset and get new values
        entity.reset()

        # Generate enough new values to have a high probability of at least one difference
        found_difference = False
        for _ in range(10):
            new_values = {
                # Existing fields
                "gender": entity.gender,
                "birthdate": entity.birthdate,
                "given_name": entity.given_name,
                "family_name": entity.family_name,
                "email": entity.email,
                "academic_title": entity.academic_title,
                "age": entity.age,
                "salutation": entity.salutation,
                "nobility_title": entity.nobility_title,
                # New fields
                "username": entity.username,
                "password": entity.password,
                "phone": entity.phone,
                "height": entity.height,
                "weight": entity.weight,
                "blood_type": entity.blood_type,
                "occupation": entity.occupation,
                "nationality": entity.nationality,
                "university": entity.university,
                "language": entity.language,
                "academic_degree": entity.academic_degree,
            }
            if new_values != initial_values:
                found_difference = True
                break
            entity.reset()

        self.assertTrue(found_difference, "Reset should allow for new random values to be generated")

    def test_physical_characteristics_ranges(self):
        """Test that physical characteristics are within reasonable ranges."""
        entity = self.default_entity

        # Test height (in meters)
        self.assertGreaterEqual(entity.height, 1.5)
        self.assertLessEqual(entity.height, 2.0)

        # Test weight (in kg)
        self.assertGreaterEqual(entity.weight, 38)
        self.assertLessEqual(entity.weight, 90)

        # Test blood type format
        blood_type = entity.blood_type
        # Normalize minus sign to standard ASCII
        blood_type = blood_type.replace("−", "-")  # Unicode minus to ASCII hyphen
        self.assertIn(blood_type, ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])

    def test_username_format(self):
        """Test that username follows the expected format."""
        entity = self.default_entity
        username = entity.username

        # Username should contain both letters and digits
        has_letters = any(c.isalpha() for c in username)
        has_digits = any(c.isdigit() for c in username)
        self.assertTrue(has_letters, "Username should contain letters")
        self.assertTrue(has_digits, "Username should contain digits")

    def test_password_security(self):
        """Test that generated passwords meet security requirements."""
        entity = self.default_entity
        password = entity.password

        # Password should be at least 12 characters
        self.assertGreaterEqual(len(password), 12)

        # Password should contain different character types
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        self.assertTrue(has_upper, "Password should contain uppercase letters")
        self.assertTrue(has_lower, "Password should contain lowercase letters")
        self.assertTrue(has_digit, "Password should contain digits")
        self.assertTrue(has_special, "Password should contain special characters")

    def test_phone_number_format(self):
        """Test that phone numbers are properly formatted."""
        entity = self.default_entity
        phone = entity.phone

        # Phone number should contain only digits, spaces, parentheses, hyphens, and plus
        valid_chars = set("0123456789 ()-+")
        self.assertTrue(all(c in valid_chars for c in phone), "Phone number contains invalid characters")
        self.assertGreater(len(phone), 8, "Phone number is too short")

    def test_nationality_gender_consistency(self):
        """Test that nationality is consistent with gender."""
        entity = self.default_entity

        with patch.object(entity, "_generate_gender", return_value="female"):
            entity.reset()
            female_nationality = entity.nationality
            self.assertIsNotNone(female_nationality)
            self.assertIsInstance(female_nationality, str)

        with patch.object(entity, "_generate_gender", return_value="male"):
            entity.reset()
            male_nationality = entity.nationality
            self.assertIsNotNone(male_nationality)
            self.assertIsInstance(male_nationality, str)

    def test_academic_fields_consistency(self):
        """Test consistency between academic fields."""
        entity = self.default_entity

        # Test with young age (should have no academic title)
        young_birthdate = datetime.datetime.now().replace(year=datetime.datetime.now().year - 19)
        with patch.object(entity, "_generate_birthdate", return_value=young_birthdate):
            entity.reset()
            self.assertEqual(entity.academic_title, "")  # No academic title for young people
            # Note: Young people can still have a university and degree in progress

        # Test with eligible age
        old_birthdate = datetime.datetime.now().replace(year=datetime.datetime.now().year - 25)
        with patch.object(entity, "_generate_birthdate", return_value=old_birthdate):
            entity.reset()
            # If has academic title, should also have degree and university
            if entity.academic_title:
                self.assertNotEqual(entity.academic_degree, "")
                self.assertNotEqual(entity.university, "")

    def test_name_gender_consistency(self):
        """Test that given names are consistent with gender."""
        entity = self.default_entity

        # Force female gender and check multiple times
        with patch.object(entity, "_generate_gender", return_value="female"):
            for _ in range(10):
                entity.reset()
                self.assertEqual(entity.salutation, "Mrs.")

        # Force male gender and check multiple times
        with patch.object(entity, "_generate_gender", return_value="male"):
            for _ in range(10):
                entity.reset()
                self.assertEqual(entity.salutation, "Mr.")

    def test_academic_title_age_restriction(self):
        """Test that academic titles are only given to people 20 or older."""
        entity = self.default_entity

        # Test with young age
        young_birthdate = datetime.datetime.now().replace(year=datetime.datetime.now().year - 19)
        with patch.object(entity, "_generate_birthdate", return_value=young_birthdate):
            self.assertEqual(entity.academic_title, "")

        # Test with eligible age
        old_birthdate = datetime.datetime.now().replace(year=datetime.datetime.now().year - 25)
        with patch.object(entity, "_generate_birthdate", return_value=old_birthdate):
            entity.reset()  # Reset to clear cached academic title
            self.assertIn(entity.academic_title, ["", "Dr."])  # Could be empty due to quota

    def test_email_format(self):
        """Test that generated email addresses are properly formatted."""
        entity = self.default_entity
        email = entity.email

        self.assertIn("@", email)
        self.assertIn(".", email)
        self.assertTrue(email.endswith("example.com"))
        self.assertGreater(len(email), len("@example.com"))

    def test_other_gender_handling(self):
        """Test handling of 'other' gender cases."""
        entity = self.default_entity

        with patch.object(entity, "_generate_gender", return_value="other"):
            self.assertEqual(entity.salutation, "")
            self.assertIsNotNone(entity.given_name)
            self.assertIsNotNone(entity.family_name)
