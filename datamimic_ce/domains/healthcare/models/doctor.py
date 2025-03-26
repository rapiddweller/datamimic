# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Doctor entity model.

This module provides the Doctor entity model for generating realistic doctor data.
"""

import datetime
import random
import string
import uuid
from typing import Any

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.common.models.person import Person
from datamimic_ce.domains.healthcare.generators.doctor_generator import DoctorGenerator
from datamimic_ce.domains.healthcare.models.hospital import Hospital


class Doctor(BaseEntity):
    """Generate doctor data.

    This class generates realistic doctor data including doctor IDs,
    names, specialties, license numbers, contact information, education,
    certifications, and schedules.

    It uses PersonEntity for generating personal information and
    AddressEntity for generating address information.

    Data is loaded from country-specific CSV files when available,
    falling back to generic data files if needed.
    """

    # Class-level cache for shared data

    def __init__(self, doctor_generator: DoctorGenerator):
        """Initialize the Doctor entity."""
        super().__init__()
        self._doctor_generator = doctor_generator

    @property
    @property_cache
    def doctor_id(self) -> str:
        """Get the doctor ID.

        Returns:
            A unique identifier for the doctor.
        """
        return f"DOC-{uuid.uuid4().hex[:8].upper()}"

    @property
    @property_cache
    def npi_number(self) -> str:
        """Get the NPI (National Provider Identifier) number.

        Returns:
            A 10-digit NPI number.
        """
        return "".join(str(random.randint(0, 9)) for _ in range(10))

    @property
    @property_cache
    def license_number(self) -> str:
        """Get the medical license number.

        Returns:
            A medical license number.
        """
        prefix = "".join(random.choices(string.ascii_uppercase, k=2))
        number = "".join(random.choices(string.digits, k=6))
        return f"{prefix}-{number}"

    @property
    @property_cache
    def person_data(self) -> Person:
        return Person(self._doctor_generator.person_generator)

    @property
    @property_cache
    def given_name(self) -> str:
        """Get the doctor's given name.

        Returns:
            The doctor's given name.
        """
        return self.person_data.given_name

    @property
    @property_cache
    def family_name(self) -> str:
        """Get the doctor's family name.

        Returns:
            The doctor's family name.
        """
        return self.person_data.family_name

    @property
    @property_cache
    def full_name(self) -> str:
        """Get the doctor's full name.

        Returns:
            The doctor's full name.
        """
        return f"{self.given_name} {self.family_name}"

    @property
    @property_cache
    def gender(self) -> str:
        """Get the doctor's gender.

        Returns:
            The doctor's gender.
        """
        return self.person_data.gender

    @property
    @property_cache
    def birthdate(self) -> datetime.datetime:
        """Get the doctor's date of birth.

        Returns:
            The doctor's date of birth in YYYY-MM-DD format.
        """
        return self.person_data.birthdate

    @property
    @property_cache
    def age(self) -> int:
        """Get the doctor's age.

        Returns:
            The doctor's age in years.
        """
        return self.person_data.age

    @property
    @property_cache
    def specialty(self) -> str:
        """Get the doctor's medical specialty.

        Returns:
            The doctor's medical specialty.
        """
        return self._doctor_generator.generate_specialty()

    @property
    @property_cache
    def hospital(self) -> Hospital:
        return Hospital(self._doctor_generator.hospital_generator)

    @hospital.setter
    def hospital(self, value: Hospital) -> None:
        """Set the doctor's hospital.

        Args:
            value: The hospital to assign to the doctor.
        """
        self._field_cache["hospital"] = value

    @property
    @property_cache
    def medical_school(self) -> str:
        """Get the medical school the doctor attended.

        Returns:
            The name of the medical school.
        """
        return self._doctor_generator.generate_medical_school()

    @property
    @property_cache
    def graduation_year(self) -> int:
        """Get the year the doctor graduated from medical school.

        Returns:
            The graduation year.
        """
        current_year = datetime.datetime.now().year
        min_years_after_graduation = 0  # Minimum years after graduation
        max_years_after_graduation = 45  # Maximum years after graduation

        # Calculate graduation year based on age and years after graduation
        age = self.age
        years_after_graduation = random.randint(
            min_years_after_graduation,
            min(max_years_after_graduation, age - 25),  # Assume graduated at 25 at the earliest
        )
        return current_year - years_after_graduation

    @property
    @property_cache
    def years_of_experience(self) -> int:
        """Get the doctor's years of experience.

        Returns:
            The number of years of experience.
        """
        current_year = datetime.datetime.now().year
        return current_year - self.graduation_year

    @property
    @property_cache
    def certifications(self) -> list[str]:
        """Get the doctor's certifications.

        Returns:
            A list of certifications.
        """
        return self._doctor_generator.generate_certifications()

    @property
    @property_cache
    def accepting_new_patients(self) -> bool:
        """Get whether the doctor is accepting new patients.

        Returns:
            True if the doctor is accepting new patients, False otherwise.
        """
        return random.random() < 0.8  # 80% chance of accepting new patients

    @property
    @property_cache
    def office_hours(self) -> dict[str, str]:
        """Get the doctor's office hours.

        Returns:
            A dictionary mapping days to hours.
        """
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        hours = {}

        for day in days:
            if random.random() < 0.9:  # 90% chance of working on a weekday
                start_hour = random.randint(7, 10)
                end_hour = random.randint(16, 19)
                hours[day] = f"{start_hour:02d}:00 - {end_hour:02d}:00"
            else:
                hours[day] = "Closed"

        # Weekend hours
        for day in ["Saturday", "Sunday"]:
            if random.random() < 0.3:  # 30% chance of working on a weekend
                start_hour = random.randint(8, 11)
                end_hour = random.randint(14, 17)
                hours[day] = f"{start_hour:02d}:00 - {end_hour:02d}:00"
            else:
                hours[day] = "Closed"

        return hours

    @property
    @property_cache
    def email(self) -> str:
        """Get the doctor's email address.

        Returns:
            The doctor's email address.
        """
        return self.person_data.email

    @property
    def phone(self) -> str:
        """Get the doctor's phone number.

        Returns:
            The doctor's phone number.
        """
        return self.person_data.phone

    @property
    def address(self) -> Address:
        """Get the doctor's address.

        Returns:
            A dictionary containing the doctor's address information.
        """
        return self.person_data.address

    def to_dict(self) -> dict[str, Any]:
        """Convert the doctor entity to a dictionary.

        Returns:
            A dictionary containing all doctor properties.
        """
        return {
            "doctor_id": self.doctor_id,
            "npi_number": self.npi_number,
            "license_number": self.license_number,
            "given_name": self.given_name,
            "family_name": self.family_name,
            "full_name": self.full_name,
            "gender": self.gender,
            "birthdate": self.birthdate,
            "age": self.age,
            "specialty": self.specialty,
            "hospital": self.hospital,
            "medical_school": self.medical_school,
            "graduation_year": self.graduation_year,
            "years_of_experience": self.years_of_experience,
            "certifications": self.certifications,
            "accepting_new_patients": self.accepting_new_patients,
            "office_hours": self.office_hours,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
        }
