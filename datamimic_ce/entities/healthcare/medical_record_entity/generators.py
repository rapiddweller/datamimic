# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Medical Record Entity Generators.

This module provides specialized generators for medical record data.
"""

import random

from datamimic_ce.entities.healthcare.medical_record_entity.data_loader import MedicalRecordDataLoader
from datamimic_ce.logger import logger


class DiagnosisGenerator:
    """Generator for diagnosis data."""

    def __init__(self, data_loader: MedicalRecordDataLoader, data_generation_util):
        """Initialize the DiagnosisGenerator.

        Args:
            data_loader: The data loader to use for retrieving diagnosis codes.
            data_generation_util: Utility for data generation.
        """
        self._data_loader = data_loader
        self._data_generation_util = data_generation_util

    def generate_diagnosis(self) -> list[dict[str, str]]:
        """Generate diagnosis data.

        Returns:
            A list of dictionaries containing diagnosis codes and descriptions.
        """
        diagnosis_codes = self._data_loader.get_diagnosis_codes()
        if not diagnosis_codes:
            logger.error("No diagnosis codes found in data cache. Please create a data file.")
            return [{"code": "Unknown", "description": "Unknown Diagnosis"}]

        # Determine number of diagnoses (1-3)
        num_diagnoses = random.randint(1, 3)
        diagnoses = []

        # Select diagnoses based on weights
        for _ in range(num_diagnoses):
            code_tuple, _ = self._data_generation_util.weighted_choice(diagnosis_codes)
            code, description = code_tuple.split("|", 1) if "|" in code_tuple else (code_tuple, "Unknown Description")
            diagnoses.append({"code": code.strip(), "description": description.strip()})

        return diagnoses


class ProcedureGenerator:
    """Generator for procedure data."""

    def __init__(self, data_loader: MedicalRecordDataLoader, data_generation_util):
        """Initialize the ProcedureGenerator.

        Args:
            data_loader: The data loader to use for retrieving procedure codes.
            data_generation_util: Utility for data generation.
        """
        self._data_loader = data_loader
        self._data_generation_util = data_generation_util

    def generate_procedures(self) -> list[dict[str, str]]:
        """Generate procedure data.

        Returns:
            A list of dictionaries containing procedure codes and descriptions.
        """
        procedure_codes = self._data_loader.get_procedure_codes()
        if not procedure_codes:
            logger.error("No procedure codes found in data cache. Please create a data file.")
            return [{"code": "Unknown", "description": "Unknown Procedure"}]

        # Determine if any procedures were performed (70% chance)
        if random.random() > 0.7:
            return []

        # Determine number of procedures (1-2)
        num_procedures = random.randint(1, 2)
        procedures = []

        # Select procedures based on weights
        for _ in range(num_procedures):
            code_tuple, _ = self._data_generation_util.weighted_choice(procedure_codes)
            code, description = code_tuple.split("|", 1) if "|" in code_tuple else (code_tuple, "Unknown Description")
            procedures.append({"code": code.strip(), "description": description.strip()})

        return procedures


class MedicationGenerator:
    """Generator for medication data."""

    def __init__(self, data_loader: MedicalRecordDataLoader, data_generation_util):
        """Initialize the MedicationGenerator.

        Args:
            data_loader: The data loader to use for retrieving medications.
            data_generation_util: Utility for data generation.
        """
        self._data_loader = data_loader
        self._data_generation_util = data_generation_util

    def generate_medications(self) -> list[dict[str, str]]:
        """Generate medication data.

        Returns:
            A list of dictionaries containing medication information.
        """
        medications = self._data_loader.get_medications()
        if not medications:
            logger.error("No medications found in data cache. Please create a data file.")
            return [{"name": "Unknown Medication", "dosage": "Unknown Dosage", "frequency": "Unknown Frequency"}]

        # Determine if any medications were prescribed (80% chance)
        if random.random() > 0.8:
            return []

        # Determine number of medications (1-3)
        num_medications = random.randint(1, 3)
        med_list = []

        # Select medications based on weights
        for _ in range(num_medications):
            med_info, _ = self._data_generation_util.weighted_choice(medications)

            # Parse medication info if it contains additional details
            parts = med_info.split("|") if "|" in med_info else [med_info]
            name = parts[0].strip()

            # Generate random dosage and frequency if not provided
            dosage = parts[1].strip() if len(parts) > 1 else f"{random.randint(5, 500)} mg"
            frequency = (
                parts[2].strip()
                if len(parts) > 2
                else random.choice(["Once daily", "Twice daily", "Three times daily", "Every 4-6 hours", "As needed"])
            )

            med_list.append({"name": name, "dosage": dosage, "frequency": frequency})

        return med_list


class LabResultGenerator:
    """Generator for lab result data."""

    def __init__(self, data_loader: MedicalRecordDataLoader, data_generation_util):
        """Initialize the LabResultGenerator.

        Args:
            data_loader: The data loader to use for retrieving lab tests.
            data_generation_util: Utility for data generation.
        """
        self._data_loader = data_loader
        self._data_generation_util = data_generation_util

    def generate_lab_results(self) -> list[dict[str, str]]:
        """Generate lab result data.

        Returns:
            A list of dictionaries containing lab result information.
        """
        lab_tests = self._data_loader.get_lab_tests()
        specimen_types = self._data_loader.get_specimen_types()
        labs = self._data_loader.get_labs()

        # Log errors if data is missing
        if not lab_tests:
            logger.error("No lab tests found in data cache. Please create a data file.")
        if not specimen_types:
            logger.error("No specimen types found in data cache. Please create a data file.")
        if not labs:
            logger.error("No labs found in data cache. Please create a data file.")

        # Return empty list if any required data is missing
        if not lab_tests or not specimen_types or not labs:
            return []

        # Determine if any lab tests were ordered (60% chance)
        if random.random() > 0.6:
            return []

        # Determine number of lab tests (1-3)
        num_tests = random.randint(1, 3)
        results = []

        # Generate lab results
        for _ in range(num_tests):
            test, _ = self._data_generation_util.weighted_choice(lab_tests)
            specimen, _ = self._data_generation_util.weighted_choice(specimen_types)
            lab, _ = self._data_generation_util.weighted_choice(labs)

            # Generate random result value and status
            result_value = f"{random.randint(1, 200)}"
            status = random.choice(["Completed", "Pending", "Cancelled"])

            results.append(
                {
                    "test": test,
                    "specimen": specimen,
                    "lab": lab,
                    "result": result_value,
                    "status": status,
                }
            )

        return results


class AllergyGenerator:
    """Generator for allergy data."""

    def __init__(self, data_loader: MedicalRecordDataLoader, data_generation_util):
        """Initialize the AllergyGenerator.

        Args:
            data_loader: The data loader to use for retrieving allergies.
            data_generation_util: Utility for data generation.
        """
        self._data_loader = data_loader
        self._data_generation_util = data_generation_util

    def generate_allergies(self) -> list[dict[str, str]]:
        """Generate allergy data.

        Returns:
            A list of dictionaries containing allergy information.
        """
        allergies = self._data_loader.get_allergies()
        if not allergies:
            logger.error("No allergies found in data cache. Please create a data file.")
            return []

        # Determine if patient has allergies (70% chance)
        if random.random() > 0.7:
            return []

        # Determine number of allergies (1-3)
        num_allergies = random.randint(1, 3)
        allergy_list = []

        # Select allergies based on weights
        for _ in range(num_allergies):
            allergen, _ = self._data_generation_util.weighted_choice(allergies)
            severity = random.choice(["Mild", "Moderate", "Severe"])
            reaction = random.choice(["Rash", "Hives", "Swelling", "Anaphylaxis", "Nausea", "Difficulty breathing"])

            allergy_list.append(
                {
                    "allergen": allergen,
                    "severity": severity,
                    "reaction": reaction,
                }
            )

        return allergy_list


class AssessmentGenerator:
    """Generator for assessment data."""

    def __init__(self, data_generation_util):
        """Initialize the AssessmentGenerator.

        Args:
            data_generation_util: Utility for data generation.
        """
        self._data_generation_util = data_generation_util

    def generate_assessment(self, chief_complaint: str, diagnoses: list[dict[str, str]]) -> str:
        """Generate assessment data.

        Args:
            chief_complaint: The chief complaint.
            diagnoses: The diagnoses.

        Returns:
            A string containing the assessment.
        """
        # Create a template-based assessment
        assessment_parts = [
            f"Patient presents with {chief_complaint}.",
        ]

        # Add diagnosis information
        if diagnoses:
            diagnosis_text = ", ".join([d["description"] for d in diagnoses])
            assessment_parts.append(f"Assessment indicates {diagnosis_text}.")

        # Add random clinical observations
        observations = [
            "Patient appears to be in no acute distress.",
            "Patient is alert and oriented.",
            "Patient is experiencing moderate discomfort.",
            "Patient's symptoms have improved since last visit.",
            "Patient's symptoms have worsened in the past 24 hours.",
            "Patient reports associated symptoms including fatigue and decreased appetite.",
        ]

        assessment_parts.append(random.choice(observations))

        return " ".join(assessment_parts)


class PlanGenerator:
    """Generator for plan data."""

    def __init__(self, data_generation_util):
        """Initialize the PlanGenerator.

        Args:
            data_generation_util: Utility for data generation.
        """
        self._data_generation_util = data_generation_util

    def generate_plan(
        self, procedures: list[dict[str, str]], medications: list[dict[str, str]], lab_results: list[dict[str, str]]
    ) -> str:
        """Generate plan data.

        Args:
            procedures: The procedures.
            medications: The medications.
            lab_results: The lab results.

        Returns:
            A string containing the plan.
        """
        plan_parts = []

        # Add procedure information
        if procedures:
            procedure_text = ", ".join([p["description"] for p in procedures])
            plan_parts.append(f"Procedures: {procedure_text}.")

        # Add medication information
        if medications:
            med_text = ", ".join([f"{m['name']} {m['dosage']} {m['frequency']}" for m in medications])
            plan_parts.append(f"Medications: {med_text}.")

        # Add lab test information
        if lab_results:
            lab_text = ", ".join([l["test"] for l in lab_results])
            plan_parts.append(f"Lab tests: {lab_text}.")

        # Add random treatment recommendations
        recommendations = [
            "Rest and hydration recommended.",
            "Follow up in 2 weeks if symptoms persist.",
            "Avoid strenuous activity for 7 days.",
            "Apply ice to affected area for 20 minutes every 2 hours.",
            "Increase fluid intake.",
            "Monitor symptoms and return if condition worsens.",
        ]

        plan_parts.append(random.choice(recommendations))

        return " ".join(plan_parts) if plan_parts else "No specific treatment plan at this time."


class FollowUpGenerator:
    """Generator for follow-up data."""

    def __init__(self, data_generation_util):
        """Initialize the FollowUpGenerator.

        Args:
            data_generation_util: Utility for data generation.
        """
        self._data_generation_util = data_generation_util

    def generate_follow_up(self) -> dict[str, str]:
        """Generate follow-up data.

        Returns:
            A dictionary containing follow-up information.
        """
        # Determine if follow-up is needed (80% chance)
        if random.random() > 0.8:
            return {"needed": "No", "timeframe": "N/A", "reason": "N/A"}

        # Generate follow-up details
        timeframes = ["1 week", "2 weeks", "1 month", "3 months", "6 months"]
        reasons = [
            "Reassessment of condition",
            "Medication adjustment",
            "Review lab results",
            "Wound check",
            "Monitoring of symptoms",
            "Post-procedure follow-up",
        ]

        return {
            "needed": "Yes",
            "timeframe": random.choice(timeframes),
            "reason": random.choice(reasons),
        }


class NotesGenerator:
    """Generator for clinical notes."""

    def __init__(self, data_generation_util):
        """Initialize the NotesGenerator.

        Args:
            data_generation_util: Utility for data generation.
        """
        self._data_generation_util = data_generation_util

    def generate_notes(self, chief_complaint: str, assessment: str, plan: str) -> str:
        """Generate clinical notes.

        Args:
            chief_complaint: The chief complaint.
            assessment: The assessment.
            plan: The treatment plan.

        Returns:
            A string containing clinical notes.
        """
        # Determine if additional notes are needed (50% chance)
        if random.random() > 0.5:
            return ""

        # Generate additional notes
        note_templates = [
            "Patient was advised on lifestyle modifications including {}.",
            "Patient expressed concerns about {}.",
            "Patient reports history of similar symptoms {} ago.",
            "Patient was counseled on the importance of {}.",
            "Patient's family history includes {}.",
        ]

        note_fillers = [
            "diet and exercise",
            "smoking cessation",
            "medication side effects",
            "cost of treatment",
            "6 months",
            "1 year",
            "medication adherence",
            "follow-up appointments",
            "cardiovascular disease",
            "diabetes",
            "cancer",
        ]

        # Select 1-2 additional notes
        num_notes = random.randint(1, 2)
        additional_notes = []

        for _ in range(num_notes):
            template = random.choice(note_templates)
            filler = random.choice(note_fillers)
            additional_notes.append(template.format(filler))

        return " ".join(additional_notes)
