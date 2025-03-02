# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Patient entity model.

This module provides the Patient entity model for generating realistic patient data.
"""

from datetime import datetime
from typing import Any, ClassVar

from datamimic_ce.core.base_entity import BaseEntity
from datamimic_ce.core.property_cache import PropertyCache
from datamimic_ce.domains.healthcare.data_loaders.patient_loader import PatientDataLoader


class Patient(BaseEntity):
    """Generate patient data.

    This class generates realistic patient data including patient IDs,
    names, demographics, medical history, insurance information, and contact details.

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
        """Initialize the Patient entity.

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
        self._data_loader = PatientDataLoader()

        # Initialize person entity for personal information
        self._person_entity = self._class_factory_util.get_person_entity(locale=locale, dataset=dataset)

        # Initialize address entity for address information
        self._address_entity = self._class_factory_util.get_address_entity(locale=locale, dataset=dataset)

        # Initialize field generators
        self._initialize_generators()

    def _initialize_generators(self):
        """Initialize all field generators."""
        # Basic information
        self._patient_id_generator = PropertyCache(self._generate_patient_id)
        self._medical_record_number_generator = PropertyCache(self._generate_medical_record_number)
        self._ssn_generator = PropertyCache(self._generate_ssn)
        self._blood_type_generator = PropertyCache(self._generate_blood_type)
        self._height_cm_generator = PropertyCache(self._generate_height_cm)
        self._weight_kg_generator = PropertyCache(self._generate_weight_kg)
        self._bmi_generator = PropertyCache(self._generate_bmi)
        self._allergies_generator = PropertyCache(self._generate_allergies)
        self._medications_generator = PropertyCache(self._generate_medications)
        self._conditions_generator = PropertyCache(self._generate_conditions)
        self._emergency_contact_generator = PropertyCache(self._generate_emergency_contact)
        self._insurance_provider_generator = PropertyCache(self._generate_insurance_provider)
        self._insurance_policy_number_generator = PropertyCache(self._generate_insurance_policy_number)
        self._primary_care_physician_generator = PropertyCache(self._generate_primary_care_physician)
        self._last_visit_date_generator = PropertyCache(self._generate_last_visit_date)
        self._next_appointment_generator = PropertyCache(self._generate_next_appointment)
        self._email_generator = PropertyCache(self._generate_email)
        self._phone_generator = PropertyCache(self._generate_phone)

    def reset(self) -> None:
        """Reset all field generators, causing new values to be generated on the next access."""
        self._person_entity.reset()
        self._address_entity.reset()
        self._patient_id_generator.reset()
        self._medical_record_number_generator.reset()
        self._ssn_generator.reset()
        self._blood_type_generator.reset()
        self._height_cm_generator.reset()
        self._weight_kg_generator.reset()
        self._bmi_generator.reset()
        self._allergies_generator.reset()
        self._medications_generator.reset()
        self._conditions_generator.reset()
        self._emergency_contact_generator.reset()
        self._insurance_provider_generator.reset()
        self._insurance_policy_number_generator.reset()
        self._primary_care_physician_generator.reset()
        self._last_visit_date_generator.reset()
        self._next_appointment_generator.reset()
        self._email_generator.reset()
        self._phone_generator.reset()

    def to_dict(self) -> dict[str, Any]:
        """Convert the patient entity to a dictionary.

        Returns:
            A dictionary containing all patient properties.
        """
        return {
            "patient_id": self.patient_id,
            "medical_record_number": self.medical_record_number,
            "ssn": self.ssn,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "gender": self.gender,
            "date_of_birth": self.date_of_birth,
            "age": self.age,
            "blood_type": self.blood_type,
            "height_cm": self.height_cm,
            "weight_kg": self.weight_kg,
            "bmi": self.bmi,
            "allergies": self.allergies,
            "medications": self.medications,
            "conditions": self.conditions,
            "emergency_contact": self.emergency_contact,
            "insurance_provider": self.insurance_provider,
            "insurance_policy_number": self.insurance_policy_number,
            "primary_care_physician": self.primary_care_physician,
            "last_visit_date": self.last_visit_date,
            "next_appointment": self.next_appointment,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of patient entities.

        Args:
            count: The number of patient entities to generate.

        Returns:
            A list of dictionaries containing the generated patient entities.
        """
        patients = []
        for _ in range(count):
            patients.append(self.to_dict())
            self.reset()
        return patients

    # Property getters
    @property
    def patient_id(self) -> str:
        """Get the patient ID.

        Returns:
            A unique identifier for the patient.
        """
        return self._patient_id_generator.get()

    @property
    def medical_record_number(self) -> str:
        """Get the medical record number.

        Returns:
            A medical record number.
        """
        return self._medical_record_number_generator.get()

    @property
    def ssn(self) -> str:
        """Get the social security number.

        Returns:
            A social security number.
        """
        return self._ssn_generator.get()

    @property
    def first_name(self) -> str:
        """Get the patient's first name.

        Returns:
            The patient's first name.
        """
        return self._person_entity.first_name

    @property
    def last_name(self) -> str:
        """Get the patient's last name.

        Returns:
            The patient's last name.
        """
        return self._person_entity.last_name

    @property
    def full_name(self) -> str:
        """Get the patient's full name.

        Returns:
            The patient's full name.
        """
        return f"{self.first_name} {self.last_name}"

    @property
    def gender(self) -> str:
        """Get the patient's gender.

        Returns:
            The patient's gender.
        """
        return self._person_entity.gender

    @property
    def date_of_birth(self) -> str:
        """Get the patient's date of birth.

        Returns:
            The patient's date of birth in YYYY-MM-DD format.
        """
        return self._person_entity.date_of_birth

    @property
    def age(self) -> int:
        """Get the patient's age.

        Returns:
            The patient's age in years.
        """
        return self._person_entity.age

    @property
    def blood_type(self) -> str:
        """Get the patient's blood type.

        Returns:
            The patient's blood type.
        """
        return self._blood_type_generator.get()

    @property
    def height_cm(self) -> float:
        """Get the patient's height in centimeters.

        Returns:
            The patient's height in centimeters.
        """
        return self._height_cm_generator.get()

    @property
    def weight_kg(self) -> float:
        """Get the patient's weight in kilograms.

        Returns:
            The patient's weight in kilograms.
        """
        return self._weight_kg_generator.get()

    @property
    def bmi(self) -> float:
        """Get the patient's body mass index (BMI).

        Returns:
            The patient's BMI.
        """
        return self._bmi_generator.get()

    @property
    def allergies(self) -> list[str]:
        """Get the patient's allergies.

        Returns:
            A list of allergies.
        """
        return self._allergies_generator.get()

    @property
    def medications(self) -> list[str]:
        """Get the patient's medications.

        Returns:
            A list of medications.
        """
        return self._medications_generator.get()

    @property
    def conditions(self) -> list[str]:
        """Get the patient's medical conditions.

        Returns:
            A list of medical conditions.
        """
        return self._conditions_generator.get()

    @property
    def emergency_contact(self) -> dict[str, str]:
        """Get the patient's emergency contact.

        Returns:
            A dictionary containing emergency contact information.
        """
        return self._emergency_contact_generator.get()

    @property
    def insurance_provider(self) -> str:
        """Get the patient's insurance provider.

        Returns:
            The patient's insurance provider.
        """
        return self._insurance_provider_generator.get()

    @property
    def insurance_policy_number(self) -> str:
        """Get the patient's insurance policy number.

        Returns:
            The patient's insurance policy number.
        """
        return self._insurance_policy_number_generator.get()

    @property
    def primary_care_physician(self) -> str:
        """Get the patient's primary care physician.

        Returns:
            The patient's primary care physician.
        """
        return self._primary_care_physician_generator.get()

    @property
    def last_visit_date(self) -> str:
        """Get the patient's last visit date.

        Returns:
            The patient's last visit date in YYYY-MM-DD format.
        """
        return self._last_visit_date_generator.get()

    @property
    def next_appointment(self) -> str | None:
        """Get the patient's next appointment date.

        Returns:
            The patient's next appointment date in YYYY-MM-DD format, or None if no appointment is scheduled.
        """
        return self._next_appointment_generator.get()

    @property
    def email(self) -> str:
        """Get the patient's email address.

        Returns:
            The patient's email address.
        """
        return self._email_generator.get()

    @property
    def phone(self) -> str:
        """Get the patient's phone number.

        Returns:
            The patient's phone number.
        """
        return self._phone_generator.get()

    @property
    def address(self) -> dict[str, Any]:
        """Get the patient's address.

        Returns:
            A dictionary containing the patient's address information.
        """
        return self._address_entity.to_dict()

    # Generator methods
    def _generate_patient_id(self) -> str:
        """Generate a unique patient ID.

        Returns:
            A unique patient ID.
        """
        import uuid

        return f"PAT-{uuid.uuid4().hex[:8].upper()}"

    def _generate_medical_record_number(self) -> str:
        """Generate a medical record number.

        Returns:
            A medical record number.
        """
        import random

        return f"MRN-{random.randint(1000000, 9999999)}"

    def _generate_ssn(self) -> str:
        """Generate a social security number.

        Returns:
            A social security number.
        """
        import random

        return f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"

    def _generate_blood_type(self) -> str:
        """Generate a blood type.

        Returns:
            A blood type.
        """
        import random

        blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        return random.choice(blood_types)

    def _generate_height_cm(self) -> float:
        """Generate a height in centimeters.

        Returns:
            A height in centimeters.
        """
        import random

        # Generate height based on gender and age
        gender = self.gender
        age = self.age

        if age < 18:
            # Children and teenagers
            if gender == "Male":
                return round(random.uniform(90 + (age * 5), 110 + (age * 5)), 1)
            else:
                return round(random.uniform(90 + (age * 4.8), 110 + (age * 4.8)), 1)
        else:
            # Adults
            if gender == "Male":
                return round(random.uniform(160, 190), 1)
            else:
                return round(random.uniform(150, 175), 1)

    def _generate_weight_kg(self) -> float:
        """Generate a weight in kilograms.

        Returns:
            A weight in kilograms.
        """
        import random

        # Generate weight based on gender, age, and height
        gender = self.gender
        age = self.age
        height_cm = self.height_cm

        # Calculate a base weight using BMI formula (weight = BMI * height^2)
        # Use a normal BMI range (18.5 - 29.9)
        if age < 18:
            # Children and teenagers - lower BMI range
            base_bmi = random.uniform(16, 24)
        else:
            # Adults - normal BMI range with some variation
            base_bmi = random.uniform(18.5, 29.9)

        # Calculate weight from BMI and height
        # BMI = weight(kg) / height(m)^2
        height_m = height_cm / 100
        weight = base_bmi * (height_m**2)

        # Add some random variation
        weight_variation = weight * 0.1  # 10% variation
        weight += random.uniform(-weight_variation, weight_variation)

        return round(weight, 1)

    def _generate_bmi(self) -> float:
        """Generate a body mass index (BMI).

        Returns:
            A BMI value.
        """
        # Calculate BMI using the formula: BMI = weight(kg) / height(m)^2
        height_m = self.height_cm / 100
        bmi = self.weight_kg / (height_m**2)
        return round(bmi, 1)

    def _generate_allergies(self) -> list[str]:
        """Generate a list of allergies.

        Returns:
            A list of allergies.
        """
        import random

        from datamimic_ce.domains.healthcare.generators.patient_generator import weighted_choice

        allergies = self._data_loader.get_data("allergies", self._country_code)

        # Determine how many allergies to generate (most people have 0-3)
        num_allergies = random.choices([0, 1, 2, 3, 4, 5], weights=[0.5, 0.2, 0.15, 0.1, 0.03, 0.02], k=1)[0]

        if num_allergies == 0:
            return []

        # Generate unique allergies
        result = []
        for _ in range(num_allergies):
            allergy = weighted_choice(allergies)
            if allergy not in result:
                result.append(allergy)

        return result

    def _generate_medications(self) -> list[str]:
        """Generate a list of medications.

        Returns:
            A list of medications.
        """
        import random

        from datamimic_ce.domains.healthcare.generators.patient_generator import weighted_choice

        medications = self._data_loader.get_data("medications", self._country_code)

        # Determine how many medications to generate
        # Older people tend to take more medications
        age = self.age
        if age < 18:
            weights = [0.7, 0.2, 0.08, 0.02, 0.0, 0.0]
        elif age < 40:
            weights = [0.5, 0.3, 0.15, 0.04, 0.01, 0.0]
        elif age < 65:
            weights = [0.3, 0.3, 0.2, 0.1, 0.07, 0.03]
        else:
            weights = [0.1, 0.2, 0.3, 0.2, 0.15, 0.05]

        num_medications = random.choices([0, 1, 2, 3, 4, 5], weights=weights, k=1)[0]

        if num_medications == 0:
            return []

        # Generate unique medications
        result = []
        for _ in range(num_medications):
            medication = weighted_choice(medications)
            if medication not in result:
                result.append(medication)

        return result

    def _generate_conditions(self) -> list[str]:
        """Generate a list of medical conditions.

        Returns:
            A list of medical conditions.
        """
        import random

        from datamimic_ce.domains.healthcare.generators.patient_generator import weighted_choice

        conditions = self._data_loader.get_data("conditions", self._country_code)

        # Determine how many conditions to generate
        # Older people tend to have more conditions
        age = self.age
        if age < 18:
            weights = [0.8, 0.15, 0.04, 0.01, 0.0, 0.0]
        elif age < 40:
            weights = [0.6, 0.25, 0.1, 0.04, 0.01, 0.0]
        elif age < 65:
            weights = [0.4, 0.3, 0.15, 0.1, 0.04, 0.01]
        else:
            weights = [0.2, 0.3, 0.25, 0.15, 0.07, 0.03]

        num_conditions = random.choices([0, 1, 2, 3, 4, 5], weights=weights, k=1)[0]

        if num_conditions == 0:
            return []

        # Generate unique conditions
        result = []
        for _ in range(num_conditions):
            condition = weighted_choice(conditions)
            if condition not in result:
                result.append(condition)

        return result

    def _generate_emergency_contact(self) -> dict[str, str]:
        """Generate emergency contact information.

        Returns:
            A dictionary containing emergency contact information.
        """
        import random

        # Generate a name for the emergency contact
        first_names = self._data_loader.get_data("first_names", self._country_code)
        last_names = self._data_loader.get_data("last_names", self._country_code)

        from datamimic_ce.domains.healthcare.generators.patient_generator import weighted_choice

        first_name = weighted_choice(first_names)

        # 50% chance the emergency contact has the same last name
        if random.random() < 0.5:
            last_name = self.last_name
        else:
            last_name = weighted_choice(last_names)

        # Generate a relationship
        relationships = [
            "Spouse",
            "Parent",
            "Child",
            "Sibling",
            "Friend",
            "Grandparent",
            "Aunt",
            "Uncle",
            "Cousin",
            "Partner",
        ]
        relationship = random.choice(relationships)

        # Generate a phone number
        area_code = random.randint(100, 999)
        prefix = random.randint(100, 999)
        line = random.randint(1000, 9999)
        phone = f"({area_code}) {prefix}-{line}"

        return {"name": f"{first_name} {last_name}", "relationship": relationship, "phone": phone}

    def _generate_insurance_provider(self) -> str:
        """Generate an insurance provider.

        Returns:
            An insurance provider name.
        """
        from datamimic_ce.domains.healthcare.generators.patient_generator import weighted_choice

        insurance_providers = self._data_loader.get_data("insurance_providers", self._country_code)
        return weighted_choice(insurance_providers)

    def _generate_insurance_policy_number(self) -> str:
        """Generate an insurance policy number.

        Returns:
            An insurance policy number.
        """
        import random
        import string

        # Generate a policy number with a mix of letters and numbers
        prefix = "".join(random.choices(string.ascii_uppercase, k=3))
        number = "".join(random.choices(string.digits, k=8))

        return f"{prefix}-{number}"

    def _generate_primary_care_physician(self) -> str:
        """Generate a primary care physician name.

        Returns:
            A primary care physician name.
        """
        from datamimic_ce.domains.healthcare.generators.patient_generator import weighted_choice

        # Generate a doctor name
        first_names = self._data_loader.get_data("doctor_first_names", self._country_code)
        last_names = self._data_loader.get_data("doctor_last_names", self._country_code)

        first_name = weighted_choice(first_names)
        last_name = weighted_choice(last_names)

        # Add title
        title = "Dr."

        return f"{title} {first_name} {last_name}"

    def _generate_last_visit_date(self) -> str:
        """Generate a last visit date.

        Returns:
            A last visit date in YYYY-MM-DD format.
        """
        import random
        from datetime import timedelta

        # Generate a date within the last 2 years
        days_ago = random.randint(1, 730)  # Up to 2 years ago
        visit_date = datetime.now() - timedelta(days=days_ago)

        return visit_date.strftime("%Y-%m-%d")

    def _generate_next_appointment(self) -> str | None:
        """Generate a next appointment date.

        Returns:
            A next appointment date in YYYY-MM-DD format, or None if no appointment is scheduled.
        """
        import random
        from datetime import timedelta

        # 30% chance of no upcoming appointment
        if random.random() < 0.3:
            return None

        # Generate a date in the next 6 months
        days_ahead = random.randint(1, 180)  # Up to 6 months ahead
        appointment_date = datetime.now() + timedelta(days=days_ahead)

        return appointment_date.strftime("%Y-%m-%d")

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
            f"{last}.{first}@{domain}",
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
