# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Hospital entity model.

This module provides the Hospital entity model for generating realistic hospital data.
"""


from datamimic_ce.domains.domain_core import BaseEntity
from datamimic_ce.domains.domain_core.property_cache import property_cache
from datamimic_ce.domains.healthcare.generators.hospital_generator import HospitalGenerator
from datamimic_ce.domains.shared.models.address import Address


class Hospital(BaseEntity):
    def __init__(self, hospital_generator: HospitalGenerator):
        super().__init__()
        self._hospital_generator = hospital_generator

    @property
    @property_cache
    def hospital_id(self) -> str:
        """Get the hospital ID.

        Returns:
            A unique identifier for the hospital.
        """
        candidate = self._hospital_generator.generate_hospital_id_candidate()
        return self._claim_identifier("hospital_id", candidate)

    @property
    @property_cache
    def name(self) -> str:
        """Get the hospital name.

        Returns:
            The hospital name.
        """
        city = self.address.city
        state = self.address.state

        return self._hospital_generator.generate_hospital_name(city, state)

    @property
    @property_cache
    def type(self) -> str:
        """Get the hospital type.

        Returns:
            The hospital type (e.g., "General", "Specialty", "Teaching").
        """
        return self._hospital_generator.get_hospital_type()

    @property
    @property_cache
    def departments(self) -> list[str]:
        """Get the hospital departments.

        Returns:
            A list of departments in the hospital.
        """
        return self._hospital_generator.generate_departments(self.type)

    @property
    @property_cache
    def services(self) -> list[str]:
        """Get the hospital services.

        Returns:
            A list of services offered by the hospital.
        """
        return self._hospital_generator.generate_services(self.type, self.departments)

    @property
    @property_cache
    def bed_count(self) -> int:
        """Get the hospital bed count.

        Returns:
            The number of beds in the hospital.
        """
        return self._hospital_generator.generate_bed_count(self.type)

    @property
    @property_cache
    def staff_count(self) -> int:
        """Get the hospital staff count.

        Returns:
            The number of staff members in the hospital.
        """
        return self._hospital_generator.generate_staff_count(self.bed_count)

    @property
    @property_cache
    def founding_year(self) -> int:
        """Get the hospital founding year.

        Returns:
            The year the hospital was founded.
        """
        return self._hospital_generator.generate_founding_year()

    @property
    @property_cache
    def accreditation(self) -> list[str]:
        """Get the hospital accreditations.

        Returns:
            A list of accreditations held by the hospital.
        """
        return self._hospital_generator.generate_accreditation(self.type)

    @property
    @property_cache
    def emergency_services(self) -> bool:
        """Get whether the hospital offers emergency services.

        Returns:
            True if the hospital offers emergency services, False otherwise.
        """
        return self._hospital_generator.generate_emergency_services(self.type)

    @property
    @property_cache
    def teaching_status(self) -> bool:
        """Get whether the hospital is a teaching hospital.

        Returns:
            True if the hospital is a teaching hospital, False otherwise.
        """
        return self._hospital_generator.generate_teaching_status(self.type)

    @property
    @property_cache
    def website(self) -> str:
        """Get the hospital website.

        Returns:
            The hospital website URL.
        """
        # Generate a website based on the hospital name
        name = self.name.lower()

        # Remove common words and special characters
        for word in ["hospital", "medical", "center", "health", "healthcare", "regional", "memorial"]:
            name = name.replace(word, "")

        # Replace spaces and special characters with empty strings
        import re

        name = re.sub(r"[^a-zA-Z0-9]", "", name)

        # If the name is too short, use a generic name
        if len(name) < 3:
            name = f"hospital{self.hospital_id.lower()}"

        # Generate domain extension based on country
        domain = f".{self._hospital_generator.dataset.lower()}"

        return f"https://www.{name}{domain}"

    @property
    @property_cache
    def phone(self) -> str:
        """Get the hospital phone number.

        Returns:
            The hospital phone number.
        """
        return self._hospital_generator.phone_number_generator.generate()

    @property
    @property_cache
    def email(self) -> str:
        """Get the hospital email address.

        Returns:
            The hospital email address.
        """
        # Generate an email based on the hospital name and website
        website = self.website

        # Extract domain from website
        domain = website.replace("https://www.", "")

        return f"info@{domain}"

    @property
    @property_cache
    def address(self) -> Address:
        """Get the hospital address.

        Returns:
            A dictionary containing the hospital address information.
        """
        return Address(self._hospital_generator.address_generator)

    def to_dict(self) -> dict[str, object]:
        """Convert the hospital entity to a dictionary.

        Returns:
            A dictionary containing all hospital properties.
        """
        return {
            "hospital_id": self.hospital_id,
            "name": self.name,
            "type": self.type,
            "departments": self.departments,
            "services": self.services,
            "bed_count": self.bed_count,
            "staff_count": self.staff_count,
            "founding_year": self.founding_year,
            "accreditation": self.accreditation,
            "emergency_services": self.emergency_services,
            "teaching_status": self.teaching_status,
            "website": self.website,
            "phone": self.phone,
            "email": self.email,
        }
