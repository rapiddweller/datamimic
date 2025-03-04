# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Patient service.

This module provides the PatientService class for generating and managing patient data.
"""

import csv
import json
import os
from typing import Any

from datamimic_ce.domains.healthcare.models.patient import Patient
from datamimic_ce.utils.domain_class_util import DomainClassUtil


class PatientService:
    """Service for generating and managing patient data.

    This class provides methods for generating patient data, exporting it to various formats,
    and retrieving patients with specific characteristics.
    """

    def __init__(self, locale: str = "en", dataset: str | None = None):
        """Initialize the PatientService.

        Args:
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
        """
        self._locale = locale
        self._dataset = dataset
        self._class_factory_util = DomainClassUtil()
        self._patient = Patient(
            class_factory_util=self._class_factory_util,
            locale=locale,
            dataset=dataset,
        )

    def generate_patient(self) -> dict[str, Any]:
        """Generate a single patient.

        Returns:
            A dictionary containing the generated patient data.
        """
        patient_data = self._patient.to_dict()
        self._patient.reset()
        return patient_data

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of patients.

        Args:
            count: The number of patients to generate.

        Returns:
            A list of dictionaries containing the generated patient data.
        """
        return self._patient.generate_batch(count)

    def export_to_json(self, patients: list[dict[str, Any]], file_path: str) -> None:
        """Export patient data to a JSON file.

        Args:
            patients: A list of patient dictionaries to export.
            file_path: The path to the output file.
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(patients, f, indent=2)

    def export_to_csv(self, patients: list[dict[str, Any]], file_path: str) -> None:
        """Export patient data to a CSV file.

        Args:
            patients: A list of patient dictionaries to export.
            file_path: The path to the output file.
        """
        if not patients:
            return

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        # Get field names from the first patient
        fieldnames = list(patients[0].keys())

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for patient in patients:
                # Handle nested dictionaries and lists for CSV export
                flat_patient = {}
                for key, value in patient.items():
                    if isinstance(value, dict) or isinstance(value, list):
                        flat_patient[key] = json.dumps(value)
                    else:
                        flat_patient[key] = value
                writer.writerow(flat_patient)

    def get_patients_by_condition(self, condition: str, count: int = 10) -> list[dict[str, Any]]:
        """Generate patients with a specific medical condition.

        Args:
            condition: The medical condition to include.
            count: The number of patients to generate.

        Returns:
            A list of patient dictionaries with the specified condition.
        """
        patients = []
        attempts = 0
        max_attempts = count * 10  # Limit the number of attempts to avoid infinite loops

        while len(patients) < count and attempts < max_attempts:
            patient = self.generate_patient()
            if condition in patient["conditions"]:
                patients.append(patient)
            attempts += 1

        return patients

    def get_patients_by_age_range(self, min_age: int, max_age: int, count: int = 10) -> list[dict[str, Any]]:
        """Generate patients within a specific age range.

        Args:
            min_age: The minimum age.
            max_age: The maximum age.
            count: The number of patients to generate.

        Returns:
            A list of patient dictionaries within the specified age range.
        """
        patients = []
        attempts = 0
        max_attempts = count * 10  # Limit the number of attempts to avoid infinite loops

        while len(patients) < count and attempts < max_attempts:
            patient = self.generate_patient()
            if min_age <= patient["age"] <= max_age:
                patients.append(patient)
            attempts += 1

        return patients

    def get_patients_by_insurance(self, insurance_provider: str, count: int = 10) -> list[dict[str, Any]]:
        """Generate patients with a specific insurance provider.

        Args:
            insurance_provider: The insurance provider to include.
            count: The number of patients to generate.

        Returns:
            A list of patient dictionaries with the specified insurance provider.
        """
        patients = []
        attempts = 0
        max_attempts = count * 10  # Limit the number of attempts to avoid infinite loops

        while len(patients) < count and attempts < max_attempts:
            patient = self.generate_patient()
            if patient["insurance_provider"] == insurance_provider:
                patients.append(patient)
            attempts += 1

        return patients

    def execute(self, command: str, params: dict[str, Any] = None) -> Any:
        """Execute a command with the given parameters.

        This method provides a generic interface for executing various patient-related operations.

        Args:
            command: The command to execute.
            params: The parameters for the command.

        Returns:
            The result of the command execution.

        Raises:
            ValueError: If the command is not supported.
        """
        if params is None:
            params = {}

        if command == "generate_patient":
            return self.generate_patient()
        elif command == "generate_batch":
            count = params.get("count", 100)
            return self.generate_batch(count)
        elif command == "export_to_json":
            patients = params.get("patients", [])
            file_path = params.get("file_path", "patients.json")
            self.export_to_json(patients, file_path)
            return {"status": "success", "file_path": file_path}
        elif command == "export_to_csv":
            patients = params.get("patients", [])
            file_path = params.get("file_path", "patients.csv")
            self.export_to_csv(patients, file_path)
            return {"status": "success", "file_path": file_path}
        elif command == "get_patients_by_condition":
            condition = params.get("condition", "")
            count = params.get("count", 10)
            return self.get_patients_by_condition(condition, count)
        elif command == "get_patients_by_age_range":
            min_age = params.get("min_age", 0)
            max_age = params.get("max_age", 100)
            count = params.get("count", 10)
            return self.get_patients_by_age_range(min_age, max_age, count)
        elif command == "get_patients_by_insurance":
            insurance_provider = params.get("insurance_provider", "")
            count = params.get("count", 10)
            return self.get_patients_by_insurance(insurance_provider, count)
        else:
            raise ValueError(f"Unsupported command: {command}")
