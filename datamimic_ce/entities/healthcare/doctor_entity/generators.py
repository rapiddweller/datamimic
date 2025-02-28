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
import re
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
        # Convert None to empty string for dataset to satisfy type checker
        address_dataset = dataset if dataset is not None else ""
        self._address_entity = AddressEntity(class_factory_util, dataset=address_dataset, locale=locale)

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
            return dataset.lower()  # Ensure lowercase for consistency

        # Try to extract country code from locale
        if locale:
            # Check for formats like "en_US" or "de-DE"
            if "_" in locale and len(locale.split("_")) > 1:
                country_part = locale.split("_")[1]
                if len(country_part) == 2:
                    return country_part.lower()
            elif "-" in locale and len(locale.split("-")) > 1:
                country_part = locale.split("-")[1]
                if len(country_part) == 2:
                    return country_part.lower()

            # Direct matching for 2-letter codes
            if len(locale) == 2:
                return locale.lower()

            # Map common language codes to countries
            language_code = locale.split("_")[0].split("-")[0].lower()
            language_map = {
                "en": "us",
                "de": "de",
                "fr": "fr",
                "es": "es",
                "it": "it",
                "pt": "br",
                "ru": "ru",
                "zh": "cn",
                "ja": "jp",
            }
            if language_code in language_map:
                return language_map[language_code]

        # Default to US if no matching country code is found
        return "us"

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
            # Create a new person entity to get a random occupation as fallback
            fallback_person = PersonEntity(self._class_factory_util, locale=self._locale, dataset=self._dataset)
            occupation = fallback_person.occupation

            # If occupation is empty, use a generic medical specialty
            if not occupation:
                return "General Medicine"

            return f"Medical {occupation}"

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
        # Use the person entity's phone if it has one and it matches the expected format
        if hasattr(self._person_entity, "phone") and self._person_entity.phone:
            # Check if it already matches the expected format
            if re.match(r"\(\d{3}\) \d{3}-\d{4}", self._person_entity.phone):
                return self._person_entity.phone

            # Try to extract digits and reformat
            digits = re.sub(r"\D", "", self._person_entity.phone)
            if len(digits) >= 10:
                # Use the last 10 digits
                last_10 = digits[-10:]
                return f"({last_10[:3]}) {last_10[3:6]}-{last_10[6:]}"

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
            # Create a new address entity to get a random location name as fallback
            # Convert None to empty string for dataset to satisfy type checker
            address_dataset = self._dataset if self._dataset is not None else ""
            fallback_address = AddressEntity(self._class_factory_util, dataset=address_dataset, locale=self._locale)
            city = fallback_address.city

            # If city is empty, use a generic hospital name
            if not city:
                return "Regional Medical Center"

            return f"{city} Medical Center"

        # Choose a hospital based on weights
        hospital_values = [h[0] for h in hospitals]
        hospital_weights = [h[1] for h in hospitals]
        return random.choices(hospital_values, weights=hospital_weights, k=1)[0]

    def generate_office_address(self) -> dict[str, str]:
        """Generate an office address using AddressEntity."""
        # Create a new address entity to ensure we get a fresh address
        # Convert None to empty string for dataset to satisfy type checker
        address_dataset = self._dataset if self._dataset is not None else ""
        office_address = AddressEntity(self._class_factory_util, dataset=address_dataset, locale=self._locale)

        return {
            "street": f"{office_address.street} {office_address.house_number}",
            "city": office_address.city,
            "state": office_address.state,
            "zip_code": office_address.postal_code,
            "country": office_address.country,
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
            # Create multiple person entities to get university names as fallback
            fallback_institutions = []
            for _ in range(3):
                person = PersonEntity(self._class_factory_util, locale=self._locale, dataset=self._dataset)
                if person.university and person.university not in fallback_institutions:
                    fallback_institutions.append(person.university)

            # If we couldn't get any universities, use generic names
            if not fallback_institutions:
                fallback_institutions = ["University Medical School"]

            institution_values = fallback_institutions

        if not degree_values:
            # Create multiple person entities to get academic degrees as fallback
            fallback_degrees = []
            for _ in range(3):
                person = PersonEntity(self._class_factory_util, locale=self._locale, dataset=self._dataset)
                if person.academic_degree and person.academic_degree not in fallback_degrees:
                    fallback_degrees.append(person.academic_degree)

            # If we couldn't get any degrees, use generic medical degrees
            if not fallback_degrees:
                fallback_degrees = ["MD"]

            degree_values = fallback_degrees

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

            # Get honors from a person entity if available
            honors = ""
            if random.random() < 0.3:
                person = PersonEntity(self._class_factory_util, locale=self._locale, dataset=self._dataset)
                if hasattr(person, "academic_title") and person.academic_title:
                    honors = person.academic_title
                else:
                    honors_options = [
                        "Cum Laude",
                        "Magna Cum Laude",
                        "Summa Cum Laude",
                        "With Honors",
                        "With Distinction",
                    ]
                    honors = random.choice(honors_options)

            education.append(
                {
                    "institution": institution,
                    "degree": degree,
                    "year": str(grad_year),
                    "honors": honors,
                }
            )

        return education

    def generate_certifications(self) -> list[dict[str, str]]:
        """Generate certifications."""
        certifications_data = DoctorDataLoader.get_country_specific_data("certifications", self._country_code)

        # Extract just the values, not the weights
        certification_values = [c[0] for c in certifications_data] if certifications_data else []

        if not certification_values:
            # Use specialty to generate a relevant certification as fallback
            specialty = self.generate_specialty()
            certification_values = [f"Board Certified in {specialty}"]

            # Add some generic medical certifications
            generic_certifications = [
                "Advanced Life Support",
                "Basic Life Support",
                "Medical Ethics Certification",
                "Clinical Research Certification",
            ]
            certification_values.extend(generic_certifications)

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
            # Create multiple person entities to get languages as fallback
            fallback_languages = []
            for _ in range(5):
                person = PersonEntity(self._class_factory_util, locale=self._locale, dataset=self._dataset)
                if person.language and person.language not in fallback_languages and person.language not in languages:
                    fallback_languages.append(person.language)

            language_values = fallback_languages

        # Add 0-2 more languages from the available list
        additional_languages_count = random.randint(0, 2)

        if additional_languages_count > 0 and language_values:
            # Filter out already selected languages
            remaining_languages = [lang for lang in language_values if lang not in languages]

            if remaining_languages:
                # Add unique random languages
                for _ in range(min(additional_languages_count, len(remaining_languages))):
                    language = random.choice(remaining_languages)
                    languages.append(language)
                    remaining_languages.remove(language)

        # Ensure we have at least one language based on locale/country code
        if not languages:
            if self._country_code == "de":
                languages.append("German")
            elif self._country_code == "fr":
                languages.append("French")
            elif self._country_code == "es":
                languages.append("Spanish")
            elif self._country_code == "it":
                languages.append("Italian")
            else:
                languages.append("English")

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
