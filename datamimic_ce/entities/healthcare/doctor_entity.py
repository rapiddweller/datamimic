# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
This module serves as a compatibility layer for the DoctorEntity class.
It imports the actual implementation from the doctor_entity package.
"""

from pathlib import Path
from typing import TypeVar

# Import the actual implementation from the package
from datamimic_ce.entities.healthcare.doctor_entity.core import DoctorEntity as DoctorEntityImpl
from datamimic_ce.entities.healthcare.doctor_entity.data_loader import DoctorDataLoader
from datamimic_ce.entities.healthcare.doctor_entity.utils import parse_weighted_value, weighted_choice

T = TypeVar("T")


# For backward compatibility
class DoctorEntity(DoctorEntityImpl):
    """Generate doctor data.

    This class generates realistic doctor data including doctor IDs,
    names, specialties, license numbers, contact information, education,
    certifications, and schedules.

    This is a compatibility wrapper around the actual implementation in the doctor_entity package.
    """

    # Module-level cache for data to reduce file I/O (for backward compatibility)
    _DATA_CACHE: dict[str, list[str]] = {}
    # Module-level cache for dictionary data (for backward compatibility)
    _DICT_CACHE: dict[str, dict[str, str]] = {}

    @staticmethod
    def _load_simple_csv(file_path: Path) -> list[str]:
        """Load a simple CSV file and return a list of values.

        This is a compatibility method that delegates to DoctorDataLoader.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of values from the CSV file
        """
        # Call the actual implementation but convert the result to the expected format
        result = DoctorDataLoader._load_simple_csv(file_path)
        # Convert list of tuples to list of strings for backward compatibility
        return [f"{value},{weight}" if weight != 1.0 else value for value, weight in result]

    @classmethod
    def _get_country_specific_data(cls, data_type: str, country_code: str = "US") -> list[str]:
        """Get country-specific data from CSV files.

        This is a compatibility method that delegates to DoctorDataLoader.

        Args:
            data_type: Type of data to retrieve (e.g., "specialties", "hospitals")
            country_code: Country code (default: "US")

        Returns:
            List of values from the CSV file
        """
        result = DoctorDataLoader.get_country_specific_data(data_type, country_code.upper())
        return [item[0] for item in result]  # Extract just the values, not the weights

    @staticmethod
    def _weighted_choice(values: list[str]) -> str:
        """Choose a value from a list based on weights.

        This is a compatibility method that delegates to the utils module.

        Args:
            values: List of values, potentially with weights

        Returns:
            A chosen value
        """
        return weighted_choice(values)

    @staticmethod
    def _parse_weighted_value(value: str) -> tuple[str, float]:
        """Parse a weighted value from a CSV file.

        This is a compatibility method that delegates to the utils module.

        Args:
            value: The value to parse

        Returns:
            A tuple of (value, weight)
        """
        return parse_weighted_value(value)

    # Override properties to ensure they never return empty values by forcing regeneration
    @property
    def specialty(self) -> str:
        """Get the specialty."""
        value = super().specialty
        if not value:
            # Force regeneration by clearing the cache for this property
            self._property_cache.clear()
            return super().specialty
        return value

    @property
    def license_number(self) -> str:
        """Get the license number."""
        value = super().license_number
        if not value:
            # Force regeneration by clearing the cache for this property
            self._property_cache.clear()
            return super().license_number
        return value

    @property
    def contact_number(self) -> str:
        """Get the contact number."""
        value = super().contact_number
        if not value:
            # Force regeneration by clearing the cache for this property
            self._property_cache.clear()
            return super().contact_number
        return value

    @property
    def hospital_affiliation(self) -> str:
        """Get the hospital affiliation."""
        value = super().hospital_affiliation
        if not value:
            # Force regeneration by clearing the cache for this property
            self._property_cache.clear()
            return super().hospital_affiliation
        return value

    @property
    def first_name(self) -> str:
        """Get the first name."""
        value = super().first_name
        if not value:
            # Force regeneration by clearing the cache for this property
            self._property_cache.clear()
            return super().first_name
        return value

    @property
    def last_name(self) -> str:
        """Get the last name."""
        value = super().last_name
        if not value:
            # Force regeneration by clearing the cache for this property
            self._property_cache.clear()
            return super().last_name
        return value
