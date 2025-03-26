# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Police officer entity model.

This module provides the PoliceOfficer entity model for generating realistic police officer data.
"""

import datetime
import random
import uuid
from typing import Any

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.common.models.person import Person
from datamimic_ce.domains.public_sector.generators.police_officer_generator import PoliceOfficerGenerator


class PoliceOfficer(BaseEntity):
    """Generate police officer data.

    This class generates realistic police officer data including officer IDs,
    names, ranks, departments, badge numbers, employment information, and
    contact details.

    It uses PersonEntity for generating personal information and
    AddressEntity for generating address information.

    Data is loaded from country-specific CSV files when available,
    falling back to generic data files if needed.
    """

    def __init__(self, police_officer_generator: PoliceOfficerGenerator):
        super().__init__()
        self.police_officer_generator = police_officer_generator

    # Property getters
    @property
    @property_cache
    def officer_id(self) -> str:
        """Get the officer ID.

        Returns:
            A unique identifier for the officer.
        """
        return f"OFF-{uuid.uuid4().hex[:8].upper()}"

    @property
    @property_cache
    def badge_number(self) -> str:
        """Get the badge number.

        Returns:
            A badge number.
        """
        return f"{random.randint(1000, 9999)}"

    @property
    @property_cache
    def person_data(self) -> Person:
        return Person(self.police_officer_generator.person_generator)

    @property
    @property_cache
    def given_name(self) -> str:
        """Get the officer's given name.

        Returns:
            The officer's given name.
        """
        return self.person_data.given_name

    @property
    @property_cache
    def family_name(self) -> str:
        """Get the officer's family name.

        Returns:
            The officer's family name.
        """
        return self.person_data.family_name

    @property
    @property_cache
    def full_name(self) -> str:
        """Get the officer's full name.

        Returns:
            The officer's full name.
        """
        return f"{self.given_name} {self.family_name}"

    @property
    @property_cache
    def gender(self) -> str:
        """Get the officer's gender.

        Returns:
            The officer's gender.
        """
        return self.person_data.gender

    @property
    @property_cache
    def birthdate(self) -> str:
        """Get the officer's date of birth.

        Returns:
            The officer's date of birth in YYYY-MM-DD format.
        """
        return self.person_data.birthdate

    @property
    @property_cache
    def age(self) -> int:
        """Get the officer's age.

        Returns:
            The officer's age in years.
        """
        return self.person_data.age

    @property
    @property_cache
    def rank(self) -> str:
        """Get the officer's rank.

        Returns:
            The officer's rank.
        """
        return self.police_officer_generator.get_rank()

    @property
    @property_cache
    def department(self) -> str:
        """Get the department where the officer works.

        Returns:
            The name of the department.
        """
        return self.police_officer_generator.get_department()

    @property
    @property_cache
    def unit(self) -> str:
        """Get the unit the officer is assigned to.

        Returns:
            The unit name.
        """
        units = [
            "Patrol",
            "Traffic",
            "Detectives",
            "SWAT",
            "K-9",
            "Narcotics",
            "Homicide",
            "Internal Affairs",
            "Community Relations",
            "Juvenile",
            "Cyber Crimes",
            "Evidence",
            "Training",
        ]
        return random.choice(units)

    @property
    @property_cache
    def hire_date(self) -> str:
        """Get the date the officer was hired.

        Returns:
            The hire date in YYYY-MM-DD format.
        """
        # Calculate a reasonable hire date based on years_of_service
        years_of_service = random.randint(0, min(30, self.age - 21))  # Assume minimum age of 21 to join
        current_date = datetime.datetime.now()
        hire_date = current_date - datetime.timedelta(days=years_of_service * 365)
        return hire_date.strftime("%Y-%m-%d")

    @property
    @property_cache
    def years_of_service(self) -> int:
        """Get the officer's years of service.

        Returns:
            The number of years of service.
        """
        # Calculate years of service based on hire date
        hire_date = datetime.datetime.strptime(self.hire_date, "%Y-%m-%d")
        current_date = datetime.datetime.now()
        return (current_date - hire_date).days // 365

    @property
    @property_cache
    def certifications(self) -> list[str]:
        """Get the officer's certifications.

        Returns:
            A list of certifications.
        """
        all_certifications = [
            "Basic Law Enforcement",
            "Advanced Law Enforcement",
            "Firearms Training",
            "Defensive Tactics",
            "Emergency Vehicle Operations",
            "Crisis Intervention",
            "De-escalation Techniques",
            "First Aid/CPR",
            "Narcotics Investigation",
            "Hostage Negotiation",
            "K-9 Handler",
            "SWAT Operations",
            "Cyber Crime Investigation",
            "Crime Scene Investigation",
            "Motorcycle Patrol",
        ]

        num_certifications = random.randint(1, 4)
        return random.sample(all_certifications, num_certifications)

    @property
    @property_cache
    def languages(self) -> list[str]:
        """Get the languages spoken by the officer.

        Returns:
            A list of languages.
        """
        languages = ["English"]

        # Chance to add additional languages
        additional_languages = [
            "Spanish",
            "French",
            "German",
            "Chinese",
            "Arabic",
            "Russian",
            "Japanese",
            "Korean",
            "Portuguese",
            "Italian",
        ]
        num_additional = random.randint(0, 2)

        if num_additional > 0:
            languages.extend(random.sample(additional_languages, num_additional))

        return languages

    @property
    @property_cache
    def shift(self) -> str:
        """Get the officer's shift.

        Returns:
            The shift (e.g., 'Day', 'Night', 'Swing').
        """
        shifts = ["Day Shift (7AM-3PM)", "Evening Shift (3PM-11PM)", "Night Shift (11PM-7AM)", "Rotating Shift"]
        return random.choice(shifts)

    @property
    @property_cache
    def email(self) -> str:
        """Get the officer's email address.

        Returns:
            The officer's email address.
        """
        return self.police_officer_generator.email_address_generator.generate()

    @property
    @property_cache
    def phone(self) -> str:
        """Get the officer's phone number.

        Returns:
            The officer's phone number.
        """
        return self.police_officer_generator.phone_number_generator.generate()

    @property
    @property_cache
    def address(self) -> Address:
        """Get the officer's address.

        Returns:
            A dictionary containing the officer's address information.
        """
        return Address(self.police_officer_generator.address_generator)

    def to_dict(self) -> dict[str, Any]:
        """Convert the police officer entity to a dictionary.

        Returns:
            A dictionary containing all police officer properties.
        """
        return {
            "officer_id": self.officer_id,
            "badge_number": self.badge_number,
            "given_name": self.given_name,
            "family_name": self.family_name,
            "full_name": self.full_name,
            "gender": self.gender,
            "birthdate": self.birthdate,
            "age": self.age,
            "rank": self.rank,
            "department": self.department,
            "unit": self.unit,
            "hire_date": self.hire_date,
            "years_of_service": self.years_of_service,
            "certifications": self.certifications,
            "languages": self.languages,
            "shift": self.shift,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
        }
