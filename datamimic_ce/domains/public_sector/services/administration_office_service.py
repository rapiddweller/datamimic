# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Administration office service.

This module provides a service for working with AdministrationOffice entities.
"""

import json
import os
from typing import Any, ClassVar, List, Dict, Optional

from datamimic_ce.core.interfaces import Service
from datamimic_ce.domains.public_sector.models.administration_office import AdministrationOffice
from datamimic_ce.logger import logger
from datamimic_ce.utils.class_factory_util import ClassFactoryUtil


class AdministrationOfficeService(Service):
    """Service for working with AdministrationOffice entities.

    This class provides methods for generating, exporting, and working with
    AdministrationOffice entities.
    """

    # Class-level cache for shared data
    _INSTANCE_CACHE: ClassVar[dict[str, "AdministrationOfficeService"]] = {}

    @classmethod
    def get_instance(cls, locale: str = "en", dataset: str | None = None) -> "AdministrationOfficeService":
        """Get a cached instance of the AdministrationOfficeService.

        Args:
            locale: The locale to use
            dataset: The dataset to use

        Returns:
            An AdministrationOfficeService instance
        """
        key = f"{locale}_{dataset}"
        if key not in cls._INSTANCE_CACHE:
            cls._INSTANCE_CACHE[key] = cls(locale, dataset)
        return cls._INSTANCE_CACHE[key]

    def __init__(self, locale: str = "en", dataset: str | None = None):
        """Initialize the AdministrationOfficeService.

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
                - count: The number of offices to generate
                - output_path: The path to write output to
                - format: The output format (json, csv)
                - type: The office type to filter by
                - jurisdiction: The jurisdiction to filter by

        Returns:
            The result of the service operation
        """
        operation = kwargs.get("operation", "generate")

        if operation == "generate":
            count = kwargs.get("count", 1)
            return self.generate_offices(count)
        elif operation == "export":
            count = kwargs.get("count", 100)
            output_path = kwargs.get("output_path", "administration_offices.json")
            format = kwargs.get("format", "json")
            return self.export_offices(count, output_path, format)
        elif operation == "filter_by_type":
            count = kwargs.get("count", 10)
            office_type = kwargs.get("type")
            if not office_type:
                raise ValueError("Type is required for filter_by_type operation")
            return self.get_offices_by_type(office_type, count)
        elif operation == "filter_by_jurisdiction":
            count = kwargs.get("count", 10)
            jurisdiction = kwargs.get("jurisdiction")
            if not jurisdiction:
                raise ValueError("Jurisdiction is required for filter_by_jurisdiction operation")
            return self.get_offices_by_jurisdiction(jurisdiction, count)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    def generate_offices(self, count: int = 1) -> list[dict[str, Any]]:
        """Generate a batch of administration office entities.

        Args:
            count: The number of administration office entities to generate

        Returns:
            A list of dictionaries containing the generated administration office entities
        """
        office = AdministrationOffice(
            class_factory_util=self._class_factory_util,
            locale=self._locale,
            dataset=self._dataset,
        )
        return office.generate_batch(count)

    def export_offices(self, count: int = 100, output_path: str = "administration_offices.json", format: str = "json") -> str:
        """Generate and export administration office entities to a file.

        Args:
            count: The number of administration office entities to generate
            output_path: The path to write the output to
            format: The output format (json, csv)

        Returns:
            The path to the output file
        """
        offices = self.generate_offices(count)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        if format.lower() == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(offices, f, indent=2)
        elif format.lower() == "csv":
            import csv

            # Get all possible keys from all offices
            fieldnames = set()
            for office in offices:
                fieldnames.update(office.keys())
                
                # Handle nested dictionaries like address and hours_of_operation
                nested_keys = []
                for key, value in office.items():
                    if isinstance(value, dict):
                        nested_keys.append(key)
                        for nested_key in value.keys():
                            fieldnames.add(f"{key}_{nested_key}")
                
                # Remove nested dictionaries
                for key in nested_keys:
                    fieldnames.discard(key)
            
            # Flatten the data
            flat_offices = []
            for office in offices:
                flat_office = {}
                for key, value in office.items():
                    if isinstance(value, dict):
                        for nested_key, nested_value in value.items():
                            flat_office[f"{key}_{nested_key}"] = nested_value
                    else:
                        flat_office[key] = value
                flat_offices.append(flat_office)

            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                writer.writeheader()
                writer.writerows(flat_offices)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Exported {count} administration offices to {output_path}")
        return output_path

    def get_office(self) -> AdministrationOffice:
        """Get a new AdministrationOffice entity instance.

        Returns:
            An AdministrationOffice entity instance
        """
        return AdministrationOffice(
            class_factory_util=self._class_factory_util,
            locale=self._locale,
            dataset=self._dataset,
        )

    def get_offices_by_type(self, office_type: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get administration offices of a specific type.

        Args:
            office_type: The office type to filter by
            count: The maximum number of offices to return

        Returns:
            A list of administration offices of the specified type
        """
        result = []
        attempts = 0
        max_attempts = count * 5  # Try at most 5 times per requested office
        
        while len(result) < count and attempts < max_attempts:
            office = self.get_office()
            if office_type.lower() in office.type.lower():
                result.append(office.to_dict())
            office.reset()
            attempts += 1
            
        # If we couldn't find enough offices with the exact type, force the type for the remaining
        if len(result) < count:
            remaining = count - len(result)
            for _ in range(remaining):
                office = self.get_office()
                office_dict = office.to_dict()
                office_dict["type"] = office_type
                result.append(office_dict)
                office.reset()
                
        return result

    def get_offices_by_jurisdiction(self, jurisdiction: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get administration offices of a specific jurisdiction.

        Args:
            jurisdiction: The jurisdiction to filter by
            count: The maximum number of offices to return

        Returns:
            A list of administration offices of the specified jurisdiction
        """
        result = []
        attempts = 0
        max_attempts = count * 5  # Try at most 5 times per requested office
        
        while len(result) < count and attempts < max_attempts:
            office = self.get_office()
            if jurisdiction.lower() in office.jurisdiction.lower():
                result.append(office.to_dict())
            office.reset()
            attempts += 1
            
        # If we couldn't find enough offices with the exact jurisdiction, force the jurisdiction for the remaining
        if len(result) < count:
            remaining = count - len(result)
            for _ in range(remaining):
                office = self.get_office()
                office_dict = office.to_dict()
                office_dict["jurisdiction"] = jurisdiction
                result.append(office_dict)
                office.reset()
                
        return result
    
    def get_offices_by_budget_range(self, min_budget: float, max_budget: float, count: int = 10) -> List[Dict[str, Any]]:
        """Get administration offices within a specific budget range.

        Args:
            min_budget: The minimum annual budget
            max_budget: The maximum annual budget
            count: The maximum number of offices to return

        Returns:
            A list of administration offices within the specified budget range
        """
        result = []
        attempts = 0
        max_attempts = count * 10  # Try at most 10 times per requested office
        
        while len(result) < count and attempts < max_attempts:
            office = self.get_office()
            if min_budget <= office.annual_budget <= max_budget:
                result.append(office.to_dict())
            office.reset()
            attempts += 1
            
        return result
    
    def get_municipal_offices(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get municipal government offices.

        Args:
            count: The maximum number of offices to return

        Returns:
            A list of municipal government offices
        """
        return self.get_offices_by_type("Municipal Government Office", count)
    
    def get_state_offices(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get state government offices.

        Args:
            count: The maximum number of offices to return

        Returns:
            A list of state government offices
        """
        return self.get_offices_by_type("State Government Agency", count)
    
    def get_federal_offices(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get federal government offices.

        Args:
            count: The maximum number of offices to return

        Returns:
            A list of federal government offices
        """
        return self.get_offices_by_type("Federal Government Office", count)