# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
This module serves as a compatibility layer for the DoctorEntity class.
It imports the actual implementation from the doctor_entity package.
"""

import datetime
import random
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar, cast

from datamimic_ce.entities.address_entity import AddressEntity
from datamimic_ce.entities.entity_util import EntityUtil

# Import the actual implementation from the package
from datamimic_ce.entities.healthcare.doctor_entity.core import DoctorEntity as DoctorEntityImpl
from datamimic_ce.entities.healthcare.doctor_entity.data_loader import DoctorDataLoader
from datamimic_ce.entities.healthcare.doctor_entity.utils import parse_weighted_value, weighted_choice
from datamimic_ce.entities.person_entity import PersonEntity
from datamimic_ce.logger import logger

T = TypeVar("T")


# For backward compatibility
class DoctorEntity(DoctorEntityImpl):
    """Generate doctor data.

    This class generates realistic doctor data including doctor IDs,
    names, specialties, license numbers, contact information, education,
    certifications, and schedules.

    This is a compatibility wrapper around the actual implementation in the doctor_entity package.
    """

    # Module-level cache for data to reduce file I/O (for backward compatibility)
    _DATA_CACHE: dict[str, list[str]] = {}
    # Module-level cache for dictionary data (for backward compatibility)
    _DICT_CACHE: dict[str, dict[str, str]] = {}

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
        self._data_generation_util = class_factory_util.get_data_generation_util()

        # Determine country code from dataset or locale
        self._country_code = self._determine_country_code(dataset, locale)

        # Create person entity for personal information generation
        self._person_entity = PersonEntity(class_factory_util, locale=locale, dataset=dataset)

        # Create address entity for address generation
        self._address_entity = AddressEntity(class_factory_util, dataset=dataset, locale=locale)

        # Load data from CSV files
        self._load_data(self._country_code)

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
        self._property_cache: dict[str, Any] = {}

    def _determine_country_code(self, dataset: str | None, locale: str) -> str:
        """Determine the country code to use based on dataset and locale.

        Args:
            dataset: The dataset parameter.
            locale: The locale parameter.

        Returns:
            A two-letter country code.
        """
        # If dataset is provided, prioritize it
        if dataset and len(dataset) == 2:
            return dataset.upper()

        # Try to extract country code from locale
        if locale:
            # Check for formats like "en_US" or "de-DE"
            if "_" in locale and len(locale.split("_")) > 1:
                country_part = locale.split("_")[1]
                if len(country_part) == 2:
                    return country_part.upper()
            elif "-" in locale and len(locale.split("-")) > 1:
                country_part = locale.split("-")[1]
                if len(country_part) == 2:
                    return country_part.upper()

            # Direct matching for 2-letter codes
            if len(locale) == 2:
                return locale.upper()

            # Map common language codes to countries
            language_code = locale.split("_")[0].split("-")[0].lower()
            language_map = {
                "en": "US",
                "de": "DE",
                "fr": "FR",
                "es": "ES",
                "it": "IT",
                "pt": "BR",
                "ru": "RU",
                "zh": "CN",
                "ja": "JP",
            }
            if language_code in language_map:
                return language_map[language_code]

        # Default to US if no matching country code is found
        return "US"

    @classmethod
    def _load_data(cls, country_code: str = "US") -> None:
        """Load data from CSV files.

        Args:
            country_code: The country code to load data for. Default is US.
        """
        if not cls._DATA_CACHE:
            # Set the data directory to the path where the medical data files are stored
            current_file = Path(__file__)
            data_dir = current_file.parent.parent / "data" / "medical"

            # Define categories of data to load with headers
            header_categories = {}

            # Define categories of data to load without headers (simple lists)
            simple_categories = {
                "specialties": "specialties",
                "degrees": "degrees",
                "institutions": "institutions",
                "certifications": "certifications",
                "languages": "languages",
                "hospitals": "hospitals",
            }

            # Load each category of simple data
            for cache_key, file_prefix in simple_categories.items():
                # Try country-specific file first
                country_specific_path = data_dir / f"{file_prefix}_{country_code}.csv"
                if country_specific_path.exists():
                    cls._DATA_CACHE[cache_key] = cls._load_simple_csv(country_specific_path)
                    continue

                # Try US as fallback
                fallback_path = data_dir / f"{file_prefix}_US.csv"
                if fallback_path.exists():
                    logger.info(f"Using US fallback for {file_prefix} data as {country_code} not available")
                    cls._DATA_CACHE[cache_key] = cls._load_simple_csv(fallback_path)
                    continue

                # Last resort - try without country code
                generic_path = data_dir / f"{file_prefix}.csv"
                if generic_path.exists():
                    logger.warning(f"Using generic data for {file_prefix} - consider creating country-specific file")
                    cls._DATA_CACHE[cache_key] = cls._load_simple_csv(generic_path)

    @staticmethod
    def _load_simple_csv(file_path: Path) -> list[str]:
        """Load a simple CSV file and return a list of values.

        This is a compatibility method that delegates to DoctorDataLoader.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of values from the CSV file
        """
        # Call the actual implementation but convert the result to the expected format
        result = DoctorDataLoader._load_simple_csv(file_path)
        # Convert list of tuples to list of strings for backward compatibility
        return [f"{value},{weight}" if weight != 1.0 else value for value, weight in result]

    @classmethod
    def _get_country_specific_data(cls, data_type: str, country_code: str = "US") -> list[str]:
        """Get country-specific data from CSV files.

        This is a compatibility method that delegates to DoctorDataLoader.

        Args:
            data_type: Type of data to retrieve (e.g., "specialties", "hospitals")
            country_code: Country code (default: "US")

        Returns:
            List of values from the CSV file
        """
        result = DoctorDataLoader.get_country_specific_data(data_type, country_code)
        return [item[0] for item in result]  # Extract just the values, not the weights

    @staticmethod
    def _weighted_choice(values: list[str]) -> str:
        """Choose a value from a list based on weights.

        This is a compatibility method that delegates to weighted_choice.

        Args:
            values: List of values, potentially with weights

        Returns:
            A chosen value
        """
        return weighted_choice(values)

    @staticmethod
    def _parse_weighted_value(value: str) -> tuple[str, float]:
        """Parse a weighted value from a CSV file.

        This is a compatibility method that delegates to parse_weighted_value.

        Args:
            value: The value to parse

        Returns:
            A tuple of (value, weight)
        """
        return parse_weighted_value(value)

    def _get_cached_property(self, property_name: str, generator_func: Callable[[], T]) -> T:
        """Get a cached property or generate and cache it if not present.

        Args:
            property_name: The name of the property to get.
            generator_func: The function to generate the property value.

        Returns:
            The cached or newly generated property value.
        """
        if property_name not in self._property_cache:
            self._property_cache[property_name] = generator_func()
        return cast(T, self._property_cache[property_name])

    def _generate_doctor_id(self) -> str:
        """Generate a unique doctor ID."""
        return f"DR-{random.randint(10000000, 99999999)}"

    def _generate_first_name(self) -> str:
        """Generate a first name using PersonEntity."""
        return self._person_entity.given_name

    def _generate_last_name(self) -> str:
        """Generate a last name using PersonEntity."""
        return self._person_entity.family_name

    def _generate_specialty(self) -> str:
        """Generate a medical specialty."""
        specialties = self._DATA_CACHE.get("specialties", [])
        if not specialties:
            logger.warning("No specialties found in data cache, using default value")
            return "Family Medicine"
        return random.choice(specialties)

    def _generate_license_number(self) -> str:
        """Generate a medical license number."""
        # Format varies by state, but most use a combination of letters and numbers
        state_code = self._address_entity.state_abbr if hasattr(self._address_entity, "state_abbr") else "XX"
        return f"{state_code}-{random.randint(100000, 999999)}"

    def _generate_npi_number(self) -> str:
        """Generate a National Provider Identifier (NPI) number."""
        # NPI is a 10-digit number
        return f"{random.randint(1000000000, 9999999999)}"

    def _generate_contact_number(self) -> str:
        """Generate a contact number."""
        # Use the person entity's phone number if it has one
        if hasattr(self._person_entity, "phone") and self._person_entity.phone:
            return self._person_entity.phone

        # Fallback to the address entity's phone number
        if hasattr(self._address_entity, "office_phone") and self._address_entity.office_phone:
            return self._address_entity.office_phone

        # Last resort fallback
        area_code = random.randint(100, 999)
        prefix = random.randint(100, 999)
        line_number = random.randint(1000, 9999)
        return f"({area_code}) {prefix}-{line_number}"

    def _generate_email(self) -> str:
        """Generate an email address."""
        # Use the person entity's email if it has one
        if hasattr(self._person_entity, "email") and self._person_entity.email:
            return self._person_entity.email

        # Fallback to generating our own
        first_name = self.first_name.lower().replace(" ", "")
        last_name = self.last_name.lower().replace(" ", "")

        # Professional emails often use full names
        domains = ["hospital.org", "medical.com", "healthcare.org", "clinic.com", "medcenter.org"]
        domain = random.choice(domains)

        formats = [
            f"{first_name}.{last_name}@{domain}",
            f"{first_name[0]}.{last_name}@{domain}",
            f"{last_name}.{first_name[0]}@{domain}",
        ]

        return random.choice(formats)

    def _generate_hospital_affiliation(self) -> str:
        """Generate a hospital affiliation."""
        hospitals = self._DATA_CACHE.get("hospitals", [])
        if not hospitals:
            logger.warning("No hospitals found in data cache, using default value")
            return "General Hospital"
        return random.choice(hospitals)

    def _generate_office_address(self) -> dict[str, str]:
        """Generate an office address using AddressEntity."""
        return {
            "street": f"{self._address_entity.street} {self._address_entity.house_number}",
            "city": self._address_entity.city,
            "state": self._address_entity.state,
            "zip_code": self._address_entity.postal_code,
            "country": self._address_entity.country,
        }

    def _generate_education(self) -> list[dict[str, str]]:
        """Generate education history."""
        # Get medical institutions and degrees from data cache
        institutions = self._DATA_CACHE.get("institutions", [])
        degrees = self._DATA_CACHE.get("degrees", [])

        if not institutions:
            logger.warning("No institutions found in data cache, using default values")
            institutions = ["Medical University", "State University Medical School", "National Medical College"]

        if not degrees:
            logger.warning("No degrees found in data cache, using default values")
            degrees = ["MD", "DO", "MBBS", "PhD"]

        # Generate 1-3 education entries
        education_count = random.randint(1, 3)
        education = []

        # Starting with medical school (typically completed around age 26)
        base_year = datetime.datetime.now().year - random.randint(1, 40)

        for i in range(education_count):
            degree = random.choice(degrees)
            institution = random.choice(institutions)

            # Calculate graduation year (medical school, then residency, etc.)
            grad_year = base_year - (education_count - i - 1) * 2 - random.randint(0, 3)

            education.append(
                {
                    "institution": institution,
                    "degree": degree,
                    "year": str(grad_year),
                    "honors": random.choice(["", "Cum Laude", "Magna Cum Laude", "Summa Cum Laude"])
                    if random.random() < 0.3
                    else "",
                }
            )

        return education

    def _generate_certifications(self) -> list[dict[str, str]]:
        """Generate certifications."""
        certifications_data = self._DATA_CACHE.get("certifications", [])

        if not certifications_data:
            logger.warning("No certifications found in data cache, using default values")
            certifications_data = [
                "Board Certified in Internal Medicine",
                "Board Certified in Family Medicine",
                "Advanced Cardiac Life Support (ACLS)",
                "Basic Life Support (BLS)",
                "Pediatric Advanced Life Support (PALS)",
            ]

        # Determine how many certifications to generate (1-3)
        num_certifications = random.randint(1, 3)

        # If we have fewer certifications than requested, use all of them
        if len(certifications_data) <= num_certifications:
            selected_certifications = certifications_data
        else:
            selected_certifications = random.sample(certifications_data, num_certifications)

        # Generate certification details
        now = datetime.datetime.now()
        certifications = []

        for cert in selected_certifications:
            # Certification issued 1-15 years ago
            years_ago = random.randint(1, 15)
            issue_date = now - datetime.timedelta(days=365 * years_ago)

            # Certifications typically valid for 5-10 years
            validity_years = random.randint(5, 10)
            expiry_date = issue_date + datetime.timedelta(days=365 * validity_years)

            # Only add if still valid or expired within last 2 years
            if expiry_date > now - datetime.timedelta(days=365 * 2):
                certifications.append(
                    {
                        "name": cert,
                        "issue_date": issue_date.strftime("%Y-%m-%d"),
                        "expiry_date": expiry_date.strftime("%Y-%m-%d"),
                    }
                )

        return certifications

    def _generate_languages(self) -> list[str]:
        """Generate languages spoken."""
        # Start with the person entity's language if it has one
        languages = []
        if hasattr(self._person_entity, "language") and self._person_entity.language:
            languages.append(self._person_entity.language)

        # Get additional languages from data cache
        available_languages = self._DATA_CACHE.get("languages", [])

        if not available_languages:
            logger.warning("No languages found in data cache, using default values")
            available_languages = ["English", "Spanish", "French", "German", "Mandarin"]

        # Add 0-2 more languages from the available list
        additional_languages_count = random.randint(0, 2)

        if additional_languages_count > 0:
            # Filter out already selected languages
            remaining_languages = [lang for lang in available_languages if lang not in languages]

            if remaining_languages:
                # Add unique random languages
                for _ in range(min(additional_languages_count, len(remaining_languages))):
                    language = random.choice(remaining_languages)
                    languages.append(language)
                    remaining_languages.remove(language)

        # Ensure we have at least one language
        if not languages:
            languages.append("English")  # Default to English if no languages are available

        return languages

    def _generate_schedule(self) -> dict[str, list[str]]:
        """Generate a weekly schedule."""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        hours = ["9:00 AM - 5:00 PM", "8:00 AM - 4:00 PM", "10:00 AM - 6:00 PM", "7:00 AM - 3:00 PM", "Not Available"]

        # Most doctors work 4-5 weekdays
        workdays = random.randint(4, 5)
        working_days = random.sample(days[:5], workdays)  # Weekdays

        # Some doctors work weekends (1 in 3 chance)
        if random.random() < 0.3:
            # Add Saturday or Sunday with reduced hours
            weekend_day = random.choice(days[5:])
            working_days.append(weekend_day)

        # Generate the schedule
        schedule = {}
        for day in days:
            if day in working_days:
                # Choose reasonable hours for this day
                if day in ["Saturday", "Sunday"]:
                    # Weekend hours are typically shorter
                    schedule[day] = ["9:00 AM - 1:00 PM"]
                else:
                    schedule[day] = [random.choice(hours[:4])]  # Only use available hours for weekdays
            else:
                schedule[day] = ["Not Available"]

        return schedule

    def _generate_accepting_new_patients(self) -> bool:
        """Generate whether the doctor is accepting new patients."""
        return random.random() < 0.75  # 75% chance of accepting new patients

    def reset(self) -> None:
        """Reset all field generators and caches."""
        for generator in self._field_generators.values():
            generator.reset()

        # Reset person and address entities
        self._person_entity.reset()
        self._address_entity.reset()

        # Clear property cache
        self._property_cache.clear()

    @property
    def doctor_id(self) -> str:
        """Get the doctor ID."""
        return self._get_cached_property("doctor_id", lambda: self._field_generators["doctor_id"].get())

    @property
    def first_name(self) -> str:
        """Get the first name."""
        return self._get_cached_property("first_name", lambda: self._field_generators["first_name"].get())

    @property
    def last_name(self) -> str:
        """Get the last name."""
        return self._get_cached_property("last_name", lambda: self._field_generators["last_name"].get())

    @property
    def specialty(self) -> str:
        """Get the specialty."""
        value = super().specialty
        if not value:
            # Force regeneration by clearing the cache for this property
            self._property_cache.clear()
            return super().specialty
        return value

    @property
    def license_number(self) -> str:
        """Get the license number."""
        value = super().license_number
        if not value:
            # Force regeneration by clearing the cache for this property
            self._property_cache.clear()
            return super().license_number
        return value

    @property
    def npi_number(self) -> str:
        """Get the NPI number."""
        return self._get_cached_property("npi_number", lambda: self._field_generators["npi_number"].get())

    @property
    def contact_number(self) -> str:
        """Get the contact number."""
        value = super().contact_number
        if not value:
            # Force regeneration by clearing the cache for this property
            self._property_cache.clear()
            return super().contact_number
        return value

    @property
    def email(self) -> str:
        """Get the email address."""
        return self._get_cached_property("email", lambda: self._field_generators["email"].get())

    @property
    def hospital_affiliation(self) -> str:
        """Get the hospital affiliation."""
        value = super().hospital_affiliation
        if not value:
            # Force regeneration by clearing the cache for this property
            self._property_cache.clear()
            return super().hospital_affiliation
        return value

    @property
    def office_address(self) -> dict[str, str]:
        """Get the office address."""
        return self._get_cached_property("office_address", lambda: self._field_generators["office_address"].get())

    @property
    def education(self) -> list[dict[str, str]]:
        """Get the education history."""
        return self._get_cached_property("education", lambda: self._field_generators["education"].get())

    @property
    def certifications(self) -> list[dict[str, str]]:
        """Get the certifications."""
        return self._get_cached_property("certifications", lambda: self._field_generators["certifications"].get())

    @property
    def languages(self) -> list[str]:
        """Get the languages spoken."""
        return self._get_cached_property("languages", lambda: self._field_generators["languages"].get())

    @property
    def schedule(self) -> dict[str, list[str]]:
        """Get the schedule."""
        return self._get_cached_property("schedule", lambda: self._field_generators["schedule"].get())

    @property
    def accepting_new_patients(self) -> bool:
        """Get whether the doctor is accepting new patients."""
        return self._get_cached_property(
            "accepting_new_patients", lambda: self._field_generators["accepting_new_patients"].get()
        )

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
