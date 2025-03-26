# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Patient entity model.

This module provides the Patient entity model for generating realistic patient data.
"""

import datetime
import random
import string
import uuid
from typing import Any

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.common.models.person import Person
from datamimic_ce.domains.healthcare.generators.patient_generator import PatientGenerator


class Patient(BaseEntity):
    """Generate patient data.

    This class generates realistic patient data including patient IDs,
    names, demographics, medical history, insurance information, and contact details.

    It uses PersonEntity for generating personal information and
    AddressEntity for generating address information.

    Data is loaded from country-specific CSV files when available,
    falling back to generic data files if needed.
    """

    def __init__(self, patient_generator: PatientGenerator):
        """Initialize the Patient entity.

        Args:
            class_factory_util: The class factory utility.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
        """
        super().__init__()
        self._patient_generator = patient_generator

    @property
    @property_cache
    def patient_id(self) -> str:
        """Get the patient ID.

        Returns:
            A unique identifier for the patient.
        """
        return f"PAT-{uuid.uuid4().hex[:8].upper()}"

    @property
    @property_cache
    def medical_record_number(self) -> str:
        """Get the medical record number.

        Returns:
            A medical record number.
        """
        return f"MRN-{uuid.uuid4().hex[:8].upper()}"

    @property
    @property_cache
    def ssn(self) -> str:
        """Get the social security number.

        Returns:
            A social security number.
        """
        return f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"

    @property
    @property_cache
    def person_data(self) -> Person:
        """Get the person data.

        Returns:
            The person data.
        """
        return Person(self._patient_generator.person_generator)

    @property
    @property_cache
    def given_name(self) -> str:
        """Get the patient's given name.

        Returns:
            The patient's given name.
        """
        return self.person_data.given_name

    @property
    @property_cache
    def family_name(self) -> str:
        """Get the patient's family name.

        Returns:
            The patient's family name.
        """
        return self.person_data.family_name

    @property
    @property_cache
    def full_name(self) -> str:
        """Get the patient's full name.

        Returns:
            The patient's full name.
        """
        return f"{self.given_name} {self.family_name}"

    @property
    @property_cache
    def gender(self) -> str:
        """Get the patient's gender.

        Returns:
            The patient's gender.
        """
        return self.person_data.gender

    @property
    @property_cache
    def birthdate(self) -> datetime.datetime:
        """Get the patient's date of birth.

        Returns:
            The patient's date of birth in YYYY-MM-DD format.
        """
        return self.person_data.birthdate

    @property
    @property_cache
    def age(self) -> int:
        """Get the patient's age.

        Returns:
            The patient's age in years.
        """
        return self.person_data.age

    @property
    @property_cache
    def blood_type(self) -> str:
        """Get the patient's blood type.

        Returns:
            The patient's blood type.
        """
        blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        return random.choice(blood_types)

    @property
    @property_cache
    def height_cm(self) -> float:
        """Get the patient's height in centimeters.

        Returns:
            The patient's height in centimeters.
        """
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

    @property
    @property_cache
    def weight_kg(self) -> float:
        """Get the patient's weight in kilograms.

        Returns:
            The patient's weight in kilograms.
        """
        # Generate weight based on gender, age, and height
        age = self.age
        height_cm = self.height_cm

        # Calculate a base weight using BMI formula (weight = BMI * height^2)
        # Use a normal BMI range (18.5 - 29.9)
        base_bmi = random.uniform(16, 24) if age < 18 else random.uniform(18.5, 29.9)

        # Calculate weight from BMI and height
        # BMI = weight(kg) / height(m)^2
        height_m = height_cm / 100
        weight = base_bmi * (height_m**2)

        # Add some random variation
        weight_variation = weight * 0.1  # 10% variation
        weight += random.uniform(-weight_variation, weight_variation)

        return round(weight, 1)

    @property
    @property_cache
    def bmi(self) -> float:
        """Get the patient's body mass index (BMI).

        Returns:
            The patient's BMI.
        """
        height_m = self.height_cm / 100
        bmi = self.weight_kg / (height_m**2)
        return round(bmi, 1)

    @property
    @property_cache
    def allergies(self) -> list[str]:
        """Get the patient's allergies.

        Returns:
            A list of allergies.
        """
        return self._patient_generator.get_allergies()

    @property
    @property_cache
    def medications(self) -> list[str]:
        """Get the patient's medications.

        Returns:
            A list of medications.
        """
        return self._patient_generator.get_medications(self.age)

    @property
    @property_cache
    def conditions(self) -> list[str]:
        """Get the patient's medical conditions.

        Returns:
            A list of medical conditions.
        """
        return self._patient_generator.generate_age_appropriate_conditions(self.age)

    @property
    @property_cache
    def emergency_contact(self) -> dict[str, str]:
        """Get the patient's emergency contact.

        Returns:
            A dictionary containing emergency contact information.
        """
        return self._patient_generator.get_emergency_contact(self.family_name)

    @property
    @property_cache
    def insurance_provider(self) -> str:
        """Get the patient's insurance provider.

        Returns:
            The patient's insurance provider.
        """
        return self._patient_generator.generate_insurance_provider()

    @property
    @property_cache
    def insurance_policy_number(self) -> str:
        """Get the patient's insurance policy number.

        Returns:
            The patient's insurance policy number.
        """
        # Generate a policy number with a mix of letters and numbers
        prefix = "".join(random.choices(string.ascii_uppercase, k=3))
        number = "".join(random.choices(string.digits, k=8))

        return f"{prefix}-{number}"

    @property
    def primary_doctor(self):
        """Get the patient's primary doctor.

        Returns:
            The patient's primary doctor.
        """
        if "primary_doctor" in self._field_cache:
            return self._field_cache["primary_doctor"]
        return None

    @primary_doctor.setter
    def primary_doctor(self, value):
        """Set the patient's primary doctor.

        Args:
            value: The doctor to assign as the patient's primary doctor.
        """
        self._field_cache["primary_doctor"] = value

    def to_dict(self) -> dict[str, Any]:
        """Convert the patient entity to a dictionary.

        Returns:
            A dictionary containing all patient properties.
        """
        result = {
            "patient_id": self.patient_id,
            "medical_record_number": self.medical_record_number,
            "ssn": self.ssn,
            "given_name": self.given_name,
            "family_name": self.family_name,
            "full_name": self.full_name,
            "gender": self.gender,
            "birthdate": self.birthdate,
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
        }

        if "primary_doctor" in self._field_cache:
            result["primary_doctor"] = self.primary_doctor

        return result
