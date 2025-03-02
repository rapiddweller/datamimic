# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Police officer service.

This module provides a service for working with PoliceOfficer entities.
"""

import json
import os
from typing import Any, ClassVar, List, Dict, Optional

from datamimic_ce.core.interfaces import Service
from datamimic_ce.domains.public_sector.models.police_officer import PoliceOfficer
from datamimic_ce.logger import logger
from datamimic_ce.utils.class_factory_util import ClassFactoryUtil


class PoliceOfficerService(Service):
    """Service for working with PoliceOfficer entities.

    This class provides methods for generating, exporting, and working with
    PoliceOfficer entities.
    """

    # Class-level cache for shared data
    _INSTANCE_CACHE: ClassVar[dict[str, "PoliceOfficerService"]] = {}

    @classmethod
    def get_instance(cls, locale: str = "en", dataset: str | None = None) -> "PoliceOfficerService":
        """Get a cached instance of the PoliceOfficerService.

        Args:
            locale: The locale to use
            dataset: The dataset to use

        Returns:
            A PoliceOfficerService instance
        """
        key = f"{locale}_{dataset}"
        if key not in cls._INSTANCE_CACHE:
            cls._INSTANCE_CACHE[key] = cls(locale, dataset)
        return cls._INSTANCE_CACHE[key]

    def __init__(self, locale: str = "en", dataset: str | None = None):
        """Initialize the PoliceOfficerService.

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
                - count: The number of police officers to generate
                - output_path: The path to write output to
                - format: The output format (json, csv)
                - rank: The rank to filter by
                - department: The department to filter by

        Returns:
            The result of the service operation
        """
        operation = kwargs.get("operation", "generate")

        if operation == "generate":
            count = kwargs.get("count", 1)
            return self.generate_officers(count)
        elif operation == "export":
            count = kwargs.get("count", 100)
            output_path = kwargs.get("output_path", "police_officers.json")
            format = kwargs.get("format", "json")
            return self.export_officers(count, output_path, format)
        elif operation == "filter_by_rank":
            count = kwargs.get("count", 10)
            rank = kwargs.get("rank")
            if not rank:
                raise ValueError("Rank is required for filter_by_rank operation")
            return self.get_officers_by_rank(rank, count)
        elif operation == "filter_by_department":
            count = kwargs.get("count", 10)
            department = kwargs.get("department")
            if not department:
                raise ValueError("Department is required for filter_by_department operation")
            return self.get_officers_by_department(department, count)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    def generate_officers(self, count: int = 1) -> list[dict[str, Any]]:
        """Generate a batch of police officer entities.

        Args:
            count: The number of police officer entities to generate

        Returns:
            A list of dictionaries containing the generated police officer entities
        """
        officer = PoliceOfficer(
            class_factory_util=self._class_factory_util,
            locale=self._locale,
            dataset=self._dataset,
        )
        return officer.generate_batch(count)

    def export_officers(self, count: int = 100, output_path: str = "police_officers.json", format: str = "json") -> str:
        """Generate and export police officer entities to a file.

        Args:
            count: The number of police officer entities to generate
            output_path: The path to write the output to
            format: The output format (json, csv)

        Returns:
            The path to the output file
        """
        officers = self.generate_officers(count)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        if format.lower() == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(officers, f, indent=2)
        elif format.lower() == "csv":
            import csv

            # Get all possible keys from all officers
            fieldnames = set()
            for officer in officers:
                fieldnames.update(officer.keys())

            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                writer.writeheader()
                writer.writerows(officers)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Exported {count} police officers to {output_path}")
        return output_path

    def get_officer(self) -> PoliceOfficer:
        """Get a new PoliceOfficer entity instance.

        Returns:
            A PoliceOfficer entity instance
        """
        return PoliceOfficer(
            class_factory_util=self._class_factory_util,
            locale=self._locale,
            dataset=self._dataset,
        )

    def get_officers_by_rank(self, rank: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get police officers with a specific rank.

        Args:
            rank: The rank to filter by
            count: The maximum number of officers to return

        Returns:
            A list of police officers with the specified rank
        """
        result = []
        attempts = 0
        max_attempts = count * 5  # Try at most 5 times per requested officer
        
        while len(result) < count and attempts < max_attempts:
            officer = self.get_officer()
            if officer.rank.lower() == rank.lower():
                result.append(officer.to_dict())
            officer.reset()
            attempts += 1
            
        # If we couldn't find enough officers with the exact rank, force the rank for the remaining
        if len(result) < count:
            remaining = count - len(result)
            for _ in range(remaining):
                officer = self.get_officer()
                officer_dict = officer.to_dict()
                officer_dict["rank"] = rank
                result.append(officer_dict)
                officer.reset()
                
        return result

    def get_officers_by_department(self, department: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get police officers from a specific department.

        Args:
            department: The department to filter by
            count: The maximum number of officers to return

        Returns:
            A list of police officers from the specified department
        """
        result = []
        attempts = 0
        max_attempts = count * 5  # Try at most 5 times per requested officer
        
        while len(result) < count and attempts < max_attempts:
            officer = self.get_officer()
            if department.lower() in officer.department.lower():
                result.append(officer.to_dict())
            officer.reset()
            attempts += 1
            
        # If we couldn't find enough officers with the exact department, force the department for the remaining
        if len(result) < count:
            remaining = count - len(result)
            for _ in range(remaining):
                officer = self.get_officer()
                officer_dict = officer.to_dict()
                officer_dict["department"] = department
                result.append(officer_dict)
                officer.reset()
                
        return result

    def get_officers_by_unit(self, unit: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get police officers from a specific unit.

        Args:
            unit: The unit to filter by
            count: The maximum number of officers to return

        Returns:
            A list of police officers from the specified unit
        """
        result = []
        attempts = 0
        max_attempts = count * 5  # Try at most 5 times per requested officer
        
        while len(result) < count and attempts < max_attempts:
            officer = self.get_officer()
            if unit.lower() == officer.unit.lower():
                result.append(officer.to_dict())
            officer.reset()
            attempts += 1
            
        # If we couldn't find enough officers with the exact unit, force the unit for the remaining
        if len(result) < count:
            remaining = count - len(result)
            for _ in range(remaining):
                officer = self.get_officer()
                officer_dict = officer.to_dict()
                officer_dict["unit"] = unit
                result.append(officer_dict)
                officer.reset()
                
        return result