# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Generator functions for the doctor entity package.
"""

import datetime
import random
from typing import Any

from datamimic_ce.entities.address_entity import AddressEntity
from datamimic_ce.entities.healthcare.doctor_entity.data_loader import DoctorDataLoader
from datamimic_ce.entities.healthcare.doctor_entity.utils import generate_email
from datamimic_ce.entities.person_entity import PersonEntity


class DoctorGenerators:
    """Field generators for doctor entity."""

    def __init__(self, locale: str, dataset: str | None = None, class_factory_util: Any = None):
        """Initialize the generators.

        Args:
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
            class_factory_util: The class factory utility.
        """
        self._locale = locale
        self._dataset = dataset
        self._class_factory_util = class_factory_util

        # Determine country code from dataset or locale
        self._country_code = self._determine_country_code(dataset, locale)

        # Create person entity for personal information generation
        self._person_entity = PersonEntity(class_factory_util, locale=locale, dataset=dataset)

        # Create address entity for address generation
        self._address_entity = AddressEntity(class_factory_util, dataset=dataset, locale=locale)

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

    def generate_doctor_id(self) -> str:
        """Generate a unique doctor ID."""
        return f"DR-{random.randint(10000000, 99999999)}"

    def generate_first_name(self) -> str:
        """Generate a first name using PersonEntity."""
        return self._person_entity.given_name

    def generate_last_name(self) -> str:
        """Generate a last name using PersonEntity."""
        return self._person_entity.family_name

    def generate_specialty(self) -> str:
        """Generate a medical specialty."""
        specialties = DoctorDataLoader.get_country_specific_data("specialties", self._country_code)

        if not specialties:
            # Fallback to default specialty if no specialties are available
            return "Family Medicine"

        # Choose a specialty based on weights
        specialty_values = [s[0] for s in specialties]
        specialty_weights = [s[1] for s in specialties]
        return random.choices(specialty_values, weights=specialty_weights, k=1)[0]

    def generate_license_number(self) -> str:
        """Generate a medical license number."""
        # Format: 2 letters followed by dash and 6 digits (e.g., "CA-123456")
        letters = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
        digits = "".join(random.choices("0123456789", k=6))
        return f"{letters}-{digits}"

    def generate_npi_number(self) -> str:
        """Generate a National Provider Identifier (NPI) number."""
        # NPI is a 10-digit number
        return f"{random.randint(1000000000, 9999999999)}"

    def generate_contact_number(self) -> str:
        """Generate a contact number."""
        # Generate a US-formatted phone number in the format (XXX) XXX-XXXX
        area_code = random.randint(100, 999)
        prefix = random.randint(100, 999)
        line_number = random.randint(1000, 9999)
        return f"({area_code}) {prefix}-{line_number}"

    def generate_email(self, first_name: str, last_name: str) -> str:
        """Generate an email address.

        Args:
            first_name: The doctor's first name
            last_name: The doctor's last name

        Returns:
            An email address
        """
        # Use the person entity's email if it has one
        if hasattr(self._person_entity, "email") and self._person_entity.email:
            return self._person_entity.email

        # Fallback to generating our own
        return generate_email(first_name, last_name)

    def generate_hospital_affiliation(self) -> str:
        """Generate a hospital affiliation."""
        hospitals = DoctorDataLoader.get_country_specific_data("hospitals", self._country_code)

        if not hospitals:
            # Fallback to default hospital if no hospitals are available
            return "General Hospital"

        # Choose a hospital based on weights
        hospital_values = [h[0] for h in hospitals]
        hospital_weights = [h[1] for h in hospitals]
        return random.choices(hospital_values, weights=hospital_weights, k=1)[0]

    def generate_office_address(self) -> dict[str, str]:
        """Generate an office address using AddressEntity."""
        return {
            "street": f"{self._address_entity.street} {self._address_entity.house_number}",
            "city": self._address_entity.city,
            "state": self._address_entity.state,
            "zip_code": self._address_entity.postal_code,
            "country": self._address_entity.country,
        }

    def generate_education(self) -> list[dict[str, str]]:
        """Generate education history."""
        # Get medical institutions and degrees from data cache
        institutions = DoctorDataLoader.get_country_specific_data("institutions", self._country_code)
        degrees = DoctorDataLoader.get_country_specific_data("degrees", self._country_code)

        # Extract just the values, not the weights
        institution_values = [i[0] for i in institutions] if institutions else []
        degree_values = [d[0] for d in degrees] if degrees else []

        if not institution_values:
            # Fallback to default institutions if none are available
            institution_values = ["Medical University", "State University Medical School", "National Medical College"]

        if not degree_values:
            # Fallback to default degrees if none are available
            degree_values = ["MD", "DO", "MBBS", "PhD"]

        # Generate 1-3 education entries
        education_count = random.randint(1, 3)
        education = []

        # Starting with medical school (typically completed around age 26)
        base_year = datetime.datetime.now().year - random.randint(1, 40)

        for i in range(education_count):
            degree = random.choice(degree_values)
            institution = random.choice(institution_values)

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

    def generate_certifications(self) -> list[dict[str, str]]:
        """Generate certifications."""
        certifications_data = DoctorDataLoader.get_country_specific_data("certifications", self._country_code)

        # Extract just the values, not the weights
        certification_values = [c[0] for c in certifications_data] if certifications_data else []

        if not certification_values:
            # Fallback to default certifications if none are available
            certification_values = [
                "Board Certified in Internal Medicine",
                "Board Certified in Family Medicine",
                "Advanced Cardiac Life Support (ACLS)",
                "Basic Life Support (BLS)",
                "Pediatric Advanced Life Support (PALS)",
            ]

        # Determine how many certifications to generate (1-3)
        num_certifications = random.randint(1, 3)

        # If we have fewer certifications than requested, use all of them
        if len(certification_values) <= num_certifications:
            selected_certifications = certification_values
        else:
            selected_certifications = random.sample(certification_values, num_certifications)

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

    def generate_languages(self) -> list[str]:
        """Generate languages spoken."""
        # Start with the person entity's language if it has one
        languages = []
        if hasattr(self._person_entity, "language") and self._person_entity.language:
            languages.append(self._person_entity.language)

        # Get additional languages from data cache
        available_languages = DoctorDataLoader.get_country_specific_data("languages", self._country_code)

        # Extract just the values, not the weights
        language_values = [l[0] for l in available_languages] if available_languages else []

        if not language_values:
            # Fallback to default languages if none are available
            language_values = ["English", "Spanish", "French", "German", "Mandarin"]

        # Add 0-2 more languages from the available list
        additional_languages_count = random.randint(0, 2)

        if additional_languages_count > 0:
            # Filter out already selected languages
            remaining_languages = [lang for lang in language_values if lang not in languages]

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

    def generate_schedule(self) -> dict[str, list[str]]:
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

    def generate_accepting_new_patients(self) -> bool:
        """Generate whether the doctor is accepting new patients."""
        return random.random() < 0.75  # 75% chance of accepting new patients
