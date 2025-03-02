# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Medical Record Entity Core.

This module provides the core functionality for generating medical record data.
"""

import random
from collections.abc import Callable
from typing import Any, TypeVar, cast

from datamimic_ce.entities.entity import Entity
from datamimic_ce.entities.entity_util import EntityUtil
from datamimic_ce.entities.healthcare.doctor_entity import DoctorEntity
from datamimic_ce.entities.healthcare.medical_record_entity.data_loader import MedicalRecordDataLoader
from datamimic_ce.entities.healthcare.medical_record_entity.generators import (
    AllergyGenerator,
    AssessmentGenerator,
    DiagnosisGenerator,
    FollowUpGenerator,
    LabResultGenerator,
    MedicationGenerator,
    NotesGenerator,
    PlanGenerator,
    ProcedureGenerator,
)
from datamimic_ce.entities.healthcare.patient_entity import PatientEntity
from datamimic_ce.logger import logger

T = TypeVar("T")


class MedicalRecordEntity(Entity):
    """Generate medical record data.

    This class generates realistic medical record data including record IDs,
    patient IDs, doctor IDs, dates, visit types, chief complaints, vital signs,
    diagnoses, procedures, medications, lab results, allergies, assessments,
    plans, follow-ups, and notes.
    """

    def __init__(
        self,
        class_factory_util,
        locale: str = "en",
        dataset: str | None = None,
    ):
        """Initialize the MedicalRecordEntity.

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

        # Create data loader
        self._data_loader = MedicalRecordDataLoader(self._country_code)

        # Create patient entity for patient information
        self._patient_entity = PatientEntity(class_factory_util, locale=locale, dataset=dataset)

        # Create doctor entity for doctor information
        self._doctor_entity = DoctorEntity(class_factory_util, locale=locale, dataset=dataset)

        # Create specialized generators
        self._diagnosis_generator = DiagnosisGenerator(self._data_loader, self._data_generation_util)
        self._procedure_generator = ProcedureGenerator(self._data_loader, self._data_generation_util)
        self._medication_generator = MedicationGenerator(self._data_loader, self._data_generation_util)
        self._lab_result_generator = LabResultGenerator(self._data_loader, self._data_generation_util)
        self._allergy_generator = AllergyGenerator(self._data_loader, self._data_generation_util)
        self._assessment_generator = AssessmentGenerator(self._data_generation_util)
        self._plan_generator = PlanGenerator(self._data_generation_util)
        self._follow_up_generator = FollowUpGenerator(self._data_generation_util)
        self._notes_generator = NotesGenerator(self._data_generation_util)

        # Initialize field generators
        self._field_generators = EntityUtil.create_field_generator_dict(
            {
                "record_id": self._generate_record_id,
                "patient_id": self._generate_patient_id,
                "doctor_id": self._generate_doctor_id,
                "date": self._generate_date,
                "visit_type": self._generate_visit_type,
                "chief_complaint": self._generate_chief_complaint,
                "vital_signs": self._generate_vital_signs,
                "diagnosis": self._generate_diagnosis,
                "procedures": self._generate_procedures,
                "medications": self._generate_medications,
                "lab_results": self._generate_lab_results,
                "allergies": self._generate_allergies,
                "assessment": self._generate_assessment,
                "plan": self._generate_plan,
                "follow_up": self._generate_follow_up,
                "notes": self._generate_notes,
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

    def _generate_record_id(self) -> str:
        """Generate a unique record ID."""
        return f"MR-{random.randint(10000000, 99999999)}"

    def _generate_patient_id(self) -> str:
        """Generate a patient ID."""
        return self._patient_entity.patient_id

    def _generate_doctor_id(self) -> str:
        """Generate a doctor ID."""
        return self._doctor_entity.doctor_id

    def _generate_date(self) -> str:
        """Generate a date for the medical record."""
        # Generate a date within the last year
        days_ago = random.randint(0, 365)
        date = self._data_generation_util.get_date_n_days_ago(days_ago)
        return date.strftime("%Y-%m-%d")

    def _generate_visit_type(self) -> str:
        """Generate a visit type."""
        visit_types = self._data_loader.get_visit_types()
        if not visit_types:
            logger.error("No visit types found in data cache. Please create a data file.")
            return "Unknown Visit Type"

        # Select a visit type based on weights
        visit_type, _ = self._data_generation_util.weighted_choice(visit_types)
        return visit_type

    def _generate_chief_complaint(self) -> str:
        """Generate a chief complaint."""
        chief_complaints = self._data_loader.get_chief_complaints()
        if not chief_complaints:
            logger.error("No chief complaints found in data cache. Please create a data file.")
            return "Unknown Complaint"

        # Select a chief complaint based on weights
        chief_complaint, _ = self._data_generation_util.weighted_choice(chief_complaints)
        return chief_complaint

    def _generate_vital_signs(self) -> dict[str, Any]:
        """Generate vital signs."""
        # Generate random vital signs
        temperature = round(random.uniform(36.0, 37.5), 1)  # Celsius
        heart_rate = random.randint(60, 100)  # BPM
        respiratory_rate = random.randint(12, 20)  # breaths per minute
        systolic_bp = random.randint(110, 140)  # mmHg
        diastolic_bp = random.randint(60, 90)  # mmHg
        oxygen_saturation = random.randint(95, 100)  # percentage

        return {
            "temperature": f"{temperature} °C",
            "heart_rate": f"{heart_rate} BPM",
            "respiratory_rate": f"{respiratory_rate} breaths/min",
            "blood_pressure": f"{systolic_bp}/{diastolic_bp} mmHg",
            "oxygen_saturation": f"{oxygen_saturation}%",
        }

    def _generate_diagnosis(self) -> list[dict[str, str]]:
        """Generate diagnosis data."""
        return self._diagnosis_generator.generate_diagnosis()

    def _generate_procedures(self) -> list[dict[str, str]]:
        """Generate procedure data."""
        return self._procedure_generator.generate_procedures()

    def _generate_medications(self) -> list[dict[str, str]]:
        """Generate medication data."""
        return self._medication_generator.generate_medications()

    def _generate_lab_results(self) -> list[dict[str, str]]:
        """Generate lab result data."""
        return self._lab_result_generator.generate_lab_results()

    def _generate_allergies(self) -> list[dict[str, str]]:
        """Generate allergy data."""
        return self._allergy_generator.generate_allergies()

    def _generate_assessment(self) -> str:
        """Generate assessment data."""
        # Get chief complaint and diagnosis from cache if available
        chief_complaint = self._get_cached_property(
            "chief_complaint", lambda: self._field_generators["chief_complaint"].get()
        )
        diagnoses = self._get_cached_property("diagnosis", lambda: self._field_generators["diagnosis"].get())

        return self._assessment_generator.generate_assessment(chief_complaint, diagnoses)

    def _generate_plan(self) -> str:
        """Generate plan data."""
        # Get procedures, medications, and lab results from cache if available
        procedures = self._get_cached_property("procedures", lambda: self._field_generators["procedures"].get())
        medications = self._get_cached_property("medications", lambda: self._field_generators["medications"].get())
        lab_results = self._get_cached_property("lab_results", lambda: self._field_generators["lab_results"].get())

        return self._plan_generator.generate_plan(procedures, medications, lab_results)

    def _generate_follow_up(self) -> dict[str, str]:
        """Generate follow-up data."""
        return self._follow_up_generator.generate_follow_up()

    def _generate_notes(self) -> str:
        """Generate clinical notes."""
        # Get chief complaint, assessment, and plan from cache if available
        chief_complaint = self._get_cached_property(
            "chief_complaint", lambda: self._field_generators["chief_complaint"].get()
        )
        assessment = self._get_cached_property("assessment", lambda: self._field_generators["assessment"].get())
        plan = self._get_cached_property("plan", lambda: self._field_generators["plan"].get())

        return self._notes_generator.generate_notes(chief_complaint, assessment, plan)

    def reset(self) -> None:
        """Reset all field generators and caches."""
        for generator in self._field_generators.values():
            generator.reset()

        # Reset patient and doctor entities
        self._patient_entity.reset()
        self._doctor_entity.reset()

        # Clear property cache
        self._property_cache.clear()

    @property
    def record_id(self) -> str:
        """Get the record ID."""
        return cast(str, self._get_cached_property("record_id", lambda: self._field_generators["record_id"].get()))

    @property
    def patient_id(self) -> str:
        """Get the patient ID."""
        return cast(str, self._get_cached_property("patient_id", lambda: self._field_generators["patient_id"].get()))

    @property
    def doctor_id(self) -> str:
        """Get the doctor ID."""
        return cast(str, self._get_cached_property("doctor_id", lambda: self._field_generators["doctor_id"].get()))

    @property
    def date(self) -> str:
        """Get the date."""
        return cast(str, self._get_cached_property("date", lambda: self._field_generators["date"].get()))

    @property
    def visit_type(self) -> str:
        """Get the visit type."""
        return cast(str, self._get_cached_property("visit_type", lambda: self._field_generators["visit_type"].get()))

    @property
    def chief_complaint(self) -> str:
        """Get the chief complaint."""
        return cast(
            str, self._get_cached_property("chief_complaint", lambda: self._field_generators["chief_complaint"].get())
        )

    @property
    def vital_signs(self) -> dict[str, Any]:
        """Get the vital signs."""
        return cast(
            dict[str, Any],
            self._get_cached_property("vital_signs", lambda: self._field_generators["vital_signs"].get()),
        )

    @property
    def diagnosis(self) -> list[dict[str, str]]:
        """Get the diagnosis."""
        return cast(
            list[dict[str, str]],
            self._get_cached_property("diagnosis", lambda: self._field_generators["diagnosis"].get()),
        )

    @property
    def procedures(self) -> list[dict[str, str]]:
        """Get the procedures."""
        return cast(
            list[dict[str, str]],
            self._get_cached_property("procedures", lambda: self._field_generators["procedures"].get()),
        )

    @property
    def medications(self) -> list[dict[str, str]]:
        """Get the medications."""
        return cast(
            list[dict[str, str]],
            self._get_cached_property("medications", lambda: self._field_generators["medications"].get()),
        )

    @property
    def lab_results(self) -> list[dict[str, str]]:
        """Get the lab results."""
        return cast(
            list[dict[str, str]],
            self._get_cached_property("lab_results", lambda: self._field_generators["lab_results"].get()),
        )

    @property
    def allergies(self) -> list[dict[str, str]]:
        """Get the allergies."""
        return cast(
            list[dict[str, str]],
            self._get_cached_property("allergies", lambda: self._field_generators["allergies"].get()),
        )

    @property
    def assessment(self) -> str:
        """Get the assessment."""
        return cast(str, self._get_cached_property("assessment", lambda: self._field_generators["assessment"].get()))

    @property
    def plan(self) -> str:
        """Get the plan."""
        return cast(str, self._get_cached_property("plan", lambda: self._field_generators["plan"].get()))

    @property
    def follow_up(self) -> dict[str, str]:
        """Get the follow-up."""
        return cast(
            dict[str, str],
            self._get_cached_property("follow_up", lambda: self._field_generators["follow_up"].get()),
        )

    @property
    def notes(self) -> str:
        """Get the notes."""
        return cast(str, self._get_cached_property("notes", lambda: self._field_generators["notes"].get()))

    @property
    def patient_name(self) -> str:
        """Get the patient name."""
        return f"{self._patient_entity.first_name} {self._patient_entity.last_name}"

    @property
    def doctor_name(self) -> str:
        """Get the doctor name."""
        return f"{self._doctor_entity.first_name} {self._doctor_entity.last_name}"

    def to_dict(self) -> dict[str, Any]:
        """Convert the entity to a dictionary.

        Returns:
            A dictionary containing all entity properties.
        """
        return {
            "record_id": self.record_id,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "doctor_id": self.doctor_id,
            "doctor_name": self.doctor_name,
            "date": self.date,
            "visit_type": self.visit_type,
            "chief_complaint": self.chief_complaint,
            "vital_signs": self.vital_signs,
            "diagnosis": self.diagnosis,
            "procedures": self.procedures,
            "medications": self.medications,
            "lab_results": self.lab_results,
            "allergies": self.allergies,
            "assessment": self.assessment,
            "plan": self.plan,
            "follow_up": self.follow_up,
            "notes": self.notes,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of medical record data.

        Args:
            count: The number of records to generate.

        Returns:
            A list of dictionaries containing generated medical record data.
        """
        field_names = [
            "record_id",
            "patient_id",
            "doctor_id",
            "date",
            "visit_type",
            "chief_complaint",
            "vital_signs",
            "diagnosis",
            "procedures",
            "medications",
            "lab_results",
            "allergies",
            "assessment",
            "plan",
            "follow_up",
            "notes",
        ]

        batch = EntityUtil.batch_generate_fields(self._field_generators, field_names, count)

        # Add patient and doctor names to each record
        for i in range(count):
            # Reset entities for each record
            self._patient_entity.reset()
            self._doctor_entity.reset()

            # Add patient and doctor names
            batch[i]["patient_name"] = f"{self._patient_entity.first_name} {self._patient_entity.last_name}"
            batch[i]["doctor_name"] = f"{self._doctor_entity.first_name} {self._doctor_entity.last_name}"

        return batch
