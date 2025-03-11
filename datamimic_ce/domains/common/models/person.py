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

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.common.generators.person_generator import PersonGenerator 
from datamimic_ce.domains.common.models.address import Address


class Person(BaseEntity):
    """Model for representing a person.

    This class provides a model for representing a person with common attributes
    such as name, age, gender, etc.
    """

    # # Sample data for generating person attributes
    # FIRST_NAMES_MALE = [
    #     "James",
    #     "John",
    #     "Robert",
    #     "Michael",
    #     "William",
    #     "David",
    #     "Richard",
    #     "Joseph",
    #     "Thomas",
    #     "Charles",
    # ]
    # FIRST_NAMES_FEMALE = [
    #     "Mary",
    #     "Patricia",
    #     "Jennifer",
    #     "Linda",
    #     "Elizabeth",
    #     "Barbara",
    #     "Susan",
    #     "Jessica",
    #     "Sarah",
    #     "Karen",
    # ]
    # LAST_NAMES = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor"]
    # GENDERS = ["male", "female", "other"]
    # EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "example.com"]
    # PHONE_FORMATS = ["###-###-####", "(###) ###-####", "###.###.####"]
    # STREET_TYPES = ["St", "Ave", "Blvd", "Rd", "Ln", "Dr", "Way", "Pl", "Ct"]
    # CITIES = [
    #     "New York",
    #     "Los Angeles",
    #     "Chicago",
    #     "Houston",
    #     "Phoenix",
    #     "Philadelphia",
    #     "San Antonio",
    #     "San Diego",
    #     "Dallas",
    #     "San Jose",
    # ]
    # STATES = [
    #     "AL",
    #     "AK",
    #     "AZ",
    #     "AR",
    #     "CA",
    #     "CO",
    #     "CT",
    #     "DE",
    #     "FL",
    #     "GA",
    #     "HI",
    #     "ID",
    #     "IL",
    #     "IN",
    #     "IA",
    #     "KS",
    #     "KY",
    #     "LA",
    #     "ME",
    #     "MD",
    # ]
    # COUNTRIES = [
    #     "United States",
    #     "Canada",
    #     "United Kingdom",
    #     "Australia",
    #     "Germany",
    #     "France",
    #     "Japan",
    #     "China",
    #     "Brazil",
    #     "India",
    # ]

    def __init__(self, person_generator: PersonGenerator):
        super().__init__()
        self._person_generator = person_generator
        
    @property
    @property_cache
    def gender(self) -> str:
        """Get the gender of the person.

        Returns:
            The gender of the person.
        """
        return self._person_generator.gender_generator.generate()

    @property
    @property_cache
    def first_name(self) -> str:
        """Get the first name of the person.

        Returns:
            The first name of the person.
        """
        return self._person_generator.given_name_generator.generate()

    @property
    @property_cache
    def last_name(self) -> str:
        """Get the last name of the person.

        Returns:
            The last name of the person.
        """
        return self._person_generator.family_name_generator.generate()

    @property
    @property_cache
    def full_name(self) -> str:
        """Get the full name of the person.

        Returns:
            The full name of the person.
        """
        return f"{self.first_name} {self.last_name}"

    @property
    @property_cache
    def age(self) -> int:
        """Get the age of the person.

        Returns:
            The age of the person.
        """
        return random.randint(0, 100)

    @property
    @property_cache
    def email(self) -> str:
        """Get the email of the person.

        Returns:
            The email of the person.
        """
        return self._person_generator.email_generator.generate_with_name(self.first_name, self.last_name)
    
    @property
    @property_cache
    def phone(self) -> str:
        """Get the phone number of the person.

        Returns:
            The phone number of the person.
        """
        return self._person_generator.phone_generator.generate()

    @property
    @property_cache
    def address(self) -> Address:
        """Get the address of the person.

        Returns:
            The address of the person as a dictionary.
        """
        return Address(self._person_generator.address_generator)

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

