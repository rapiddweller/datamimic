# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Doctor entity model.

This module provides the Doctor entity model for generating realistic doctor data.
"""

from typing import Any, ClassVar

from datamimic_ce.core.base_entity import BaseEntity
from datamimic_ce.core.property_cache import PropertyCache
from datamimic_ce.domains.healthcare.data_loaders.doctor_loader import DoctorDataLoader


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
    _DATA_CACHE: ClassVar[dict[str, Any]] = {}

    def __init__(
        self,
        class_factory_util: Any,
        locale: str = "en",
        dataset: str | None = None,
    ):
        """Initialize the Doctor entity.

        Args:
            class_factory_util: The class factory utility.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
        """
        super().__init__(locale, dataset)
        self._class_factory_util = class_factory_util
        self._locale = locale
        self._dataset = dataset
        self._country_code = dataset or "US"

        # Initialize data loader
        self._data_loader = DoctorDataLoader()

        # Initialize person entity for personal information
        self._person_entity = self._class_factory_util.get_person_entity(locale=locale, dataset=dataset)

        # Initialize address entity for address information
        self._address_entity = self._class_factory_util.get_address_entity(locale=locale, dataset=dataset)

        # Initialize field generators
        self._initialize_generators()

    def _initialize_generators(self):
        """Initialize all field generators."""
        # Basic information
        self._doctor_id_generator = PropertyCache(self._generate_doctor_id)
        self._npi_number_generator = PropertyCache(self._generate_npi_number)
        self._license_number_generator = PropertyCache(self._generate_license_number)
        self._specialty_generator = PropertyCache(self._generate_specialty)
        self._hospital_generator = PropertyCache(self._generate_hospital)
        self._medical_school_generator = PropertyCache(self._generate_medical_school)
        self._graduation_year_generator = PropertyCache(self._generate_graduation_year)
        self._years_of_experience_generator = PropertyCache(self._generate_years_of_experience)
        self._certifications_generator = PropertyCache(self._generate_certifications)
        self._languages_generator = PropertyCache(self._generate_languages)
        self._accepting_new_patients_generator = PropertyCache(self._generate_accepting_new_patients)
        self._office_hours_generator = PropertyCache(self._generate_office_hours)
        self._email_generator = PropertyCache(self._generate_email)
        self._phone_generator = PropertyCache(self._generate_phone)

    def reset(self) -> None:
        """Reset all field generators, causing new values to be generated on the next access."""
        self._person_entity.reset()
        self._address_entity.reset()
        self._doctor_id_generator.reset()
        self._npi_number_generator.reset()
        self._license_number_generator.reset()
        self._specialty_generator.reset()
        self._hospital_generator.reset()
        self._medical_school_generator.reset()
        self._graduation_year_generator.reset()
        self._years_of_experience_generator.reset()
        self._certifications_generator.reset()
        self._languages_generator.reset()
        self._accepting_new_patients_generator.reset()
        self._office_hours_generator.reset()
        self._email_generator.reset()
        self._phone_generator.reset()

    def to_dict(self) -> dict[str, Any]:
        """Convert the doctor entity to a dictionary.

        Returns:
            A dictionary containing all doctor properties.
        """
        return {
            "doctor_id": self.doctor_id,
            "npi_number": self.npi_number,
            "license_number": self.license_number,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "gender": self.gender,
            "date_of_birth": self.date_of_birth,
            "age": self.age,
            "specialty": self.specialty,
            "hospital": self.hospital,
            "medical_school": self.medical_school,
            "graduation_year": self.graduation_year,
            "years_of_experience": self.years_of_experience,
            "certifications": self.certifications,
            "languages": self.languages,
            "accepting_new_patients": self.accepting_new_patients,
            "office_hours": self.office_hours,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of doctor entities.

        Args:
            count: The number of doctor entities to generate.

        Returns:
            A list of dictionaries containing the generated doctor entities.
        """
        doctors = []
        for _ in range(count):
            doctors.append(self.to_dict())
            self.reset()
        return doctors

    # Property getters
    @property
    def doctor_id(self) -> str:
        """Get the doctor ID.

        Returns:
            A unique identifier for the doctor.
        """
        return self._doctor_id_generator.get()

    @property
    def npi_number(self) -> str:
        """Get the NPI (National Provider Identifier) number.

        Returns:
            A 10-digit NPI number.
        """
        return self._npi_number_generator.get()

    @property
    def license_number(self) -> str:
        """Get the medical license number.

        Returns:
            A medical license number.
        """
        return self._license_number_generator.get()

    @property
    def first_name(self) -> str:
        """Get the doctor's first name.

        Returns:
            The doctor's first name.
        """
        return self._person_entity.first_name

    @property
    def last_name(self) -> str:
        """Get the doctor's last name.

        Returns:
            The doctor's last name.
        """
        return self._person_entity.last_name

    @property
    def full_name(self) -> str:
        """Get the doctor's full name.

        Returns:
            The doctor's full name.
        """
        return f"{self.first_name} {self.last_name}"

    @property
    def gender(self) -> str:
        """Get the doctor's gender.

        Returns:
            The doctor's gender.
        """
        return self._person_entity.gender

    @property
    def date_of_birth(self) -> str:
        """Get the doctor's date of birth.

        Returns:
            The doctor's date of birth in YYYY-MM-DD format.
        """
        return self._person_entity.date_of_birth

    @property
    def age(self) -> int:
        """Get the doctor's age.

        Returns:
            The doctor's age in years.
        """
        return self._person_entity.age

    @property
    def specialty(self) -> str:
        """Get the doctor's medical specialty.

        Returns:
            The doctor's medical specialty.
        """
        return self._specialty_generator.get()

    @property
    def hospital(self) -> str:
        """Get the hospital where the doctor works.

        Returns:
            The name of the hospital.
        """
        return self._hospital_generator.get()

    @property
    def medical_school(self) -> str:
        """Get the medical school the doctor attended.

        Returns:
            The name of the medical school.
        """
        return self._medical_school_generator.get()

    @property
    def graduation_year(self) -> int:
        """Get the year the doctor graduated from medical school.

        Returns:
            The graduation year.
        """
        return self._graduation_year_generator.get()

    @property
    def years_of_experience(self) -> int:
        """Get the doctor's years of experience.

        Returns:
            The number of years of experience.
        """
        return self._years_of_experience_generator.get()

    @property
    def certifications(self) -> list[str]:
        """Get the doctor's certifications.

        Returns:
            A list of certifications.
        """
        return self._certifications_generator.get()

    @property
    def languages(self) -> list[str]:
        """Get the languages spoken by the doctor.

        Returns:
            A list of languages.
        """
        return self._languages_generator.get()

    @property
    def accepting_new_patients(self) -> bool:
        """Get whether the doctor is accepting new patients.

        Returns:
            True if the doctor is accepting new patients, False otherwise.
        """
        return self._accepting_new_patients_generator.get()

    @property
    def office_hours(self) -> dict[str, str]:
        """Get the doctor's office hours.

        Returns:
            A dictionary mapping days to hours.
        """
        return self._office_hours_generator.get()

    @property
    def email(self) -> str:
        """Get the doctor's email address.

        Returns:
            The doctor's email address.
        """
        return self._email_generator.get()

    @property
    def phone(self) -> str:
        """Get the doctor's phone number.

        Returns:
            The doctor's phone number.
        """
        return self._phone_generator.get()

    @property
    def address(self) -> dict[str, Any]:
        """Get the doctor's address.

        Returns:
            A dictionary containing the doctor's address information.
        """
        return self._address_entity.to_dict()

    # Generator methods
    def _generate_doctor_id(self) -> str:
        """Generate a unique doctor ID.

        Returns:
            A unique doctor ID.
        """
        import uuid

        return f"DOC-{uuid.uuid4().hex[:8].upper()}"

    def _generate_npi_number(self) -> str:
        """Generate an NPI (National Provider Identifier) number.

        Returns:
            A 10-digit NPI number.
        """
        import random

        return "".join(str(random.randint(0, 9)) for _ in range(10))

    def _generate_license_number(self) -> str:
        """Generate a medical license number.

        Returns:
            A medical license number.
        """
        import random
        import string

        prefix = "".join(random.choices(string.ascii_uppercase, k=2))
        number = "".join(random.choices(string.digits, k=6))
        return f"{prefix}-{number}"

    def _generate_specialty(self) -> str:
        """Generate a medical specialty.

        Returns:
            A medical specialty.
        """
        from datamimic_ce.domains.healthcare.generators.doctor_generator import weighted_choice

        specialties = self._data_loader.get_data("specialties", self._country_code)
        return weighted_choice(specialties)

    def _generate_hospital(self) -> str:
        """Generate a hospital name.

        Returns:
            A hospital name.
        """
        from datamimic_ce.domains.healthcare.generators.doctor_generator import weighted_choice

        hospitals = self._data_loader.get_data("hospitals", self._country_code)
        return weighted_choice(hospitals)

    def _generate_medical_school(self) -> str:
        """Generate a medical school name.

        Returns:
            A medical school name.
        """
        from datamimic_ce.domains.healthcare.generators.doctor_generator import weighted_choice

        medical_schools = self._data_loader.get_data("medical_schools", self._country_code)
        return weighted_choice(medical_schools)

    def _generate_graduation_year(self) -> int:
        """Generate a graduation year.

        Returns:
            A graduation year.
        """
        import datetime
        import random

        current_year = datetime.datetime.now().year
        min_age = 30  # Minimum age for a doctor
        max_age = 70  # Maximum age for a doctor
        min_years_after_graduation = 5  # Minimum years after graduation
        max_years_after_graduation = 45  # Maximum years after graduation

        # Calculate graduation year based on age and years after graduation
        age = self.age
        years_after_graduation = random.randint(
            min_years_after_graduation,
            min(max_years_after_graduation, age - 25),  # Assume graduated at 25 at the earliest
        )
        return current_year - years_after_graduation

    def _generate_years_of_experience(self) -> int:
        """Generate years of experience.

        Returns:
            Years of experience.
        """
        import datetime

        current_year = datetime.datetime.now().year
        return current_year - self.graduation_year

    def _generate_certifications(self) -> list[str]:
        """Generate a list of certifications.

        Returns:
            A list of certifications.
        """
        import random

        from datamimic_ce.domains.healthcare.generators.doctor_generator import weighted_choice

        certifications = self._data_loader.get_data("certifications", self._country_code)
        num_certifications = random.randint(1, 3)
        return [weighted_choice(certifications) for _ in range(num_certifications)]

    def _generate_languages(self) -> list[str]:
        """Generate a list of languages spoken.

        Returns:
            A list of languages.
        """
        import random

        from datamimic_ce.domains.healthcare.generators.doctor_generator import weighted_choice

        languages = self._data_loader.get_data("languages", self._country_code)
        num_languages = random.randint(1, 3)
        return [weighted_choice(languages) for _ in range(num_languages)]

    def _generate_accepting_new_patients(self) -> bool:
        """Generate whether the doctor is accepting new patients.

        Returns:
            True if the doctor is accepting new patients, False otherwise.
        """
        import random

        return random.random() < 0.8  # 80% chance of accepting new patients

    def _generate_office_hours(self) -> dict[str, str]:
        """Generate office hours.

        Returns:
            A dictionary mapping days to hours.
        """
        import random

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

    def _generate_email(self) -> str:
        """Generate an email address.

        Returns:
            An email address.
        """
        import random

        domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com"]
        first = self.first_name.lower()
        last = self.last_name.lower()
        domain = random.choice(domains)

        email_formats = [
            f"{first}.{last}@{domain}",
            f"{first[0]}{last}@{domain}",
            f"{first}{last[0]}@{domain}",
            f"{first}_{last}@{domain}",
            f"dr.{last}@{domain}",
        ]

        return random.choice(email_formats)

    def _generate_phone(self) -> str:
        """Generate a phone number.

        Returns:
            A formatted phone number.
        """
        import random

        area_code = random.randint(100, 999)
        prefix = random.randint(100, 999)
        line = random.randint(1000, 9999)
        return f"({area_code}) {prefix}-{line}"
