# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime  # Added for medical appointment generator
import json  # Added for PatientHistoryGenerator
import random
from typing import cast

from datamimic_ce.generators.generator import Generator

# Healthcare Generators


class DiagnosisGenerator(Generator):
    """Generate ICD-10 codes and descriptions for medical diagnoses."""

    def __init__(self, code_only: bool = False, category: str | None = None):
        """
        Initialize DiagnosisGenerator.

        Args:
            code_only (bool): Return only the ICD-10 code without description
            category (str): Optional category of diagnoses ('cardiac', 'respiratory', 'endocrine', etc.)
        """
        self._code_only = code_only
        self._category = category
        # Common ICD-10 codes with descriptions
        self._diagnoses = {
            "cardiac": [
                ("I21.0", "Acute ST elevation myocardial infarction of anterior wall"),
                ("I20.9", "Angina pectoris, unspecified"),
                ("I50.9", "Heart failure, unspecified"),
                ("I48.91", "Unspecified atrial fibrillation"),
                ("I10", "Essential (primary) hypertension"),
            ],
            "respiratory": [
                ("J44.9", "Chronic obstructive pulmonary disease, unspecified"),
                ("J45.909", "Unspecified asthma, uncomplicated"),
                ("J18.9", "Pneumonia, unspecified organism"),
                ("J40", "Bronchitis, not specified as acute or chronic"),
                ("J11.1", "Influenza with other respiratory manifestations"),
            ],
            "endocrine": [
                ("E11.9", "Type 2 diabetes mellitus without complications"),
                ("E03.9", "Hypothyroidism, unspecified"),
                ("E05.90", "Hyperthyroidism, unspecified"),
                ("E66.9", "Obesity, unspecified"),
                ("E21.0", "Primary hyperparathyroidism"),
            ],
            "neurological": [
                ("G40.909", "Epilepsy, unspecified, not intractable"),
                ("G43.909", "Migraine, unspecified"),
                ("G20", "Parkinson's disease"),
                ("G30.9", "Alzheimer's disease, unspecified"),
                ("G35", "Multiple sclerosis"),
            ],
            "musculoskeletal": [
                ("M54.5", "Low back pain"),
                ("M17.9", "Osteoarthritis of knee, unspecified"),
                ("M19.90", "Unspecified osteoarthritis, unspecified site"),
                ("M81.0", "Age-related osteoporosis"),
                ("M25.50", "Pain in unspecified joint"),
            ],
        }

    def generate(self) -> str:
        # Select category
        category = self._category if self._category else random.choice(list(self._diagnoses.keys()))
        # Select diagnosis from category
        code, description = random.choice(self._diagnoses[category])
        return code if self._code_only else f"{code} - {description}"


class VitalSignsGenerator(Generator):
    """Generate realistic vital signs with optional abnormal ranges."""

    def __init__(self, vital_type: str | None = None, abnormal: bool = False):
        """
        Initialize VitalSignsGenerator.

        Args:
            vital_type (str): Specific vital sign to generate ('bp', 'temp', 'pulse', 'resp', 'spo2')
            abnormal (bool): Generate abnormal values outside normal ranges
        """
        self._vital_type = vital_type.lower() if vital_type else None
        self._abnormal = abnormal
        # Normal ranges for vital signs
        self._ranges: dict[str, dict[str, tuple[int, int] | tuple[float, float] | tuple[int, int, int, int]]] = {
            "bp": {"normal": (90, 120, 60, 80), "abnormal": (70, 200, 40, 120)},  # (sys_min, sys_max, dia_min, dia_max)
            "temp": {"normal": (36.1, 37.2), "abnormal": (34.0, 40.0)},  # Celsius
            "pulse": {"normal": (60, 100), "abnormal": (40, 150)},  # beats per minute
            "resp": {"normal": (12, 20), "abnormal": (8, 40)},  # breaths per minute
            "spo2": {"normal": (95, 100), "abnormal": (85, 100)},  # oxygen saturation percentage
        }

    def _generate_bp(self) -> str:
        range_type = "abnormal" if self._abnormal else "normal"
        range_values = self._ranges["bp"][range_type]
        sys_min, sys_max, dia_min, dia_max = cast(tuple[int, int, int, int], range_values)
        systolic = random.randint(sys_min, sys_max)
        diastolic = random.randint(dia_min, dia_max)
        return f"{systolic}/{diastolic} mmHg"

    def _generate_temp(self) -> str:
        range_type = "abnormal" if self._abnormal else "normal"
        range_values = self._ranges["temp"][range_type]
        min_temp, max_temp = cast(tuple[float, float], range_values)
        temp = round(random.uniform(min_temp, max_temp), 1)
        return f"{temp}°C"

    def _generate_vital(self, vital_type: str) -> str:
        range_type = "abnormal" if self._abnormal else "normal"
        range_values = self._ranges[vital_type][range_type]

        # Handle blood pressure separately as it has 4 values
        if vital_type == "bp":
            sys_min, sys_max, dia_min, dia_max = cast(tuple[int, int, int, int], range_values)
            systolic = random.randint(sys_min, sys_max)
            diastolic = random.randint(dia_min, dia_max)
            return f"{systolic}/{diastolic} mmHg"
        else:
            # For other vitals that have 2 values
            min_val, max_val = cast(tuple[int | float, int | float], range_values)
            if isinstance(min_val, float) or isinstance(max_val, float):
                value = round(random.uniform(float(min_val), float(max_val)), 1)
            else:
                value = random.randint(int(min_val), int(max_val))
            units = {"pulse": "bpm", "resp": "breaths/min", "spo2": "%"}
            return f"{value} {units.get(vital_type, '')}"

    def generate(self) -> str:
        if not self._vital_type or self._vital_type not in self._ranges:
            self._vital_type = random.choice(list(self._ranges.keys()))

        if self._vital_type == "bp":
            return self._generate_bp()
        elif self._vital_type == "temp":
            return self._generate_temp()
        else:
            return self._generate_vital(self._vital_type)


class MedicationGenerator(Generator):
    """Generate medication names with dosages and frequencies."""

    def __init__(self, category: str | None = None, include_dosage: bool = True):
        """
        Initialize MedicationGenerator.

        Args:
            category (str): Optional medication category ('cardiac', 'antibiotic', 'analgesic', etc.)
            include_dosage (bool): Include dosage and frequency information
        """
        self._category = category
        self._include_dosage = include_dosage
        # Common medications by category with typical dosages
        self._medications = {
            "cardiac": [
                ("Metoprolol", "25-100 mg", "twice daily"),
                ("Lisinopril", "10-40 mg", "daily"),
                ("Amlodipine", "5-10 mg", "daily"),
                ("Atorvastatin", "10-80 mg", "daily"),
                ("Warfarin", "2-10 mg", "daily"),
            ],
            "antibiotic": [
                ("Amoxicillin", "500 mg", "three times daily"),
                ("Azithromycin", "500 mg", "daily"),
                ("Ciprofloxacin", "500 mg", "twice daily"),
                ("Doxycycline", "100 mg", "twice daily"),
                ("Cephalexin", "500 mg", "four times daily"),
            ],
            "analgesic": [
                ("Ibuprofen", "400-800 mg", "every 6-8 hours"),
                ("Acetaminophen", "500-1000 mg", "every 4-6 hours"),
                ("Naproxen", "250-500 mg", "twice daily"),
                ("Tramadol", "50-100 mg", "every 4-6 hours"),
                ("Morphine", "15-30 mg", "every 4 hours"),
            ],
            "respiratory": [
                ("Albuterol", "2 puffs", "every 4-6 hours as needed"),
                ("Fluticasone", "1-2 sprays", "twice daily"),
                ("Montelukast", "10 mg", "daily"),
                ("Tiotropium", "18 mcg", "daily"),
                ("Budesonide", "180 mcg", "twice daily"),
            ],
            "psychiatric": [
                ("Sertraline", "50-200 mg", "daily"),
                ("Fluoxetine", "20-80 mg", "daily"),
                ("Alprazolam", "0.25-1 mg", "three times daily"),
                ("Quetiapine", "25-800 mg", "daily"),
                ("Lithium", "300-900 mg", "twice daily"),
            ],
        }

    def generate(self) -> str:
        # Select category
        category = self._category if self._category else random.choice(list(self._medications.keys()))
        # Select medication from category
        medication, dosage, frequency = random.choice(self._medications[category])
        return medication if not self._include_dosage else f"{medication} {dosage} {frequency}"


class LabResultGenerator(Generator):
    """Generate laboratory test results with reference ranges."""

    def __init__(self, test_type: str | None = None, abnormal: bool = False):
        """
        Initialize LabResultGenerator.

        Args:
            test_type (str): Specific test type to generate
            abnormal (bool): Generate abnormal values outside reference ranges
        """
        self._test_type = test_type
        self._abnormal = abnormal
        # Common lab tests with reference ranges and units
        self._lab_tests = {
            "cbc": {
                "Hemoglobin": {"range": (12.0, 16.0), "abnormal": (8.0, 20.0), "unit": "g/dL"},
                "WBC": {"range": (4.5, 11.0), "abnormal": (2.0, 30.0), "unit": "K/µL"},
                "Platelets": {"range": (150, 450), "abnormal": (50, 1000), "unit": "K/µL"},
            },
            "metabolic": {
                "Glucose": {"range": (70, 100), "abnormal": (40, 400), "unit": "mg/dL"},
                "Creatinine": {"range": (0.6, 1.2), "abnormal": (0.3, 8.0), "unit": "mg/dL"},
                "Sodium": {"range": (135, 145), "abnormal": (120, 160), "unit": "mEq/L"},
                "Potassium": {"range": (3.5, 5.0), "abnormal": (2.5, 7.0), "unit": "mEq/L"},
            },
            "lipids": {
                "Total Cholesterol": {"range": (150, 200), "abnormal": (100, 400), "unit": "mg/dL"},
                "HDL": {"range": (40, 60), "abnormal": (20, 100), "unit": "mg/dL"},
                "LDL": {"range": (70, 130), "abnormal": (50, 250), "unit": "mg/dL"},
                "Triglycerides": {"range": (50, 150), "abnormal": (30, 500), "unit": "mg/dL"},
            },
            "thyroid": {
                "TSH": {"range": (0.4, 4.0), "abnormal": (0.01, 20.0), "unit": "mIU/L"},
                "T4": {"range": (5.0, 12.0), "abnormal": (1.0, 25.0), "unit": "µg/dL"},
                "T3": {"range": (80, 200), "abnormal": (40, 400), "unit": "ng/dL"},
            },
            "liver": {
                "ALT": {"range": (7, 56), "abnormal": (5, 1000), "unit": "U/L"},
                "AST": {"range": (10, 40), "abnormal": (5, 1000), "unit": "U/L"},
                "Bilirubin": {"range": (0.3, 1.2), "abnormal": (0.1, 15.0), "unit": "mg/dL"},
                "Albumin": {"range": (3.4, 5.4), "abnormal": (1.0, 7.0), "unit": "g/dL"},
            },
        }

    def _generate_value(self, test_info: dict) -> float:
        range_key = "abnormal" if self._abnormal else "range"
        min_val, max_val = test_info[range_key]
        # Use appropriate precision based on the range values
        precision = 1 if max_val - min_val < 10 else 0
        return round(random.uniform(min_val, max_val), precision)

    def generate(self) -> str:
        # Select test category
        category = (
            self._test_type if self._test_type in self._lab_tests else random.choice(list(self._lab_tests.keys()))
        )
        # Select specific test from category
        test_name = random.choice(list(self._lab_tests[category].keys()))
        test_info = self._lab_tests[category][test_name]

        # Generate value
        value = self._generate_value(test_info)

        # Format result with reference range
        ref_range = f"({test_info['range'][0]}-{test_info['range'][1]} {test_info['unit']})"
        return f"{test_name}: {value} {test_info['unit']} {ref_range}"


class MedicalProcedureGenerator(Generator):
    """Generate CPT codes and medical procedures."""

    def __init__(self, category: str | None = None, code_only: bool = False):
        """
        Initialize MedicalProcedureGenerator.

        Args:
            category (str): Optional procedure category
            code_only (bool): Return only the CPT code without description
        """
        self._category = category
        self._code_only = code_only
        # Common CPT codes with descriptions by category
        self._procedures = {
            "evaluation": [
                ("99213", "Office visit, established patient, low to moderate severity"),
                ("99214", "Office visit, established patient, moderate to high severity"),
                ("99203", "Office visit, new patient, low severity"),
                ("99204", "Office visit, new patient, moderate severity"),
                ("99285", "Emergency department visit, high severity"),
            ],
            "surgical": [
                ("43239", "Upper GI endoscopy, diagnostic"),
                ("45378", "Colonoscopy, diagnostic"),
                ("47562", "Laparoscopic cholecystectomy"),
                ("49505", "Inguinal hernia repair"),
                ("27447", "Total knee arthroplasty"),
            ],
            "diagnostic": [
                ("71045", "Chest X-ray, single view"),
                ("71046", "Chest X-ray, 2 views"),
                ("70450", "CT head/brain without contrast"),
                ("93000", "Electrocardiogram, complete"),
                ("93306", "Echocardiogram with doppler"),
            ],
            "therapeutic": [
                ("97110", "Therapeutic exercises"),
                ("97140", "Manual therapy techniques"),
                ("97530", "Therapeutic activities"),
                ("97112", "Neuromuscular reeducation"),
                ("97116", "Gait training therapy"),
            ],
        }

    def generate(self) -> str:
        # Select category
        category = self._category if self._category else random.choice(list(self._procedures.keys()))
        # Select procedure from category
        code, description = random.choice(self._procedures[category])
        return code if self._code_only else f"{code} - {description}"


# Additional Healthcare Generators


class AllergyGenerator(Generator):
    """Generate common allergy information with optional reaction details."""

    def __init__(self, include_reaction: bool = True):
        """
        Initialize AllergyGenerator.

        Args:
            include_reaction (bool): Whether to include reaction details
        """
        self._include_reaction = include_reaction
        self._allergens = [
            "Peanuts",
            "Shellfish",
            "Milk",
            "Eggs",
            "Wheat",
            "Soy",
            "Tree Nuts",
            "Pollen",
            "Dust Mites",
            "Latex",
        ]
        self._reactions = [
            "Mild: Sneezing",
            "Moderate: Rash",
            "Severe: Anaphylaxis",
            "Mild: Itchy eyes",
            "Moderate: Hives",
        ]

    def generate(self) -> str:
        allergen = random.choice(self._allergens)
        if self._include_reaction:
            reaction = random.choice(self._reactions)
            return f"{allergen} - {reaction}"
        return allergen


class ImmunizationGenerator(Generator):
    """Generate immunization/vaccine records with optional administration date and booster info."""

    def __init__(self, include_date: bool = True, include_booster: bool = False):
        """
        Initialize ImmunizationGenerator.

        Args:
            include_date (bool): Whether to include the administration date
            include_booster (bool): Whether to include booster information
        """
        self._include_date = include_date
        self._include_booster = include_booster
        self._vaccines = [
            "Influenza Vaccine",
            "COVID-19 Vaccine (Pfizer)",
            "COVID-19 Vaccine (Moderna)",
            "Hepatitis B Vaccine",
            "MMR Vaccine",
            "Varicella Vaccine",
            "Tetanus Booster",
        ]

    def generate(self) -> str:
        vaccine = random.choice(self._vaccines)
        date_part = ""
        booster_part = ""
        if self._include_date:
            # Generate a random date within the past 5 years
            start_year = datetime.date.today().year - 5
            year = random.randint(start_year, datetime.date.today().year)
            month = random.randint(1, 12)
            day = random.randint(1, 28)  # simplified
            date_part = f" - Administered on {year:04d}-{month:02d}-{day:02d}"
        if self._include_booster:
            booster = random.choice(["First Dose", "Second Dose", "Booster"])
            booster_part = f", {booster}"
        return f"{vaccine}{booster_part}{date_part}"


class MedicalAppointmentGenerator(Generator):
    """Generate future medical appointment details including date, optional time, and department."""

    def __init__(self, include_time: bool = True):
        """
        Initialize MedicalAppointmentGenerator.

        Args:
            include_time (bool): Whether to include appointment time
        """
        self._include_time = include_time
        self._departments = [
            "Cardiology",
            "Dermatology",
            "Neurology",
            "Orthopedics",
            "Pediatrics",
            "General Medicine",
            "Oncology",
            "Gynecology",
        ]

    def generate(self) -> str:
        # Generate a future date within the next 90 days
        days_ahead = random.randint(1, 90)
        appointment_date = datetime.date.today() + datetime.timedelta(days=days_ahead)
        time_part = ""
        if self._include_time:
            # Generate a random time between 08:00 and 17:00
            hour = random.randint(8, 16)
            minute = random.choice([0, 15, 30, 45])
            time_part = f" {hour:02d}:{minute:02d}"
        department = random.choice(self._departments)
        return f"Appointment on {appointment_date}{time_part} - {department}"


# Additional Innovative Healthcare Generators


class SymptomGenerator(Generator):
    """Generate a list of common symptoms for a given disease category."""

    def __init__(self, disease_category: str | None = None, number_of_symptoms: int = 3):
        """
        Initialize SymptomGenerator.

        Args:
            disease_category (str): Optional disease category ('respiratory', 'cardiac', 'neurological', 'gastrointestinal', or 'general')
            number_of_symptoms (int): Number of symptoms to generate
        """
        self._disease_category = disease_category
        self._number = number_of_symptoms
        self._symptoms = {
            "respiratory": ["cough", "shortness of breath", "chest tightness", "wheezing", "sore throat"],
            "cardiac": ["chest pain", "palpitations", "shortness of breath", "dizziness"],
            "neurological": ["headache", "seizures", "numbness", "confusion"],
            "gastrointestinal": ["nausea", "vomiting", "diarrhea", "abdominal pain"],
            "general": ["fever", "fatigue", "malaise", "weight loss"],
        }

    def generate(self) -> str:
        # Choose category; if none or not found, use 'general'
        category = (
            self._disease_category.lower()
            if self._disease_category and self._disease_category.lower() in self._symptoms
            else "general"
        )
        symptoms_available = self._symptoms[category]
        count = min(self._number, len(symptoms_available))
        selected = random.sample(symptoms_available, count)
        return ", ".join(selected)


class PatientHistoryGenerator(Generator):
    """Generate a synthetic patient history record including diagnosis, allergies, medications, lab results, immunizations, and upcoming appointments."""

    def __init__(
        self, include_allergies: bool = True, include_immunizations: bool = True, include_appointments: bool = True
    ):
        """
        Initialize PatientHistoryGenerator.

        Args:
            include_allergies (bool): Whether to include allergy information
            include_immunizations (bool): Whether to include immunization records
            include_appointments (bool): Whether to include upcoming appointment details
        """
        self._include_allergies = include_allergies
        self._include_immunizations = include_immunizations
        self._include_appointments = include_appointments
        # Initialize constituent generators
        self._diagnosis_gen = DiagnosisGenerator()
        self._allergy_gen = AllergyGenerator()
        self._medication_gen = MedicationGenerator()
        self._lab_result_gen = LabResultGenerator()
        self._immunization_gen = ImmunizationGenerator()
        self._appointment_gen = MedicalAppointmentGenerator()

    def generate(self) -> str:
        history = {}
        history["Diagnosis"] = self._diagnosis_gen.generate()
        if self._include_allergies:
            history["Allergies"] = self._allergy_gen.generate()
        history["Medications"] = self._medication_gen.generate()
        history["Lab Results"] = self._lab_result_gen.generate()
        if self._include_immunizations:
            history["Immunizations"] = self._immunization_gen.generate()
        if self._include_appointments:
            history["Next Appointment"] = self._appointment_gen.generate()
        return json.dumps(history, indent=2)
