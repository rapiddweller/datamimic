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
from pathlib import Path
from typing import Any

from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.common.models.person import Person
from datamimic_ce.domains.domain_core import BaseEntity
from datamimic_ce.domains.domain_core.property_cache import property_cache
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
        self._police_officer_generator = police_officer_generator

    @property
    def police_officer_generator(self) -> PoliceOfficerGenerator:
        return self._police_officer_generator

    @property
    def dataset(self) -> str:
        return self._police_officer_generator.dataset  #  align downstream CSV reads with configured dataset

    # Property getters
    @property
    @property_cache
    def officer_id(self) -> str:
        """Get the officer ID.

        Returns:
            A unique identifier for the officer.
        """
        rng = self.police_officer_generator.rng
        suffix = "".join(rng.choice("0123456789ABCDEF") for _ in range(8))
        return f"OFF-{suffix}"

    @property
    @property_cache
    def badge_number(self) -> str:
        """Get the badge number.

        Returns:
            A badge number.
        """
        rng = self.police_officer_generator.rng
        return "".join(str(rng.randint(0, 9)) for _ in range(4))

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
        #  delegate to generator helper to keep model pure and allow dataset-driven units
        return self.police_officer_generator.pick_unit()

    @property
    @property_cache
    def hire_date(self) -> str:
        """Get the date the officer was hired.

        Returns:
            The hire date in YYYY-MM-DD format.
        """
        #  delegate date generation to generator for SOC and determinism
        return self.police_officer_generator.generate_hire_date(self.age)

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
        #  delegate dataset I/O and selection to generator helper
        return self.police_officer_generator.pick_certifications(start=Path(__file__))

    @property
    @property_cache
    def languages(self) -> list[str]:
        """Get the languages spoken by the officer.

        Returns:
            A list of languages.
        """
        return self.police_officer_generator.pick_languages(start=Path(__file__))

    @property
    @property_cache
    def shift(self) -> str:
        """Get the officer's shift.

        Returns:
            The shift (e.g., 'Day', 'Night', 'Swing').
        """
        return self.police_officer_generator.pick_shift(start=Path(__file__))

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
