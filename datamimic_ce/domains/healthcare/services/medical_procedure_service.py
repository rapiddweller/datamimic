# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Medical Procedure service.

This module provides the MedicalProcedureService class for generating and managing medical procedure data.
"""

import csv
import json
import os
from typing import Any

from datamimic_ce.domains.healthcare.models.medical_procedure import MedicalProcedure
from datamimic_ce.utils.domain_class_util import DomainClassUtil


class MedicalProcedureService:
    """Service for generating and managing medical procedure data.

    This class provides methods for generating medical procedure data, exporting it to various formats,
    and retrieving procedures with specific characteristics.
    """

    def __init__(self, locale: str = "en", dataset: str | None = None):
        """Initialize the MedicalProcedureService.

        Args:
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
        """
        self._locale = locale
        self._dataset = dataset
        self._class_factory_util = DomainClassUtil()
        self._procedure = MedicalProcedure(
            class_factory_util=self._class_factory_util,
            locale=locale,
            dataset=dataset,
        )

    def generate_procedure(self) -> dict[str, Any]:
        """Generate a single medical procedure.

        Returns:
            A dictionary containing the generated medical procedure data.
        """
        procedure_data = self._procedure.to_dict()
        self._procedure.reset()
        return procedure_data

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of medical procedures.

        Args:
            count: The number of medical procedures to generate.

        Returns:
            A list of dictionaries containing the generated medical procedure data.
        """
        return self._procedure.generate_batch(count)

    def export_to_json(self, procedures: list[dict[str, Any]], file_path: str) -> None:
        """Export medical procedure data to a JSON file.

        Args:
            procedures: A list of medical procedure dictionaries to export.
            file_path: The path to the output file.
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(procedures, f, indent=2)

    def export_to_csv(self, procedures: list[dict[str, Any]], file_path: str) -> None:
        """Export medical procedure data to a CSV file.

        Args:
            procedures: A list of medical procedure dictionaries to export.
            file_path: The path to the output file.
        """
        if not procedures:
            return

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        # Get field names from the first procedure
        fieldnames = list(procedures[0].keys())

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for procedure in procedures:
                # Handle nested dictionaries and lists for CSV export
                flat_procedure = {}
                for key, value in procedure.items():
                    if isinstance(value, dict) or isinstance(value, list):
                        flat_procedure[key] = json.dumps(value)
                    else:
                        flat_procedure[key] = value
                writer.writerow(flat_procedure)

    def get_procedures_by_category(self, category: str, count: int = 10) -> list[dict[str, Any]]:
        """Generate medical procedures of a specific category.

        Args:
            category: The category of medical procedures to generate.
            count: The number of medical procedures to generate.

        Returns:
            A list of medical procedure dictionaries of the specified category.
        """
        procedures = []
        attempts = 0
        max_attempts = count * 10  # Limit the number of attempts to avoid infinite loops

        while len(procedures) < count and attempts < max_attempts:
            procedure = self.generate_procedure()
            if procedure["category"] == category:
                procedures.append(procedure)
            attempts += 1

        return procedures

    def get_procedures_by_specialty(self, specialty: str, count: int = 10) -> list[dict[str, Any]]:
        """Generate medical procedures associated with a specific specialty.

        Args:
            specialty: The medical specialty associated with the procedures.
            count: The number of medical procedures to generate.

        Returns:
            A list of medical procedure dictionaries associated with the specified specialty.
        """
        procedures = []
        attempts = 0
        max_attempts = count * 10  # Limit the number of attempts to avoid infinite loops

        while len(procedures) < count and attempts < max_attempts:
            procedure = self.generate_procedure()
            if procedure["specialty"] == specialty:
                procedures.append(procedure)
            attempts += 1

        return procedures

    def get_surgical_procedures(self, count: int = 10) -> list[dict[str, Any]]:
        """Generate surgical medical procedures.

        Args:
            count: The number of medical procedures to generate.

        Returns:
            A list of surgical medical procedure dictionaries.
        """
        procedures = []
        attempts = 0
        max_attempts = count * 10  # Limit the number of attempts to avoid infinite loops

        while len(procedures) < count and attempts < max_attempts:
            procedure = self.generate_procedure()
            if procedure["is_surgical"]:
                procedures.append(procedure)
            attempts += 1

        return procedures

    def get_diagnostic_procedures(self, count: int = 10) -> list[dict[str, Any]]:
        """Generate diagnostic medical procedures.

        Args:
            count: The number of medical procedures to generate.

        Returns:
            A list of diagnostic medical procedure dictionaries.
        """
        procedures = []
        attempts = 0
        max_attempts = count * 10  # Limit the number of attempts to avoid infinite loops

        while len(procedures) < count and attempts < max_attempts:
            procedure = self.generate_procedure()
            if procedure["is_diagnostic"]:
                procedures.append(procedure)
            attempts += 1

        return procedures

    def get_preventive_procedures(self, count: int = 10) -> list[dict[str, Any]]:
        """Generate preventive medical procedures.

        Args:
            count: The number of medical procedures to generate.

        Returns:
            A list of preventive medical procedure dictionaries.
        """
        procedures = []
        attempts = 0
        max_attempts = count * 10  # Limit the number of attempts to avoid infinite loops

        while len(procedures) < count and attempts < max_attempts:
            procedure = self.generate_procedure()
            if procedure["is_preventive"]:
                procedures.append(procedure)
            attempts += 1

        return procedures

    def get_procedures_by_cost_range(self, min_cost: float, max_cost: float, count: int = 10) -> list[dict[str, Any]]:
        """Generate medical procedures within a specific cost range.

        Args:
            min_cost: The minimum cost.
            max_cost: The maximum cost.
            count: The number of medical procedures to generate.

        Returns:
            A list of medical procedure dictionaries within the specified cost range.
        """
        procedures = []
        attempts = 0
        max_attempts = count * 10  # Limit the number of attempts to avoid infinite loops

        while len(procedures) < count and attempts < max_attempts:
            procedure = self.generate_procedure()
            if min_cost <= procedure["cost"] <= max_cost:
                procedures.append(procedure)
            attempts += 1

        return procedures

    def execute(self, command: str, params: dict[str, Any] = None) -> Any:
        """Execute a command with the given parameters.

        This method provides a generic interface for executing various medical procedure-related operations.

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

        if command == "generate_procedure":
            return self.generate_procedure()
        elif command == "generate_batch":
            count = params.get("count", 100)
            return self.generate_batch(count)
        elif command == "export_to_json":
            procedures = params.get("procedures", [])
            file_path = params.get("file_path", "procedures.json")
            self.export_to_json(procedures, file_path)
            return {"status": "success", "file_path": file_path}
        elif command == "export_to_csv":
            procedures = params.get("procedures", [])
            file_path = params.get("file_path", "procedures.csv")
            self.export_to_csv(procedures, file_path)
            return {"status": "success", "file_path": file_path}
        elif command == "get_procedures_by_category":
            category = params.get("category", "")
            count = params.get("count", 10)
            return self.get_procedures_by_category(category, count)
        elif command == "get_procedures_by_specialty":
            specialty = params.get("specialty", "")
            count = params.get("count", 10)
            return self.get_procedures_by_specialty(specialty, count)
        elif command == "get_surgical_procedures":
            count = params.get("count", 10)
            return self.get_surgical_procedures(count)
        elif command == "get_diagnostic_procedures":
            count = params.get("count", 10)
            return self.get_diagnostic_procedures(count)
        elif command == "get_preventive_procedures":
            count = params.get("count", 10)
            return self.get_preventive_procedures(count)
        elif command == "get_procedures_by_cost_range":
            min_cost = params.get("min_cost", 0)
            max_cost = params.get("max_cost", 10000)
            count = params.get("count", 10)
            return self.get_procedures_by_cost_range(min_cost, max_cost, count)
        else:
            raise ValueError(f"Unsupported command: {command}")
