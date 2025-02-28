# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import csv
import datetime
import random
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from datamimic_ce.entities.entity import Entity
from datamimic_ce.entities.entity_util import EntityUtil
from datamimic_ce.entities.person_entity import PersonEntity

T = TypeVar("T")


class MedicalRecordEntity(Entity):
    """Generate medical record data.

    This class generates realistic medical record data including record IDs,
    patient IDs, doctor IDs, dates, visit types, chief complaints, vital signs,
    diagnoses, procedures, medications, lab results, allergies, assessments,
    plans, follow-ups, and notes.
    """

    # Module-level cache for data to reduce file I/O
    _DATA_CACHE: dict[str, list[Any]] = {}

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

        # Create person entities for patient and doctor name generation
        self._patient_entity = PersonEntity(class_factory_util, locale=locale, dataset=dataset)
        self._doctor_entity = PersonEntity(class_factory_util, locale=locale, dataset=dataset)

        # Load data from CSV files
        self._load_data()

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

    @classmethod
    def _load_data(cls):
        """Load data from CSV files."""
        if not cls._DATA_CACHE:
            data_dir = Path(__file__).parent / "data" / "medical"

            # Load visit types
            cls._DATA_CACHE["visit_types"] = cls._load_simple_csv(data_dir / "visit_types.csv")

            # Load chief complaints
            cls._DATA_CACHE["chief_complaints"] = cls._load_simple_csv(data_dir / "chief_complaints.csv")

            # Load diagnosis codes
            cls._DATA_CACHE["diagnosis_codes"] = cls._load_csv_with_header(data_dir / "diagnosis_codes.csv")

            # Load procedure codes
            cls._DATA_CACHE["procedure_codes"] = cls._load_csv_with_header(data_dir / "procedure_codes.csv")

            # Load medications
            cls._DATA_CACHE["medications"] = cls._load_csv_with_header(data_dir / "medications.csv")

            # Load lab tests
            cls._DATA_CACHE["lab_tests"] = cls._load_csv_with_header(data_dir / "lab_tests.csv")

            # Load allergies
            cls._DATA_CACHE["allergies"] = cls._load_csv_with_header(data_dir / "allergies.csv")

            # Load medical conditions
            cls._DATA_CACHE["medical_conditions"] = cls._load_csv_with_header(data_dir / "medical_conditions.csv")

            # Load specimen types
            cls._DATA_CACHE["specimen_types"] = cls._load_simple_csv(data_dir / "specimen_types.csv")

            # Load labs
            cls._DATA_CACHE["labs"] = cls._load_csv_with_header(data_dir / "labs.csv")

            # Load statuses
            cls._DATA_CACHE["statuses"] = cls._load_simple_csv(data_dir / "statuses.csv")

    @staticmethod
    def _load_simple_csv(file_path: Path) -> list[str]:
        """Load a simple CSV file with one value per line.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of values from the CSV file
        """
        if not file_path.exists():
            return []

        try:
            with open(file_path, encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except Exception:
            return []

    @staticmethod
    def _load_csv_with_header(file_path: Path) -> list[dict[str, str]]:
        """Load a CSV file with a header row.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of dictionaries, where each dictionary represents a row in the CSV file
        """
        if not file_path.exists():
            return []

        try:
            with open(file_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception:
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
        return self._property_cache[property_name]

    def _generate_record_id(self) -> str:
        """Generate a unique medical record ID."""
        return f"MR-{random.randint(10000000, 99999999)}"

    def _generate_patient_id(self) -> str:
        """Generate a patient ID."""
        return f"P-{random.randint(10000000, 99999999)}"

    def _generate_doctor_id(self) -> str:
        """Generate a doctor ID."""
        return f"DR-{random.randint(10000000, 99999999)}"

    def _generate_date(self) -> str:
        """Generate a date for the medical record."""
        # Generate a date within the last 2 years
        days_ago = random.randint(0, 2 * 365)
        record_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        return record_date.strftime("%Y-%m-%d")

    def _generate_visit_type(self) -> str:
        """Generate a visit type."""
        visit_types = self._DATA_CACHE.get("visit_types", [])
        if not visit_types:
            return "Regular Checkup"
        return random.choice(visit_types)

    def _generate_chief_complaint(self) -> str:
        """Generate a chief complaint."""
        chief_complaints = self._DATA_CACHE.get("chief_complaints", [])
        if not chief_complaints:
            return "Routine checkup"
        return random.choice(chief_complaints)

    def _generate_vital_signs(self) -> dict[str, Any]:
        """Generate vital signs."""
        # Generate random vital signs within normal ranges
        temperature = round(random.uniform(97.0, 99.5), 1)  # Fahrenheit
        systolic = random.randint(100, 140)
        diastolic = random.randint(60, 90)
        heart_rate = random.randint(60, 100)
        respiratory_rate = random.randint(12, 20)
        oxygen_saturation = random.randint(95, 100)
        height = round(random.uniform(150, 190), 1)  # cm
        weight = round(random.uniform(50, 100), 1)  # kg
        bmi = round(weight / ((height / 100) ** 2), 1)

        return {
            "temperature": f"{temperature} °F",
            "blood_pressure": f"{systolic}/{diastolic} mmHg",
            "heart_rate": f"{heart_rate} bpm",
            "respiratory_rate": f"{respiratory_rate} breaths/min",
            "oxygen_saturation": f"{oxygen_saturation}%",
            "height": f"{height} cm",
            "weight": f"{weight} kg",
            "bmi": str(bmi),
        }

    def _generate_diagnosis(self) -> list[dict[str, str]]:
        """Generate diagnoses."""
        diagnosis_codes = self._DATA_CACHE.get("diagnosis_codes", [])
        if not diagnosis_codes:
            # Fallback if no diagnosis codes are loaded
            return [
                {
                    "code": "I10",
                    "description": "Essential (primary) hypertension",
                    "type": "ICD-10",
                }
            ]

        # Generate 1-3 diagnoses
        num_diagnoses = random.randint(1, 3)
        diagnoses = []

        # Select random diagnoses from the loaded data
        selected_diagnoses = random.sample(diagnosis_codes, min(num_diagnoses, len(diagnosis_codes)))

        for diagnosis in selected_diagnoses:
            diagnoses.append(
                {
                    "code": diagnosis["code"],
                    "description": diagnosis["description"],
                    "type": diagnosis["type"],
                }
            )

        return diagnoses

    def _generate_procedures(self) -> list[dict[str, str]]:
        """Generate procedures."""
        procedure_codes = self._DATA_CACHE.get("procedure_codes", [])
        if not procedure_codes:
            # Fallback if no procedure codes are loaded
            return [
                {
                    "code": "99213",
                    "description": (
                        "Office or other outpatient visit for the evaluation and management "
                        "of an established patient"
                    ),
                    "date": self.date,
                }
            ]

        # Generate 0-2 procedures
        num_procedures = random.randint(0, 2)
        if num_procedures == 0:
            return []

        procedures = []

        # Select random procedures from the loaded data
        selected_procedures = random.sample(procedure_codes, min(num_procedures, len(procedure_codes)))

        for procedure in selected_procedures:
            # Generate a date on or before the record date
            record_date = datetime.datetime.strptime(self.date, "%Y-%m-%d")
            days_before = random.randint(0, 7)  # Within a week of the record date
            procedure_date = record_date - datetime.timedelta(days=days_before)

            procedures.append(
                {
                    "code": procedure["code"],
                    "description": procedure["description"],
                    "date": procedure_date.strftime("%Y-%m-%d"),
                }
            )

        return procedures

    def _generate_medications(self) -> list[dict[str, str]]:
        """Generate medications."""
        medications_data = self._DATA_CACHE.get("medications", [])
        if not medications_data:
            # Fallback if no medications are loaded
            return [
                {
                    "name": "Lisinopril",
                    "dosage": "10 mg",
                    "frequency": "Once daily",
                    "route": "Oral",
                    "start_date": self.date,
                    "end_date": "",
                }
            ]

        # Generate 0-3 medications
        num_medications = random.randint(0, 3)
        if num_medications == 0:
            return []

        medications = []

        # Select random medications from the loaded data
        selected_medications = random.sample(medications_data, min(num_medications, len(medications_data)))

        for medication in selected_medications:
            # Generate start date (on or before the record date)
            record_date = datetime.datetime.strptime(self.date, "%Y-%m-%d")
            days_before = random.randint(0, 30)  # Within a month of the record date
            start_date = record_date - datetime.timedelta(days=days_before)

            # Generate end date (50% chance of having an end date)
            end_date = ""
            if random.random() < 0.5:
                days_after = random.randint(7, 90)  # 1 week to 3 months after start date
                end_date = (start_date + datetime.timedelta(days=days_after)).strftime("%Y-%m-%d")

            medications.append(
                {
                    "name": medication["name"],
                    "dosage": medication["dosage"],
                    "frequency": medication["frequency"],
                    "route": medication["route"],
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date,
                }
            )

        return medications

    def _generate_lab_results(self) -> list[dict[str, str]]:
        """Generate lab results."""
        lab_tests = self._DATA_CACHE.get("lab_tests", [])
        specimen_types = self._DATA_CACHE.get("specimen_types", [])
        labs = self._DATA_CACHE.get("labs", [])

        if not lab_tests or not specimen_types:
            # Fallback if no lab tests are loaded
            return [
                {
                    "test_name": "Complete Blood Count",
                    "result": "Normal",
                    "unit": "",
                    "reference_range": "Normal",
                    "date": self.date,
                }
            ]

        # Generate 0-3 lab results
        num_lab_results = random.randint(0, 3)
        if num_lab_results == 0:
            return []

        lab_results = []

        # Select random lab tests from the loaded data
        selected_lab_tests = random.sample(lab_tests, min(num_lab_results, len(lab_tests)))

        # Select a random lab
        lab = random.choice(labs) if labs else {"name": "Quest Diagnostics"}

        for lab_test in selected_lab_tests:
            # Generate result date (on or before the record date)
            record_date = datetime.datetime.strptime(self.date, "%Y-%m-%d")
            days_before = random.randint(0, 7)  # Within a week of the record date
            result_date = record_date - datetime.timedelta(days=days_before)

            # Generate result value
            # For simplicity, we'll generate a random value within the reference range
            reference_range = lab_test.get("reference_range", "")
            unit = lab_test.get("unit", "")

            # Parse reference range to generate a realistic value
            result = self._generate_lab_value(reference_range, unit)

            # Select a random specimen type
            specimen_type = random.choice(specimen_types) if specimen_types else "Blood"

            lab_results.append(
                {
                    "test_name": lab_test["test_name"],
                    "result": result,
                    "unit": unit,
                    "reference_range": reference_range,
                    "date": result_date.strftime("%Y-%m-%d"),
                    "specimen_type": specimen_type,
                    "lab_name": lab.get("name", "Quest Diagnostics"),
                }
            )

        return lab_results

    def _generate_lab_value(self, reference_range: str, unit: str) -> str:
        """Generate a lab value based on the reference range.

        Args:
            reference_range: The reference range for the lab test
            unit: The unit for the lab test

        Returns:
            A string representing a lab value
        """
        # Handle special cases
        if reference_range == "See individual components" or not reference_range:
            return "Normal"

        if reference_range.startswith("<"):
            # For values with upper limit only (e.g., "<200")
            try:
                upper_limit = float(reference_range[1:])
                return str(round(random.uniform(upper_limit * 0.5, upper_limit * 0.9), 1))
            except ValueError:
                return "Normal"

        if reference_range.startswith(">"):
            # For values with lower limit only (e.g., ">40")
            try:
                lower_limit = float(reference_range[1:])
                return str(round(random.uniform(lower_limit * 1.1, lower_limit * 1.5), 1))
            except ValueError:
                return "Normal"

        if ";" in reference_range:
            # For gender-specific ranges (e.g., "Male: 13.5-17.5; Female: 12.0-15.5")
            gender = random.choice(["Male", "Female"])
            if "Male" in reference_range and "Female" in reference_range:
                if gender == "Male":
                    range_part = reference_range.split(";")[0].replace("Male:", "").strip()
                else:
                    range_part = reference_range.split(";")[1].replace("Female:", "").strip()

                if "-" in range_part:
                    try:
                        lower, upper = map(float, range_part.split("-"))
                        return str(round(random.uniform(lower, upper), 1))
                    except ValueError:
                        return "Normal"

            return "Normal"

        if "-" in reference_range:
            # For simple ranges (e.g., "13.5-17.5")
            try:
                lower, upper = map(float, reference_range.split("-"))
                return str(round(random.uniform(lower, upper), 1))
            except ValueError:
                return "Normal"

        # Default case
        return "Normal"

    def _generate_allergies(self) -> list[dict[str, str]]:
        """Generate allergies."""
        allergies_data = self._DATA_CACHE.get("allergies", [])
        if not allergies_data:
            # Fallback if no allergies are loaded
            return [
                {
                    "allergen": "Penicillin",
                    "severity": "Moderate",
                    "reaction": "Rash",
                }
            ]

        # Generate 0-2 allergies
        num_allergies = random.randint(0, 2)
        if num_allergies == 0:
            return []

        allergies = []

        # Select random allergies from the loaded data
        selected_allergies = random.sample(allergies_data, min(num_allergies, len(allergies_data)))

        for allergy in selected_allergies:
            allergies.append(
                {
                    "allergen": allergy["allergen"],
                    "severity": allergy["severity"],
                    "reaction": allergy["reaction"],
                }
            )

        return allergies

    def _generate_assessment(self) -> str:
        """Generate an assessment."""
        # Generate an assessment based on the diagnoses
        diagnoses = self.diagnosis
        if not diagnoses:
            return "No significant findings."

        assessment_parts = []
        for diagnosis in diagnoses:
            description = diagnosis.get("description", "")
            if description:
                assessment_parts.append(f"{description}.")

        if not assessment_parts:
            return "No significant findings."

        # Add a general statement
        general_statements = [
            "Patient is stable.",
            "Patient is improving.",
            "Patient requires follow-up.",
            "Patient requires medication adjustment.",
            "Patient requires further testing.",
            "Patient requires specialist referral.",
        ]

        assessment = " ".join(assessment_parts) + " " + random.choice(general_statements)
        return assessment

    def _generate_plan(self) -> str:
        """Generate a plan."""
        # Generate a plan based on the diagnoses, procedures, and medications
        procedures = self.procedures
        medications = self.medications

        plan_parts = []

        # Add medication plans
        if medications:
            medication_plans = []
            for medication in medications:
                name = medication.get("name", "")
                dosage = medication.get("dosage", "")
                frequency = medication.get("frequency", "")
                if name:
                    medication_plans.append(f"Continue {name} {dosage} {frequency}.")

            if medication_plans:
                plan_parts.append("Medications: " + " ".join(medication_plans))

        # Add procedure plans
        if procedures:
            procedure_plans = []
            for procedure in procedures:
                description = procedure.get("description", "")
                if description:
                    procedure_plans.append(f"Completed {description}.")

            if procedure_plans:
                plan_parts.append("Procedures: " + " ".join(procedure_plans))

        # Add follow-up plan
        follow_up_plans = [
            "Follow up in 1 week.",
            "Follow up in 2 weeks.",
            "Follow up in 1 month.",
            "Follow up in 3 months.",
            "Follow up in 6 months.",
            "Follow up in 1 year.",
            "Follow up as needed.",
        ]

        plan_parts.append("Follow-up: " + random.choice(follow_up_plans))

        # Add additional recommendations
        additional_recommendations = [
            "Maintain healthy diet and exercise.",
            "Monitor symptoms and report any changes.",
            "Complete all prescribed medications.",
            "Avoid alcohol and tobacco.",
            "Get adequate rest and hydration.",
            "Manage stress through relaxation techniques.",
        ]

        plan_parts.append("Recommendations: " + random.choice(additional_recommendations))

        return " ".join(plan_parts)

    def _generate_follow_up(self) -> dict[str, str]:
        """Generate follow-up information."""
        # Generate a follow-up date based on the record date
        record_date = datetime.datetime.strptime(self.date, "%Y-%m-%d")

        # Determine follow-up interval
        intervals = [7, 14, 30, 90, 180, 365]  # days
        interval = random.choice(intervals)

        follow_up_date = record_date + datetime.timedelta(days=interval)

        # Generate follow-up instructions
        instructions = [
            f"Return to clinic in {interval // 7} weeks for follow-up.",
            f"Schedule follow-up appointment in {interval // 30} months.",
            "Call if symptoms worsen before next appointment.",
            "Bring medication list to next appointment.",
            "Complete lab work 1 week before next appointment.",
            "Continue current treatment plan until next visit.",
        ]

        return {
            "date": follow_up_date.strftime("%Y-%m-%d"),
            "instructions": random.choice(instructions),
        }

    def _generate_notes(self) -> str:
        """Generate additional notes."""
        # Generate additional notes (50% chance of having notes)
        if random.random() < 0.5:
            return ""

        notes_options = [
            "Patient expressed concern about medication side effects.",
            "Patient reports improved symptoms since last visit.",
            "Patient was accompanied by family member.",
            "Patient requested refill of current medications.",
            "Patient has been compliant with treatment plan.",
            "Patient missed previous appointment due to illness.",
            "Patient has questions about test results.",
            "Patient is considering alternative treatments.",
            "Patient reports difficulty affording medications.",
            "Patient is planning to travel internationally next month.",
        ]

        return random.choice(notes_options)

    def reset(self) -> None:
        """Reset all field generators and caches."""
        for generator in self._field_generators.values():
            generator.reset()

        # Reset person entities
        self._patient_entity.reset()
        self._doctor_entity.reset()

        # Clear property cache
        self._property_cache.clear()

    @property
    def record_id(self) -> str:
        """Get the record ID."""
        return self._get_cached_property("record_id", lambda: self._field_generators["record_id"].get())

    @property
    def patient_id(self) -> str:
        """Get the patient ID."""
        return self._get_cached_property("patient_id", lambda: self._field_generators["patient_id"].get())

    @property
    def doctor_id(self) -> str:
        """Get the doctor ID."""
        return self._get_cached_property("doctor_id", lambda: self._field_generators["doctor_id"].get())

    @property
    def date(self) -> str:
        """Get the record date."""
        return self._get_cached_property("date", lambda: self._field_generators["date"].get())

    @property
    def visit_type(self) -> str:
        """Get the visit type."""
        return self._get_cached_property("visit_type", lambda: self._field_generators["visit_type"].get())

    @property
    def chief_complaint(self) -> str:
        """Get the chief complaint."""
        return self._get_cached_property("chief_complaint", lambda: self._field_generators["chief_complaint"].get())

    @property
    def vital_signs(self) -> dict[str, Any]:
        """Get the vital signs."""
        return self._get_cached_property("vital_signs", lambda: self._field_generators["vital_signs"].get())

    @property
    def diagnosis(self) -> list[dict[str, str]]:
        """Get the diagnoses."""
        return self._get_cached_property("diagnosis", lambda: self._field_generators["diagnosis"].get())

    @property
    def procedures(self) -> list[dict[str, str]]:
        """Get the procedures."""
        return self._get_cached_property("procedures", lambda: self._field_generators["procedures"].get())

    @property
    def medications(self) -> list[dict[str, str]]:
        """Get the medications."""
        return self._get_cached_property("medications", lambda: self._field_generators["medications"].get())

    @property
    def lab_results(self) -> list[dict[str, str]]:
        """Get the lab results."""
        return self._get_cached_property("lab_results", lambda: self._field_generators["lab_results"].get())

    @property
    def allergies(self) -> list[dict[str, str]]:
        """Get the allergies."""
        return self._get_cached_property("allergies", lambda: self._field_generators["allergies"].get())

    @property
    def assessment(self) -> str:
        """Get the assessment."""
        return self._get_cached_property("assessment", lambda: self._field_generators["assessment"].get())

    @property
    def plan(self) -> str:
        """Get the plan."""
        return self._get_cached_property("plan", lambda: self._field_generators["plan"].get())

    @property
    def follow_up(self) -> dict[str, str]:
        """Get the follow-up information."""
        return self._get_cached_property("follow_up", lambda: self._field_generators["follow_up"].get())

    @property
    def notes(self) -> str:
        """Get the additional notes."""
        return self._get_cached_property("notes", lambda: self._field_generators["notes"].get())

    @property
    def patient_name(self) -> str:
        """Get the patient name."""
        return f"{self._patient_entity.given_name} {self._patient_entity.family_name}"

    @property
    def doctor_name(self) -> str:
        """Get the doctor name."""
        return f"{self._doctor_entity.given_name} {self._doctor_entity.family_name}"

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
        records = []

        for _ in range(count):
            # Reset for a new record
            self.reset()

            # Generate a new record
            record = self.to_dict()
            records.append(record)

        return records
