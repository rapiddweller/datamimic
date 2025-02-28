# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Core implementation of the DoctorEntity class.
"""

from typing import Any

from datamimic_ce.entities.entity import Entity
from datamimic_ce.entities.entity_util import EntityUtil
from datamimic_ce.entities.healthcare.doctor_entity.generators import DoctorGenerators
from datamimic_ce.entities.healthcare.doctor_entity.utils import PropertyCache


class DoctorEntity(Entity):
    """Generate doctor data.

    This class generates realistic doctor data including doctor IDs,
    names, specialties, license numbers, contact information, education,
    certifications, and schedules.

    It uses PersonEntity for generating personal information and
    AddressEntity for generating address information.

    Data is loaded from country-specific CSV files when available,
    falling back to generic data files if needed.
    """

    def __init__(
        self,
        class_factory_util: Any,
        locale: str = "en",
        dataset: str | None = None,
    ):
        """Initialize the DoctorEntity.

        Args:
            class_factory_util: The class factory utility.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
        """
        super().__init__(locale, dataset)
        self._class_factory_util = class_factory_util
        self._locale = locale
        self._dataset = dataset

        # Initialize generators
        self._generators = DoctorGenerators(locale, dataset, class_factory_util)

        # Add country code attribute for test compatibility
        self._country_code = self._generators._country_code

        # Initialize field generators
        self._field_generators = EntityUtil.create_field_generator_dict(
            {
                "doctor_id": self._generate_doctor_id,
                "first_name": self._generate_first_name,
                "last_name": self._generate_last_name,
                "specialty": self._generate_specialty,
                "license_number": self._generate_license_number,
                "npi_number": self._generate_npi_number,
                "contact_number": self._generate_contact_number,
                "email": self._generate_email,
                "hospital_affiliation": self._generate_hospital_affiliation,
                "office_address": self._generate_office_address,
                "education": self._generate_education,
                "certifications": self._generate_certifications,
                "languages": self._generate_languages,
                "schedule": self._generate_schedule,
                "accepting_new_patients": self._generate_accepting_new_patients,
            }
        )

        # Cache for entity properties
        self._property_cache = PropertyCache()

    def _generate_doctor_id(self) -> str:
        """Generate a unique doctor ID."""
        return self._generators.generate_doctor_id()

    def _generate_first_name(self) -> str:
        """Generate a first name."""
        return self._generators.generate_first_name()

    def _generate_last_name(self) -> str:
        """Generate a last name."""
        return self._generators.generate_last_name()

    def _generate_specialty(self) -> str:
        """Generate a medical specialty."""
        return self._generators.generate_specialty()

    def _generate_license_number(self) -> str:
        """Generate a medical license number."""
        return self._generators.generate_license_number()

    def _generate_npi_number(self) -> str:
        """Generate a National Provider Identifier (NPI) number."""
        return self._generators.generate_npi_number()

    def _generate_contact_number(self) -> str:
        """Generate a contact number."""
        return self._generators.generate_contact_number()

    def _generate_email(self) -> str:
        """Generate an email address."""
        return self._generators.generate_email(self.first_name, self.last_name)

    def _generate_hospital_affiliation(self) -> str:
        """Generate a hospital affiliation."""
        return self._generators.generate_hospital_affiliation()

    def _generate_office_address(self) -> dict[str, str]:
        """Generate an office address."""
        return self._generators.generate_office_address()

    def _generate_education(self) -> list[dict[str, str]]:
        """Generate education history."""
        return self._generators.generate_education()

    def _generate_certifications(self) -> list[dict[str, str]]:
        """Generate certifications."""
        return self._generators.generate_certifications()

    def _generate_languages(self) -> list[str]:
        """Generate languages spoken."""
        return self._generators.generate_languages()

    def _generate_schedule(self) -> dict[str, list[str]]:
        """Generate a weekly schedule."""
        return self._generators.generate_schedule()

    def _generate_accepting_new_patients(self) -> bool:
        """Generate whether the doctor is accepting new patients."""
        return self._generators.generate_accepting_new_patients()

    def reset(self) -> None:
        """Reset the entity by clearing the property cache."""
        self._property_cache.clear()

        # Re-initialize generators to ensure fresh data
        self._generators = DoctorGenerators(self._locale, self._dataset, self._class_factory_util)
        self._country_code = self._generators._country_code

    @property
    def doctor_id(self) -> str:
        """Get the doctor ID."""
        return self._property_cache.get("doctor_id", self._generate_doctor_id)

    @property
    def first_name(self) -> str:
        """Get the first name."""
        return self._property_cache.get("first_name", self._generate_first_name)

    @property
    def last_name(self) -> str:
        """Get the last name."""
        return self._property_cache.get("last_name", self._generate_last_name)

    @property
    def specialty(self) -> str:
        """Get the specialty."""
        return self._property_cache.get("specialty", self._generate_specialty)

    @property
    def license_number(self) -> str:
        """Get the license number."""
        return self._property_cache.get("license_number", self._generate_license_number)

    @property
    def npi_number(self) -> str:
        """Get the NPI number."""
        return self._property_cache.get("npi_number", self._generate_npi_number)

    @property
    def contact_number(self) -> str:
        """Get the contact number."""
        return self._property_cache.get("contact_number", self._generate_contact_number)

    @property
    def email(self) -> str:
        """Get the email address."""
        return self._property_cache.get("email", self._generate_email)

    @property
    def hospital_affiliation(self) -> str:
        """Get the hospital affiliation."""
        return self._property_cache.get("hospital_affiliation", self._generate_hospital_affiliation)

    @property
    def office_address(self) -> dict[str, str]:
        """Get the office address."""
        return self._property_cache.get("office_address", self._generate_office_address)

    @property
    def education(self) -> list[dict[str, str]]:
        """Get the education history."""
        return self._property_cache.get("education", self._generate_education)

    @property
    def certifications(self) -> list[dict[str, str]]:
        """Get the certifications."""
        return self._property_cache.get("certifications", self._generate_certifications)

    @property
    def languages(self) -> list[str]:
        """Get the languages spoken."""
        return self._property_cache.get("languages", self._generate_languages)

    @property
    def schedule(self) -> dict[str, list[str]]:
        """Get the schedule."""
        return self._property_cache.get("schedule", self._generate_schedule)

    @property
    def accepting_new_patients(self) -> bool:
        """Get whether the doctor is accepting new patients."""
        return self._property_cache.get("accepting_new_patients", self._generate_accepting_new_patients)

    def to_dict(self) -> dict[str, Any]:
        """Convert the entity to a dictionary.

        Returns:
            A dictionary containing all entity properties.
        """
        return {
            "doctor_id": self.doctor_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "specialty": self.specialty,
            "license_number": self.license_number,
            "npi_number": self.npi_number,
            "contact_number": self.contact_number,
            "email": self.email,
            "hospital_affiliation": self.hospital_affiliation,
            "office_address": self.office_address,
            "education": self.education,
            "certifications": self.certifications,
            "languages": self.languages,
            "schedule": self.schedule,
            "accepting_new_patients": self.accepting_new_patients,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of doctor data.

        Args:
            count: The number of records to generate.

        Returns:
            A list of dictionaries containing generated doctor data.
        """
        field_names = [
            "doctor_id",
            "first_name",
            "last_name",
            "specialty",
            "license_number",
            "npi_number",
            "contact_number",
            "email",
            "hospital_affiliation",
            "office_address",
            "education",
            "certifications",
            "languages",
            "schedule",
            "accepting_new_patients",
        ]

        return EntityUtil.batch_generate_fields(self._field_generators, field_names, count)
