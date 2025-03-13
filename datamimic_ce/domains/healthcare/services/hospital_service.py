# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Hospital service.

This module provides the HospitalService class for generating and managing hospital data.
"""

import csv
import json
import os
from typing import Any

from datamimic_ce.domains.healthcare.models.hospital import Hospital
from datamimic_ce.utils.domain_class_util import DomainClassUtil


class HospitalService:
    """Service for generating and managing hospital data.

    This class provides methods for generating hospital data, exporting it to various formats,
    and retrieving hospitals with specific characteristics.
    """

    def __init__(self, locale: str = "en", dataset: str | None = None):
        """Initialize the HospitalService.

        Args:
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
        """
        self._locale = locale
        self._dataset = dataset
        self._class_factory_util = DomainClassUtil()
        self._hospital = Hospital(
            class_factory_util=self._class_factory_util,
            locale=locale,
            dataset=dataset,
        )

    def generate_hospital(self) -> dict[str, Any]:
        """Generate a single hospital.

        Returns:
            A dictionary containing the generated hospital data.
        """
        hospital_data = self._hospital.to_dict()
        self._hospital.reset()
        return hospital_data

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of hospitals.

        Args:
            count: The number of hospitals to generate.

        Returns:
            A list of dictionaries containing the generated hospital data.
        """
        return self._hospital.generate_batch(count)

    def export_to_json(self, hospitals: list[dict[str, Any]], file_path: str) -> None:
        """Export hospital data to a JSON file.

        Args:
            hospitals: A list of hospital dictionaries to export.
            file_path: The path to the output file.
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(hospitals, f, indent=2)

    def export_to_csv(self, hospitals: list[dict[str, Any]], file_path: str) -> None:
        """Export hospital data to a CSV file.

        Args:
            hospitals: A list of hospital dictionaries to export.
            file_path: The path to the output file.
        """
        if not hospitals:
            return

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        # Get field names from the first hospital
        fieldnames = list(hospitals[0].keys())

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for hospital in hospitals:
                # Handle nested dictionaries and lists for CSV export
                flat_hospital = {}
                for key, value in hospital.items():
                    if isinstance(value, dict) or isinstance(value, list):
                        flat_hospital[key] = json.dumps(value)
                    else:
                        flat_hospital[key] = value
                writer.writerow(flat_hospital)

    def get_hospitals_by_type(self, hospital_type: str, count: int = 10) -> list[dict[str, Any]]:
        """Generate hospitals of a specific type.

        Args:
            hospital_type: The type of hospital to generate.
            count: The number of hospitals to generate.

        Returns:
            A list of hospital dictionaries of the specified type.
        """
        hospitals = []
        attempts = 0
        max_attempts = count * 10  # Limit the number of attempts to avoid infinite loops

        while len(hospitals) < count and attempts < max_attempts:
            hospital = self.generate_hospital()
            if hospital["type"] == hospital_type:
                hospitals.append(hospital)
            attempts += 1

        return hospitals

    def get_hospitals_by_service(self, service: str, count: int = 10) -> list[dict[str, Any]]:
        """Generate hospitals that offer a specific service.

        Args:
            service: The service that hospitals should offer.
            count: The number of hospitals to generate.

        Returns:
            A list of hospital dictionaries that offer the specified service.
        """
        hospitals = []
        attempts = 0
        max_attempts = count * 10  # Limit the number of attempts to avoid infinite loops

        while len(hospitals) < count and attempts < max_attempts:
            hospital = self.generate_hospital()
            if service in hospital["services"]:
                hospitals.append(hospital)
            attempts += 1

        return hospitals

    def get_hospitals_by_department(self, department: str, count: int = 10) -> list[dict[str, Any]]:
        """Generate hospitals that have a specific department.

        Args:
            department: The department that hospitals should have.
            count: The number of hospitals to generate.

        Returns:
            A list of hospital dictionaries that have the specified department.
        """
        hospitals = []
        attempts = 0
        max_attempts = count * 10  # Limit the number of attempts to avoid infinite loops

        while len(hospitals) < count and attempts < max_attempts:
            hospital = self.generate_hospital()
            if department in hospital["departments"]:
                hospitals.append(hospital)
            attempts += 1

        return hospitals

    def get_hospitals_by_bed_count_range(self, min_beds: int, max_beds: int, count: int = 10) -> list[dict[str, Any]]:
        """Generate hospitals within a specific bed count range.

        Args:
            min_beds: The minimum number of beds.
            max_beds: The maximum number of beds.
            count: The number of hospitals to generate.

        Returns:
            A list of hospital dictionaries within the specified bed count range.
        """
        hospitals = []
        attempts = 0
        max_attempts = count * 10  # Limit the number of attempts to avoid infinite loops

        while len(hospitals) < count and attempts < max_attempts:
            hospital = self.generate_hospital()
            if min_beds <= hospital["bed_count"] <= max_beds:
                hospitals.append(hospital)
            attempts += 1

        return hospitals

    def get_hospitals_with_emergency_services(self, count: int = 10) -> list[dict[str, Any]]:
        """Generate hospitals that offer emergency services.

        Args:
            count: The number of hospitals to generate.

        Returns:
            A list of hospital dictionaries that offer emergency services.
        """
        hospitals = []
        attempts = 0
        max_attempts = count * 10  # Limit the number of attempts to avoid infinite loops

        while len(hospitals) < count and attempts < max_attempts:
            hospital = self.generate_hospital()
            if hospital["emergency_services"]:
                hospitals.append(hospital)
            attempts += 1

        return hospitals

    def get_teaching_hospitals(self, count: int = 10) -> list[dict[str, Any]]:
        """Generate teaching hospitals.

        Args:
            count: The number of hospitals to generate.

        Returns:
            A list of hospital dictionaries that are teaching hospitals.
        """
        hospitals = []
        attempts = 0
        max_attempts = count * 10  # Limit the number of attempts to avoid infinite loops

        while len(hospitals) < count and attempts < max_attempts:
            hospital = self.generate_hospital()
            if hospital["teaching_status"]:
                hospitals.append(hospital)
            attempts += 1

        return hospitals

    def execute(self, command: str, params: dict[str, Any] = None) -> Any:
        """Execute a command with the given parameters.

        This method provides a generic interface for executing various hospital-related operations.

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

        if command == "generate_hospital":
            return self.generate_hospital()
        elif command == "generate_batch":
            count = params.get("count", 100)
            return self.generate_batch(count)
        elif command == "export_to_json":
            hospitals = params.get("hospitals", [])
            file_path = params.get("file_path", "hospitals.json")
            self.export_to_json(hospitals, file_path)
            return {"status": "success", "file_path": file_path}
        elif command == "export_to_csv":
            hospitals = params.get("hospitals", [])
            file_path = params.get("file_path", "hospitals.csv")
            self.export_to_csv(hospitals, file_path)
            return {"status": "success", "file_path": file_path}
        elif command == "get_hospitals_by_type":
            hospital_type = params.get("hospital_type", "")
            count = params.get("count", 10)
            return self.get_hospitals_by_type(hospital_type, count)
        elif command == "get_hospitals_by_service":
            service = params.get("service", "")
            count = params.get("count", 10)
            return self.get_hospitals_by_service(service, count)
        elif command == "get_hospitals_by_department":
            department = params.get("department", "")
            count = params.get("count", 10)
            return self.get_hospitals_by_department(department, count)
        elif command == "get_hospitals_by_bed_count_range":
            min_beds = params.get("min_beds", 0)
            max_beds = params.get("max_beds", 1000)
            count = params.get("count", 10)
            return self.get_hospitals_by_bed_count_range(min_beds, max_beds, count)
        elif command == "get_hospitals_with_emergency_services":
            count = params.get("count", 10)
            return self.get_hospitals_with_emergency_services(count)
        elif command == "get_teaching_hospitals":
            count = params.get("count", 10)
            return self.get_teaching_hospitals(count)
        else:
            raise ValueError(f"Unsupported command: {command}")
