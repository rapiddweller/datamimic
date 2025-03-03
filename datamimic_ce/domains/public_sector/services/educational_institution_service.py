# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Educational institution service.

This module provides a service for working with EducationalInstitution entities.
"""

import json
import os
from typing import Any, ClassVar

from datamimic_ce.core.interfaces import Service
from datamimic_ce.domains.public_sector.models.educational_institution import EducationalInstitution
from datamimic_ce.logger import logger
from datamimic_ce.utils.class_factory_util import ClassFactoryUtil


class EducationalInstitutionService(Service):
    """Service for working with EducationalInstitution entities.

    This class provides methods for generating, exporting, and working with
    EducationalInstitution entities.
    """

    # Class-level cache for shared data
    _INSTANCE_CACHE: ClassVar[dict[str, "EducationalInstitutionService"]] = {}

    @classmethod
    def get_instance(cls, locale: str = "en", dataset: str | None = None) -> "EducationalInstitutionService":
        """Get a cached instance of the EducationalInstitutionService.

        Args:
            locale: The locale to use
            dataset: The dataset to use

        Returns:
            An EducationalInstitutionService instance
        """
        key = f"{locale}_{dataset}"
        if key not in cls._INSTANCE_CACHE:
            cls._INSTANCE_CACHE[key] = cls(locale, dataset)
        return cls._INSTANCE_CACHE[key]

    def __init__(self, locale: str = "en", dataset: str | None = None):
        """Initialize the EducationalInstitutionService.

        Args:
            locale: The locale to use
            dataset: The dataset to use
        """
        self._locale = locale
        self._dataset = dataset
        self._class_factory_util = ClassFactoryUtil()

    def execute(self, *args, **kwargs) -> Any:
        """Execute the service operation.

        This method is a generic entry point for service operations.
        It delegates to more specific methods based on the operation parameter.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments including:
                - operation: The operation to perform
                - count: The number of institutions to generate
                - output_path: The path to write output to
                - format: The output format (json, csv)
                - type: The institution type to filter by
                - level: The education level to filter by

        Returns:
            The result of the service operation
        """
        operation = kwargs.get("operation", "generate")

        if operation == "generate":
            count = kwargs.get("count", 1)
            return self.generate_institutions(count)
        elif operation == "export":
            count = kwargs.get("count", 100)
            output_path = kwargs.get("output_path", "educational_institutions.json")
            format = kwargs.get("format", "json")
            return self.export_institutions(count, output_path, format)
        elif operation == "filter_by_type":
            count = kwargs.get("count", 10)
            institution_type = kwargs.get("type")
            if not institution_type:
                raise ValueError("Type is required for filter_by_type operation")
            return self.get_institutions_by_type(institution_type, count)
        elif operation == "filter_by_level":
            count = kwargs.get("count", 10)
            level = kwargs.get("level")
            if not level:
                raise ValueError("Level is required for filter_by_level operation")
            return self.get_institutions_by_level(level, count)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    def generate_institutions(self, count: int = 1) -> list[dict[str, Any]]:
        """Generate a batch of educational institution entities.

        Args:
            count: The number of educational institution entities to generate

        Returns:
            A list of dictionaries containing the generated educational institution entities
        """
        institution = EducationalInstitution(
            class_factory_util=self._class_factory_util,
            locale=self._locale,
            dataset=self._dataset,
        )
        return institution.generate_batch(count)

    def export_institutions(
        self, count: int = 100, output_path: str = "educational_institutions.json", format: str = "json"
    ) -> str:
        """Generate and export educational institution entities to a file.

        Args:
            count: The number of educational institution entities to generate
            output_path: The path to write the output to
            format: The output format (json, csv)

        Returns:
            The path to the output file
        """
        institutions = self.generate_institutions(count)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        if format.lower() == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(institutions, f, indent=2)
        elif format.lower() == "csv":
            import csv

            # Get all possible keys from all institutions
            fieldnames = set()
            for institution in institutions:
                fieldnames.update(institution.keys())

            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                writer.writeheader()
                writer.writerows(institutions)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Exported {count} educational institutions to {output_path}")
        return output_path

    def get_institution(self) -> EducationalInstitution:
        """Get a new EducationalInstitution entity instance.

        Returns:
            An EducationalInstitution entity instance
        """
        return EducationalInstitution(
            class_factory_util=self._class_factory_util,
            locale=self._locale,
            dataset=self._dataset,
        )

    def get_institutions_by_type(self, institution_type: str, count: int = 10) -> list[dict[str, Any]]:
        """Get educational institutions of a specific type.

        Args:
            institution_type: The institution type to filter by
            count: The maximum number of institutions to return

        Returns:
            A list of educational institutions of the specified type
        """
        result = []
        attempts = 0
        max_attempts = count * 5  # Try at most 5 times per requested institution

        while len(result) < count and attempts < max_attempts:
            institution = self.get_institution()
            if institution_type.lower() in institution.type.lower():
                result.append(institution.to_dict())
            institution.reset()
            attempts += 1

        # If we couldn't find enough institutions with the exact type, force the type for the remaining
        if len(result) < count:
            remaining = count - len(result)
            for _ in range(remaining):
                institution = self.get_institution()
                institution_dict = institution.to_dict()
                institution_dict["type"] = institution_type
                result.append(institution_dict)
                institution.reset()

        return result

    def get_institutions_by_level(self, level: str, count: int = 10) -> list[dict[str, Any]]:
        """Get educational institutions of a specific level.

        Args:
            level: The education level to filter by
            count: The maximum number of institutions to return

        Returns:
            A list of educational institutions of the specified level
        """
        result = []
        attempts = 0
        max_attempts = count * 5  # Try at most 5 times per requested institution

        while len(result) < count and attempts < max_attempts:
            institution = self.get_institution()
            if level.lower() in institution.level.lower():
                result.append(institution.to_dict())
            institution.reset()
            attempts += 1

        # If we couldn't find enough institutions with the exact level, force the level for the remaining
        if len(result) < count:
            remaining = count - len(result)
            for _ in range(remaining):
                institution = self.get_institution()
                institution_dict = institution.to_dict()
                institution_dict["level"] = level
                result.append(institution_dict)
                institution.reset()

        return result

    def get_institutions_by_student_count_range(
        self, min_count: int, max_count: int, count: int = 10
    ) -> list[dict[str, Any]]:
        """Get educational institutions within a specific student count range.

        Args:
            min_count: The minimum student count
            max_count: The maximum student count
            count: The maximum number of institutions to return

        Returns:
            A list of educational institutions within the specified student count range
        """
        result = []
        attempts = 0
        max_attempts = count * 10  # Try at most 10 times per requested institution

        while len(result) < count and attempts < max_attempts:
            institution = self.get_institution()
            if min_count <= institution.student_count <= max_count:
                result.append(institution.to_dict())
            institution.reset()
            attempts += 1

        return result

    def get_universities(self, count: int = 10) -> list[dict[str, Any]]:
        """Get university institutions.

        Args:
            count: The maximum number of universities to return

        Returns:
            A list of university institutions
        """
        return self.get_institutions_by_type("University", count)

    def get_colleges(self, count: int = 10) -> list[dict[str, Any]]:
        """Get college institutions.

        Args:
            count: The maximum number of colleges to return

        Returns:
            A list of college institutions
        """
        return self.get_institutions_by_type("College", count)

    def get_k12_schools(self, count: int = 10) -> list[dict[str, Any]]:
        """Get K-12 school institutions.

        Args:
            count: The maximum number of K-12 schools to return

        Returns:
            A list of K-12 school institutions
        """
        return self.get_institutions_by_level("K-12", count)
