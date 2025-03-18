# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Person model.

This module provides a model for representing a person.
"""

from datetime import datetime
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
    def given_name(self) -> str:
        """Get the first name of the person.

        Returns:
            The first name of the person.
        """
        return self._person_generator.given_name_generator.generate()

    @property
    @property_cache
    def family_name(self) -> str:
        """Get the last name of the person.

        Returns:
            The last name of the person.
        """
        return self._person_generator.family_name_generator.generate()

    @property
    @property_cache
    def name(self) -> str:
        """Get the full name of the person.

        Returns:
            The full name of the person.
        """
        return f"{self.given_name} {self.family_name}"

    @property
    @property_cache
    def age(self) -> int:
        """Get the age of the person.

        Returns:
            The age of the person.
        """
        return self._person_generator.birthdate_generator.convert_birthdate_to_age(self.birthdate)

    @property
    @property_cache
    def email(self) -> str:
        """Get the email of the person.

        Returns:
            The email of the person.
        """
        return self._person_generator.email_generator.generate_with_name(self.given_name, self.family_name)
    
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
    
    @property
    @property_cache
    def birthdate(self) -> datetime:
        """Get the birthdate of the person.

        Returns:
            The birthdate of the person.
        """
        return self._person_generator.birthdate_generator.generate()
    
    @property
    @property_cache
    def academic_title(self) -> str:
        """Get the academic title of the person.
        """
        return self._person_generator.academic_title_generator.generate()
    
    @property
    @property_cache
    def nobility_title(self) -> str:
        """Get the nobility title of the person.
        """
        return self._person_generator.nobility_title_generator.generate()
        
    @property
    @property_cache
    def salutation(self) -> str:
        """Get the salutation of the person.
        """
        gender = self.gender.upper()

        return self._person_generator.get_salutation_data(gender)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the person to a dictionary.

        Returns:
            A dictionary representation of the person.
        """
        return {
            "birthdate": self.birthdate,
            "given_name": self.given_name,
            "family_name": self.family_name,
            "gender": self.gender,
            "name": self.name,
            "age": self.age,
            "email": self.email,
            "phone": self.phone,
            "academic_title": self.academic_title,
            "salutation": self.salutation,
            "nobility_title": self.nobility_title,
        }
