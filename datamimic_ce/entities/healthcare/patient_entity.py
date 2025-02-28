# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import csv
import random
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, TypeVar, cast

from datamimic_ce.entities.address_entity import AddressEntity
from datamimic_ce.entities.entity import Entity
from datamimic_ce.entities.entity_util import EntityUtil
from datamimic_ce.entities.person_entity import PersonEntity
from datamimic_ce.logger import logger

T = TypeVar("T")


class PatientEntity(Entity):
    """Generate patient data.

    This class generates realistic patient data including patient IDs,
    names, dates of birth, gender, blood type, contact information,
    medical history, allergies, and medications.

    It uses PersonEntity for generating personal information and
    AddressEntity for generating address information.

    Data is loaded from country-specific CSV files when available,
    falling back to generic data files if needed.
    """

    # Module-level cache for data to reduce file I/O
    _DATA_CACHE: dict[str, list[Any]] = {}

    def __init__(
        self,
        class_factory_util: Any,
        locale: str = "en",
        dataset: str | None = None,
    ):
        """Initialize the PatientEntity.

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

        # Create person entity for name generation
        self._person_entity = PersonEntity(class_factory_util, locale=locale, dataset=dataset)

        # Create address entity for address generation
        self._address_entity = AddressEntity(class_factory_util, dataset=dataset, locale=locale)

        # Load data from CSV files
        self._load_data(self._country_code)

        # Initialize field generators
        self._field_generators = EntityUtil.create_field_generator_dict(
            {
                "patient_id": self._generate_patient_id,
                "first_name": self._generate_first_name,
                "last_name": self._generate_last_name,
                "date_of_birth": self._generate_date_of_birth,
                "gender": self._generate_gender,
                "blood_type": self._generate_blood_type,
                "contact_number": self._generate_contact_number,
                "email": self._generate_email,
                "address": self._generate_address,
                "insurance_provider": self._generate_insurance_provider,
                "insurance_policy_number": self._generate_insurance_policy_number,
                "emergency_contact": self._generate_emergency_contact,
                "medical_history": self._generate_medical_history,
                "allergies": self._generate_allergies,
                "medications": self._generate_medications,
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
            header_categories = {
                "medical_conditions": "medical_conditions",
                "allergies": "allergies",
                "medications": "medications",
            }

            # Define categories of data to load without headers (simple lists)
            simple_categories = {
                "genders": "genders",
                "blood_types": "blood_types",
                "insurance_providers": "insurance_providers",
                "emergency_relationships": "emergency_relationships",
                "statuses": "statuses",
            }

            # Load each category of data with headers
            for cache_key, file_prefix in header_categories.items():
                # Try country-specific file first if country_code is available
                country_specific_path = data_dir / f"{file_prefix}_{country_code}.csv"
                if country_specific_path.exists():
                    cls._DATA_CACHE[cache_key] = cls._load_csv_with_header(country_specific_path)
                    continue

                # Try US as fallback
                fallback_path = data_dir / f"{file_prefix}_US.csv"
                if fallback_path.exists():
                    logger.info(f"Using US fallback for {file_prefix} data as {country_code} not available")
                    cls._DATA_CACHE[cache_key] = cls._load_csv_with_header(fallback_path)
                    continue

                # Last resort - try without country code
                generic_path = data_dir / f"{file_prefix}.csv"
                if generic_path.exists():
                    logger.warning(f"Using generic data for {file_prefix} - consider creating country-specific file")
                    cls._DATA_CACHE[cache_key] = cls._load_csv_with_header(generic_path)

            # Load each category of simple data
            for cache_key, file_prefix in simple_categories.items():
                # Try country-specific file first if country_code is available
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
    def _load_csv_with_header(file_path: Path) -> list[dict[str, str]]:
        """Load a CSV file with header into a list of dictionaries.

        Args:
            file_path: Path to the CSV file.

        Returns:
            List of dictionaries with column names as keys.
        """
        if not file_path.exists():
            return []

        try:
            with open(file_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            logger.error(f"Error loading CSV file {file_path}: {e}")
            return []

    @staticmethod
    def _load_simple_csv(file_path: Path) -> list[str]:
        """Load a simple CSV file with one value per line.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of values from the CSV file, with weighted values repeated according to their weight
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                result = []
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    # Check if the line contains a comma (indicating a weighted value)
                    if "," in line:
                        # Split the line into value and weight
                        parts = line.split(",", 1)
                        if len(parts) == 2:
                            value = parts[0].strip()
                            try:
                                # Try to convert the weight to an integer
                                weight = int(parts[1].strip())
                                # Add the value to the result list 'weight' times
                                result.extend([value] * weight)
                                continue
                            except ValueError:
                                # If weight is not an integer, treat the whole line as a single value
                                pass

                    # If no comma or invalid weight, add the line as a single value
                    result.append(line)

                return result
        except Exception as e:
            logger.error(f"Error loading simple CSV file {file_path}: {e}")
            return []

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

    def _generate_patient_id(self) -> str:
        """Generate a unique patient ID."""
        return f"P-{random.randint(10000000, 99999999)}"

    def _generate_first_name(self) -> str:
        """Generate a first name using PersonEntity."""
        return self._person_entity.given_name

    def _generate_last_name(self) -> str:
        """Generate a last name using PersonEntity."""
        return self._person_entity.family_name

    def _generate_date_of_birth(self) -> str:
        """Generate a date of birth."""
        # Use the person entity's birthdate if it has one
        if hasattr(self._person_entity, "birthdate"):
            return self._person_entity.birthdate.strftime("%Y-%m-%d")

        # Fallback to a random date
        days_ago = random.randint(365, 36500)  # 1 to 100 years
        birth_date = datetime.now() - timedelta(days=days_ago)
        return birth_date.strftime("%Y-%m-%d")

    def _generate_gender(self) -> str:
        """Generate a gender."""
        # Use the person entity's gender if possible
        if hasattr(self._person_entity, "gender"):
            person_gender = self._person_entity.gender
            # Map mimesis genders to our format
            gender_mapping = {"female": "Female", "male": "Male", "other": "Other"}
            if person_gender in gender_mapping:
                return gender_mapping[person_gender]

        # Fallback to our cached data
        genders = self._DATA_CACHE.get("genders", ["Male", "Female", "Other", "Unknown"])
        return random.choice(genders)

    def _generate_blood_type(self) -> str:
        """Generate a blood type."""
        # Use the person entity's blood type if it has one
        if hasattr(self._person_entity, "blood_type") and self._person_entity.blood_type:
            return self._person_entity.blood_type

        # Fallback to our cached data
        blood_types = self._DATA_CACHE.get("blood_types", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
        return random.choice(blood_types)

    def _generate_contact_number(self) -> str:
        """Generate a contact number."""
        # Use the person entity's phone number if it has one
        if hasattr(self._person_entity, "phone") and self._person_entity.phone:
            return self._person_entity.phone

        # Fallback to the address entity's phone number
        if hasattr(self._address_entity, "private_phone") and self._address_entity.private_phone:
            return self._address_entity.private_phone

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
        random_num = random.randint(1, 9999)
        domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"]
        domain = random.choice(domains)

        formats = [
            f"{first_name}.{last_name}@{domain}",
            f"{first_name}{last_name}@{domain}",
            f"{first_name}{random_num}@{domain}",
            f"{first_name[0]}{last_name}@{domain}",
        ]

        return random.choice(formats)

    def _generate_address(self) -> dict[str, str]:
        """Generate an address using AddressEntity."""
        return {
            "street": f"{self._address_entity.street} {self._address_entity.house_number}",
            "city": self._address_entity.city,
            "state": self._address_entity.state,
            "zip_code": self._address_entity.postal_code,
            "country": self._address_entity.country,
        }

    def _generate_insurance_provider(self) -> str:
        """Generate an insurance provider."""
        providers = self._DATA_CACHE.get("insurance_providers", [])
        if not providers:
            # Emergency fallback - should be handled properly by CSV files
            logger.warning("No insurance providers found in data cache, using emergency default list")
            return "Insurance Provider"
        return random.choice(providers)

    def _generate_insurance_policy_number(self) -> str:
        """Generate an insurance policy number."""
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return f"{random.choice(letters)}{random.randint(100000, 999999)}{random.choice(letters)}{random.randint(1000, 9999)}"

    def _generate_emergency_contact(self) -> dict[str, str]:
        """Generate emergency contact information."""
        # Create a new person for the emergency contact
        emergency_person = PersonEntity(self._class_factory_util, locale=self._locale, dataset=self._dataset)

        # Get relationships from cache
        relationships = self._DATA_CACHE.get("emergency_relationships", [])
        if not relationships:
            # Emergency fallback - should be handled properly by CSV files
            logger.warning("No emergency relationships found in data cache, using emergency default")
            relationship = "Family Member"
        else:
            relationship = random.choice(relationships)

        return {
            "name": f"{emergency_person.given_name} {emergency_person.family_name}",
            "relationship": relationship,
            "phone": emergency_person.phone if hasattr(emergency_person, "phone") else self._generate_contact_number(),
        }

    def _generate_medical_history(self) -> list[dict[str, str]]:
        """Generate medical history."""
        # Determine how many conditions to generate (0 to 5)
        num_conditions = random.randint(0, 5)

        if num_conditions == 0:
            return []

        # Get medical conditions from cache
        medical_conditions = self._DATA_CACHE.get("medical_conditions", [])
        statuses = self._DATA_CACHE.get("statuses", [])

        if not medical_conditions:
            # Emergency fallback - should be handled properly by CSV files
            logger.warning("No medical conditions found in data cache, using emergency default")
            return []

        # Use data from CSV
        if len(medical_conditions) < num_conditions:
            selected_conditions = medical_conditions
        else:
            selected_conditions = random.sample(medical_conditions, num_conditions)

        history = []
        for condition_data in selected_conditions:
            # Generate a diagnosis date between 1 and 20 years ago
            days_ago = random.randint(365, 7300)  # 1 to 20 years
            diagnosis_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            # Get status from the condition data or from the statuses list
            if "status" in condition_data and condition_data["status"]:
                status = condition_data["status"]
            elif statuses:
                status = random.choice(statuses)
            else:
                status = "Active"  # Emergency fallback

            history.append(
                {
                    "condition": condition_data["condition"],
                    "diagnosed_date": diagnosis_date,
                    "status": status,
                }
            )

        return history

    def _generate_allergies(self) -> list[dict[str, str]]:
        """Generate allergies."""
        # Determine how many allergies to generate (0 to 3)
        num_allergies = random.randint(0, 3)

        if num_allergies == 0:
            return []

        # Get allergies from cache
        allergies_data = self._DATA_CACHE.get("allergies", [])

        if not allergies_data:
            # Emergency fallback - should be handled properly by CSV files
            logger.warning("No allergies found in data cache, using emergency default")
            return []

        # Use data from CSV
        if len(allergies_data) < num_allergies:
            selected_allergies = allergies_data
        else:
            selected_allergies = random.sample(allergies_data, num_allergies)

        return [
            {
                "allergen": allergy["allergen"],
                "severity": allergy.get("severity", "Moderate"),
                "reaction": allergy.get("reaction", ""),
            }
            for allergy in selected_allergies
        ]

    def _generate_medications(self) -> list[dict[str, str]]:
        """Generate medications."""
        # Determine how many medications to generate (0 to 5)
        num_medications = random.randint(0, 5)

        if num_medications == 0:
            return []

        # Get medications from cache
        medications_data = self._DATA_CACHE.get("medications", [])

        if not medications_data:
            # Emergency fallback - should be handled properly by CSV files
            logger.warning("No medications found in data cache, using emergency default")
            return []

        # Use data from CSV
        if len(medications_data) < num_medications:
            selected_medications = medications_data
        else:
            selected_medications = random.sample(medications_data, num_medications)

        medications = []
        for medication in selected_medications:
            # Generate a start date between 1 month and 5 years ago
            days_ago = random.randint(30, 1825)  # 1 month to 5 years
            start_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            medications.append(
                {
                    "name": medication["name"],
                    "dosage": medication.get("dosage", ""),
                    "frequency": medication.get("frequency", ""),
                    "route": medication.get("route", "Oral"),
                    "start_date": start_date,
                }
            )

        return medications

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
    def patient_id(self) -> str:
        """Get the patient ID."""
        value = self._field_generators["patient_id"].get()
        assert value is not None, "patient_id should not be None"
        return value

    @property
    def first_name(self) -> str:
        """Get the first name."""
        value = self._field_generators["first_name"].get()
        assert value is not None, "first_name should not be None"
        return value

    @property
    def last_name(self) -> str:
        """Get the last name."""
        value = self._field_generators["last_name"].get()
        assert value is not None, "last_name should not be None"
        return value

    @property
    def date_of_birth(self) -> str:
        """Get the date of birth."""
        value = self._field_generators["date_of_birth"].get()
        assert value is not None, "date_of_birth should not be None"
        return value

    @property
    def gender(self) -> str:
        """Get the gender."""
        value = self._field_generators["gender"].get()
        assert value is not None, "gender should not be None"
        return value

    @property
    def blood_type(self) -> str:
        """Get the blood type."""
        value = self._field_generators["blood_type"].get()
        assert value is not None, "blood_type should not be None"
        return value

    @property
    def contact_number(self) -> str:
        """Get the contact number."""
        value = self._field_generators["contact_number"].get()
        assert value is not None, "contact_number should not be None"
        return value

    @property
    def email(self) -> str:
        """Get the email address."""
        value = self._field_generators["email"].get()
        assert value is not None, "email should not be None"
        return value

    @property
    def address(self) -> dict[str, str]:
        """Get the address."""
        value = self._field_generators["address"].get()
        assert value is not None, "address should not be None"
        return value

    @property
    def insurance_provider(self) -> str:
        """Get the insurance provider."""
        value = self._field_generators["insurance_provider"].get()
        assert value is not None, "insurance_provider should not be None"
        return value

    @property
    def insurance_policy_number(self) -> str:
        """Get the insurance policy number."""
        value = self._field_generators["insurance_policy_number"].get()
        assert value is not None, "insurance_policy_number should not be None"
        return value

    @property
    def emergency_contact(self) -> dict[str, str]:
        """Get the emergency contact."""
        value = self._field_generators["emergency_contact"].get()
        assert value is not None, "emergency_contact should not be None"
        return value

    @property
    def medical_history(self) -> list[dict[str, str]]:
        """Get the medical history."""
        value = self._field_generators["medical_history"].get()
        assert value is not None, "medical_history should not be None"
        return value

    @property
    def allergies(self) -> list[dict[str, str]]:
        """Get the allergies."""
        value = self._field_generators["allergies"].get()
        assert value is not None, "allergies should not be None"
        return value

    @property
    def medications(self) -> list[dict[str, str]]:
        """Get the medications."""
        value = self._field_generators["medications"].get()
        assert value is not None, "medications should not be None"
        return value

    def to_dict(self) -> dict[str, Any]:
        """Convert the entity to a dictionary.

        Returns:
            A dictionary containing all entity properties.
        """
        return {
            "patient_id": self.patient_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": self.date_of_birth,
            "gender": self.gender,
            "blood_type": self.blood_type,
            "contact_number": self.contact_number,
            "email": self.email,
            "address": self.address,
            "insurance_provider": self.insurance_provider,
            "insurance_policy_number": self.insurance_policy_number,
            "emergency_contact": self.emergency_contact,
            "medical_history": self.medical_history,
            "allergies": self.allergies,
            "medications": self.medications,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of patient data.

        Args:
            count: The number of records to generate.

        Returns:
            A list of dictionaries containing generated patient data.
        """
        field_names = [
            "patient_id",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "blood_type",
            "contact_number",
            "email",
            "address",
            "insurance_provider",
            "insurance_policy_number",
            "emergency_contact",
            "medical_history",
            "allergies",
            "medications",
        ]

        return EntityUtil.batch_generate_fields(self._field_generators, field_names, count)
