# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Data loader for doctor entity.

This module provides functionality for loading data from CSV files for doctor entities.
"""

from datamimic_ce.entities.base_data_loader import BaseDataLoader


class DoctorDataLoader(BaseDataLoader):
    """Load data for doctor entity from CSV files."""

    # Cache for loaded data to reduce file I/O
    _SPECIALTIES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _HOSPITALS_CACHE: dict[str, list[tuple[str, float]]] = {}
    _MEDICAL_SCHOOLS_CACHE: dict[str, list[tuple[str, float]]] = {}
    _CERTIFICATIONS_CACHE: dict[str, list[tuple[str, float]]] = {}
    _LANGUAGES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _INSTITUTIONS_CACHE: dict[str, list[tuple[str, float]]] = {}
    _DEGREES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _DOCTOR_TITLES_CACHE: dict[str, list[tuple[str, float]]] = {}

    def __init__(self) -> None:
        """Initialize a new DoctorDataLoader."""
        self._domain_path = "medical"

    def get_data(self, data_type: str, country_code: str = "US") -> list[tuple[str, float]]:
        """Get data for a specific type and country code.

        Args:
            data_type: The type of data to retrieve
            country_code: The country code to use

        Returns:
            A list of tuples containing values and weights
        """
        return self.get_country_specific_data(data_type, country_code, self._domain_path)

    @classmethod
    def _get_cache_for_data_type(cls, data_type: str) -> dict[str, list[tuple[str, float]]]:
        """Get the appropriate cache dictionary for a data type.

        Args:
            data_type: The type of data

        Returns:
            The cache dictionary for the data type
        """
        cache_dict = {
            "specialties": cls._SPECIALTIES_CACHE,
            "hospitals": cls._HOSPITALS_CACHE,
            "medical_schools": cls._MEDICAL_SCHOOLS_CACHE,
            "certifications": cls._CERTIFICATIONS_CACHE,
            "languages": cls._LANGUAGES_CACHE,
            "institutions": cls._INSTITUTIONS_CACHE,
            "degrees": cls._DEGREES_CACHE,
            "doctor_titles": cls._DOCTOR_TITLES_CACHE,
        }

        return cache_dict.get(data_type, super()._get_cache_for_data_type(data_type))

    @classmethod
    def _get_default_values(cls, data_type: str) -> list[tuple[str, float]]:
        """Get default values for a data type when no file is found.

        Args:
            data_type: The type of data

        Returns:
            A list of default values with weights
        """
        # Return an empty list to force the use of data files
        # No hardcoded fallbacks
        return []
