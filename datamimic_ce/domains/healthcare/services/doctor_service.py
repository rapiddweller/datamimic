# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Doctor service.

This module provides a service for working with Doctor entities.
"""

import json
import os
from typing import Any, ClassVar

from datamimic_ce.core.interfaces import Service
from datamimic_ce.domains.healthcare.models.doctor import Doctor
from datamimic_ce.logger import logger
from datamimic_ce.utils.domain_class_util import DomainClassUtil


class DoctorService(Service):
    """Service for working with Doctor entities.

    This class provides methods for generating, exporting, and working with
    Doctor entities.
    """

    # Class-level cache for shared data
    _INSTANCE_CACHE: ClassVar[dict[str, "DoctorService"]] = {}

    @classmethod
    def get_instance(cls, locale: str = "en", dataset: str | None = None) -> "DoctorService":
        """Get a cached instance of the DoctorService.

        Args:
            locale: The locale to use
            dataset: The dataset to use

        Returns:
            A DoctorService instance
        """
        key = f"{locale}_{dataset}"
        if key not in cls._INSTANCE_CACHE:
            cls._INSTANCE_CACHE[key] = cls(locale, dataset)
        return cls._INSTANCE_CACHE[key]

    def __init__(self, locale: str = "en", dataset: str | None = None):
        """Initialize the DoctorService.

        Args:
            locale: The locale to use
            dataset: The dataset to use
        """
        self._locale = locale
        self._dataset = dataset
        self._class_factory_util = DomainClassUtil()

    def execute(self, *args, **kwargs) -> Any:
        """Execute the service operation.

        This method is a generic entry point for service operations.
        It delegates to more specific methods based on the operation parameter.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments including:
                - operation: The operation to perform
                - count: The number of doctors to generate
                - output_path: The path to write output to
                - format: The output format (json, csv)

        Returns:
            The result of the service operation
        """
        operation = kwargs.get("operation", "generate")

        if operation == "generate":
            count = kwargs.get("count", 1)
            return self.generate_doctors(count)
        elif operation == "export":
            count = kwargs.get("count", 100)
            output_path = kwargs.get("output_path", "doctors.json")
            format = kwargs.get("format", "json")
            return self.export_doctors(count, output_path, format)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    def generate_doctors(self, count: int = 1) -> list[dict[str, Any]]:
        """Generate a batch of doctor entities.

        Args:
            count: The number of doctor entities to generate

        Returns:
            A list of dictionaries containing the generated doctor entities
        """
        doctor = Doctor(
            class_factory_util=self._class_factory_util,
            locale=self._locale,
            dataset=self._dataset,
        )
        return doctor.generate_batch(count)

    def export_doctors(self, count: int = 100, output_path: str = "doctors.json", format: str = "json") -> str:
        """Generate and export doctor entities to a file.

        Args:
            count: The number of doctor entities to generate
            output_path: The path to write the output to
            format: The output format (json, csv)

        Returns:
            The path to the output file
        """
        doctors = self.generate_doctors(count)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        if format.lower() == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(doctors, f, indent=2)
        elif format.lower() == "csv":
            import csv

            # Get all possible keys from all doctors
            fieldnames = set()
            for doctor in doctors:
                fieldnames.update(doctor.keys())

            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                writer.writeheader()
                writer.writerows(doctors)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Exported {count} doctors to {output_path}")
        return output_path

    def get_doctor(self) -> Doctor:
        """Get a new Doctor entity instance.

        Returns:
            A Doctor entity instance
        """
        return Doctor(
            class_factory_util=self._class_factory_util,
            locale=self._locale,
            dataset=self._dataset,
        )

    def get_doctor_by_specialty(self, specialty: str) -> dict[str, Any] | None:
        """Get a doctor with a specific specialty.

        Args:
            specialty: The specialty to look for

        Returns:
            A doctor with the specified specialty, or None if not found after 10 attempts
        """
        doctor = self.get_doctor()

        # Try up to 10 times to find a doctor with the specified specialty
        for _ in range(10):
            if doctor.specialty.lower() == specialty.lower():
                return doctor.to_dict()
            doctor.reset()

        # If we couldn't find a doctor with the exact specialty, try to force it
        doctor_dict = doctor.to_dict()
        doctor_dict["specialty"] = specialty
        return doctor_dict
