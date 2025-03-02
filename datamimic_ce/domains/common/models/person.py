# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Person model.

This module provides a model for representing a person.
"""

import random
from typing import Any

from datamimic_ce.core.base_entity import BaseEntity
from datamimic_ce.core.property_cache import property_cache
from datamimic_ce.domains.common.utils.random_utils import (
    random_element_with_exclusions,
    random_int_in_range,
)


class Person(BaseEntity):
    """Model for representing a person.

    This class provides a model for representing a person with common attributes
    such as name, age, gender, etc.
    """

    # Sample data for generating person attributes
    FIRST_NAMES_MALE = [
        "James",
        "John",
        "Robert",
        "Michael",
        "William",
        "David",
        "Richard",
        "Joseph",
        "Thomas",
        "Charles",
    ]
    FIRST_NAMES_FEMALE = [
        "Mary",
        "Patricia",
        "Jennifer",
        "Linda",
        "Elizabeth",
        "Barbara",
        "Susan",
        "Jessica",
        "Sarah",
        "Karen",
    ]
    LAST_NAMES = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor"]
    GENDERS = ["male", "female", "other"]
    EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "example.com"]
    PHONE_FORMATS = ["###-###-####", "(###) ###-####", "###.###.####"]
    STREET_TYPES = ["St", "Ave", "Blvd", "Rd", "Ln", "Dr", "Way", "Pl", "Ct"]
    CITIES = [
        "New York",
        "Los Angeles",
        "Chicago",
        "Houston",
        "Phoenix",
        "Philadelphia",
        "San Antonio",
        "San Diego",
        "Dallas",
        "San Jose",
    ]
    STATES = [
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "FL",
        "GA",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
    ]
    COUNTRIES = [
        "United States",
        "Canada",
        "United Kingdom",
        "Australia",
        "Germany",
        "France",
        "Japan",
        "China",
        "Brazil",
        "India",
    ]

    def __init__(self, class_factory_util=None, locale: str = "en", dataset: str | None = None):
        """Initialize the Person model.

        Args:
            class_factory_util: A utility for creating class instances.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
        """
        super().__init__(class_factory_util, locale, dataset)
        self._first_name = None
        self._last_name = None
        self._age = None
        self._gender = None
        self._email = None
        self._phone = None
        self._address = None

    @property
    def gender(self) -> str:
        """Get the gender of the person.

        Returns:
            The gender of the person.
        """
        if self._gender is None:
            self._gender = random_element_with_exclusions(self.GENDERS, [])
        return self._gender

    @property
    def first_name(self) -> str:
        """Get the first name of the person.

        Returns:
            The first name of the person.
        """
        if self._first_name is None:
            if self.gender == "male":
                self._first_name = random.choice(self.FIRST_NAMES_MALE)
            elif self.gender == "female":
                self._first_name = random.choice(self.FIRST_NAMES_FEMALE)
            else:
                # For "other" gender, choose from all names
                self._first_name = random.choice(self.FIRST_NAMES_MALE + self.FIRST_NAMES_FEMALE)
        return self._first_name

    @property
    def last_name(self) -> str:
        """Get the last name of the person.

        Returns:
            The last name of the person.
        """
        if self._last_name is None:
            self._last_name = random.choice(self.LAST_NAMES)
        return self._last_name

    @property
    def full_name(self) -> str:
        """Get the full name of the person.

        Returns:
            The full name of the person.
        """
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self) -> int:
        """Get the age of the person.

        Returns:
            The age of the person.
        """
        if self._age is None:
            self._age = random_int_in_range(18, 90)
        return self._age

    @property
    def email(self) -> str:
        """Get the email of the person.

        Returns:
            The email of the person.
        """
        if self._email is None:
            # Create an email based on first and last name
            first_initial = self.first_name[0].lower()
            last_name = self.last_name.lower()
            domain = random.choice(self.EMAIL_DOMAINS)

            # Add a random number to ensure uniqueness
            random_num = random.randint(1, 999)

            # 50% chance to use first initial + last name format
            if random.random() < 0.5:
                self._email = f"{first_initial}{last_name}{random_num}@{domain}"
            else:
                self._email = f"{last_name}.{first_initial}{random_num}@{domain}"
        return self._email

    @property
    def phone(self) -> str:
        """Get the phone number of the person.

        Returns:
            The phone number of the person.
        """
        if self._phone is None:
            # Choose a random phone format and replace # with random digits
            phone_format = random.choice(self.PHONE_FORMATS)
            self._phone = ""
            for char in phone_format:
                if char == "#":
                    self._phone += str(random.randint(0, 9))
                else:
                    self._phone += char
        return self._phone

    @property_cache
    def address(self) -> dict[str, str]:
        """Get the address of the person.

        Returns:
            The address of the person as a dictionary.
        """
        # Generate a random street number
        street_number = random.randint(1, 9999)

        # Generate a random street name
        street_name = random.choice(self.LAST_NAMES)
        street_type = random.choice(self.STREET_TYPES)

        # Generate a random city, state, zip code, and country
        city = random.choice(self.CITIES)
        state = random.choice(self.STATES)
        zip_code = f"{random.randint(10000, 99999)}"
        country = random.choice(self.COUNTRIES)

        return {
            "street": f"{street_number} {street_name} {street_type}",
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "country": country,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert the person to a dictionary.

        Returns:
            A dictionary representation of the person.
        """
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "age": self.age,
            "gender": self.gender,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
        }

    def reset(self) -> None:
        """Reset the person's attributes."""
        self._first_name = None
        self._last_name = None
        self._age = None
        self._gender = None
        self._email = None
        self._phone = None
        if hasattr(self.address, "reset_cache"):
            self.address.reset_cache(self)
