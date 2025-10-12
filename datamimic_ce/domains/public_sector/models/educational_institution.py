# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Educational institution entity model.

This module provides the EducationalInstitution entity model for generating
realistic educational institution data.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.domain_core import BaseEntity
from datamimic_ce.domains.domain_core.property_cache import property_cache
from datamimic_ce.domains.public_sector.generators.educational_institution_generator import (
    EducationalInstitutionGenerator,
)


class EducationalInstitution(BaseEntity):
    """Generate educational institution data.

    This class generates realistic educational institution data including
    school IDs, names, types, levels, addresses, contact information,
    staff counts, student counts, programs, and accreditations.

    It uses AddressEntity for generating address information.

    Data is loaded from country-specific CSV files when available,
    falling back to generic data files if needed.
    """

    def __init__(self, educational_institution_generator: EducationalInstitutionGenerator):
        super().__init__()
        self._educational_institution_generator = educational_institution_generator

    @property
    def dataset(self) -> str:
        """Expose dataset from generator."""
        return self._educational_institution_generator.dataset  #  reuse normalized dataset for CSV lookups

    # Property getters
    @property
    @property_cache
    def institution_id(self) -> str:
        """Get the institution ID.

        Returns:
            A unique identifier for the institution.
        """
        rng = self._educational_institution_generator.rng
        suffix = "".join(rng.choice("0123456789ABCDEF") for _ in range(8))
        return f"EDU-{suffix}"

    @property
    @property_cache
    def name(self) -> str:
        """Get the institution name.

        Returns:
            The institution name.
        """
        # Get city or address information for naming
        city = self.address.city
        state = self.address.state

        # Generate institution name based on type and level
        institution_type = self.type
        level = self.level

        # Name formats
        name_formats = []

        if "University" in institution_type:
            name_formats = [
                f"{city} University",
                f"University of {city}",
                f"{state} State University",
                f"{city} Technical University",
                f"{city} Metropolitan University",
            ]
        elif "College" in institution_type:
            name_formats = [
                f"{city} College",
                f"{city} Community College",
                f"{state} College",
                f"{city} Technical College",
                f"{city} Liberal Arts College",
            ]
        elif "School" in institution_type:
            if "Elementary" in level:
                name_formats = [
                    f"{city} Elementary School",
                    f"{city} Primary School",
                    f"{city} Academy",
                    f"Washington Elementary School of {city}",
                    "Lincoln Elementary School",
                ]
            elif "Middle" in level:
                name_formats = [
                    f"{city} Middle School",
                    f"{city} Intermediate School",
                    f"{city} Junior High School",
                    "Jefferson Middle School",
                    "Roosevelt Middle School",
                ]
            elif "High" in level:
                name_formats = [
                    f"{city} High School",
                    f"{city} Senior High School",
                    f"{state} High School",
                    "Kennedy High School",
                    "Roosevelt High School",
                ]
            else:
                name_formats = [
                    f"{city} Academy",
                    f"{city} School",
                    f"{city} {level} School",
                    f"{state} Academy",
                    f"Central School of {city}",
                ]

        if not name_formats:
            name_formats = [
                f"{city} Education Center",
                f"{city} Learning Institute",
                f"{city} Academy",
                f"{state} Institute",
                f"Central Institute of {city}",
            ]

        #  domain RNG must be deterministic via generator
        return self._educational_institution_generator.rng.choice(name_formats)

    @property
    @property_cache
    def type(self) -> str:
        """Get the institution type.

        Returns:
            The institution type.
        """
        #  move dataset I/O and weighted selection into generator helper
        return self._educational_institution_generator.pick_institution_type(start=Path(__file__))

    @property
    @property_cache
    def level(self) -> str:
        """Get the education level.

        Returns:
            The education level.
        """
        institution_type = self.type
        # Delegate to generator for consistent anti-repetition and dataset handling
        return self._educational_institution_generator.pick_level(institution_type, start=Path(__file__))

    @property
    @property_cache
    def founding_year(self) -> int:
        """Get the founding year.

        Returns:
            The founding year.
        """
        current_year = datetime.now().year
        min_age = 5  # Minimum age for a school
        max_age = 200  # Maximum age for a school (oldest universities)

        # Adjust based on institution type - universities tend to be older
        if "University" in self.type:
            min_age = 20
            max_age = 300
        elif "College" in self.type:
            min_age = 15
            max_age = 150

        return current_year - self._educational_institution_generator.rng.randint(min_age, max_age)

    @property
    @property_cache
    def student_count(self) -> int:
        """Get the student count.

        Returns:
            The number of students.
        """
        institution_type = self.type
        level = self.level

        # Adjust student count ranges based on institution type and level
        if "University" in institution_type:
            return self._educational_institution_generator.rng.randint(5000, 40000)
        elif "College" in institution_type:
            return self._educational_institution_generator.rng.randint(1000, 15000)
        elif "School" in institution_type:
            if "Elementary" in level:
                return self._educational_institution_generator.rng.randint(200, 800)
            elif "Middle" in level:
                return self._educational_institution_generator.rng.randint(300, 1000)
            elif "High" in level:
                return self._educational_institution_generator.rng.randint(500, 2500)
            else:
                return self._educational_institution_generator.rng.randint(200, 1500)
        else:
            return self._educational_institution_generator.rng.randint(100, 5000)

    @property
    @property_cache
    def staff_count(self) -> int:
        """Get the staff count.

        Returns:
            The number of staff members.
        """
        student_count = self.student_count
        student_to_staff_ratio = self._educational_institution_generator.rng.uniform(
            10, 25
        )  # Average student-to-staff ratio

        return max(5, int(student_count / student_to_staff_ratio))

    @property
    @property_cache
    def website(self) -> str:
        """Get the institution website.

        Returns:
            The institution website URL.
        """
        # Derive from name
        name = self.name.lower()

        # Simplified name for URL
        url_name = name.replace(" ", "")
        url_name = "".join(c for c in url_name if c.isalnum())

        # Determine domain extension based on type
        if "University" in self.type or "College" in self.type:
            domain = ".edu"
        elif "School" in self.type and "Public" in self.type:
            domain = ".k12.us"
        else:
            domain = ".org"

        return f"https://www.{url_name}{domain}"

    @property
    @property_cache
    def email(self) -> str:
        """Get the institution email address.

        Returns:
            The institution email address.
        """

        # Extract domain from website
        website = self.website
        domain = website.replace("https://www.", "")

        return f"info@{domain}"

    @property
    @property_cache
    def phone(self) -> str:
        """Get the institution phone number.

        Returns:
            The institution phone number.
        """
        return self._educational_institution_generator.phone_number_generator.generate()

    @property
    @property_cache
    def programs(self) -> list[str]:
        """Get the educational programs offered.

        Returns:
            A list of programs.
        """
        level = self.level
        # Map level to slug
        if "Elementary" in level:
            slug = "elementary"
        elif "Middle" in level:
            slug = "middle_school"
        elif "High" in level:
            slug = "high_school"
        elif any(k in level for k in ("Higher", "Undergraduate", "Graduate", "Postgraduate")):
            slug = "higher_education"
        elif any(k in level for k in ("Vocational", "Technical")):
            slug = "vocational"
        else:
            slug = "k12"

        return self._educational_institution_generator.pick_programs(slug, start=Path(__file__))

    @property
    @property_cache
    def accreditations(self) -> list[str]:
        """Get the institution accreditations.

        Returns:
            A list of accreditations.
        """
        institution_type = self.type
        return self._educational_institution_generator.pick_accreditations(institution_type, start=Path(__file__))

    @property
    @property_cache
    def facilities(self) -> list[str]:
        """Get the institution facilities.

        Returns:
            A list of facilities.
        """
        institution_type = self.type
        return self._educational_institution_generator.pick_facilities(institution_type, start=Path(__file__))

    @property
    @property_cache
    def address(self) -> Address:
        """Get the institution address.

        Returns:
            A dictionary containing the institution's address information.
        """
        return Address(self._educational_institution_generator.address_generator)

    def to_dict(self) -> dict[str, Any]:
        """Convert the educational institution entity to a dictionary.

        Returns:
            A dictionary containing all educational institution properties.
        """
        return {
            "institution_id": self.institution_id,
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "founding_year": self.founding_year,
            "student_count": self.student_count,
            "staff_count": self.staff_count,
            "website": self.website,
            "email": self.email,
            "phone": self.phone,
            "programs": self.programs,
            "accreditations": self.accreditations,
            "facilities": self.facilities,
            "address": self.address,
        }
