# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Data loader for the Medical Record Entity.

This module provides functionality for loading data from CSV files for medical records.
"""

from datamimic_ce.entities.base_data_loader import BaseDataLoader


class MedicalRecordDataLoader(BaseDataLoader):
    """Load data from CSV files for medical records."""

    # Class-level caches to optimize file I/O
    _VISIT_TYPES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _CHIEF_COMPLAINTS_CACHE: dict[str, list[tuple[str, float]]] = {}
    _DIAGNOSIS_CODES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _PROCEDURE_CODES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _MEDICATIONS_CACHE: dict[str, list[tuple[str, float]]] = {}
    _LAB_TESTS_CACHE: dict[str, list[tuple[str, float]]] = {}
    _ALLERGIES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _SPECIMEN_TYPES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _LABS_CACHE: dict[str, list[tuple[str, float]]] = {}
    _STATUSES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _MEDICAL_CONDITIONS_CACHE: dict[str, list[tuple[str, float]]] = {}

    def __init__(self, country_code: str = "US") -> None:
        """Initialize a new MedicalRecordDataLoader.

        Args:
            country_code: The country code to use for loading data.
        """
        super().__init__()
        self._country_code = country_code
        # Setting the entity type and subdirectory separately for correct path handling
        self._entity_type = "medical"
        self._subdirectory = "medical_records"
        # Combine them for domain_path to ensure compatibility with get_country_specific_data
        self._domain_path = f"{self._entity_type}/{self._subdirectory}"

    def get_visit_types(self) -> list[tuple[str, float]]:
        """Get visit types.

        Returns:
            A list of tuples containing visit types and weights.
        """
        return self.get_country_specific_data("visit_types", self._country_code, self._domain_path)

    def get_chief_complaints(self) -> list[tuple[str, float]]:
        """Get chief complaints.

        Returns:
            A list of tuples containing chief complaints and weights.
        """
        return self.get_country_specific_data("chief_complaints", self._country_code, self._domain_path)

    def get_diagnosis_codes(self) -> list[tuple[str, float]]:
        """Get diagnosis codes.

        Returns:
            A list of tuples containing diagnosis codes and weights.
        """
        return self.get_country_specific_data("diagnosis_codes", self._country_code, self._domain_path)

    def get_procedure_codes(self) -> list[tuple[str, float]]:
        """Get procedure codes.

        Returns:
            A list of tuples containing procedure codes and weights.
        """
        return self.get_country_specific_data("procedure_codes", self._country_code, self._domain_path)

    def get_medications(self) -> list[tuple[str, float]]:
        """Get medications.

        Returns:
            A list of tuples containing medications and weights.
        """
        return self.get_country_specific_data("medications", self._country_code, self._domain_path)

    def get_lab_tests(self) -> list[tuple[str, float]]:
        """Get lab tests.

        Returns:
            A list of tuples containing lab tests and weights.
        """
        return self.get_country_specific_data("lab_tests", self._country_code, self._domain_path)

    def get_allergies(self) -> list[tuple[str, float]]:
        """Get allergies.

        Returns:
            A list of tuples containing allergies and weights.
        """
        return self.get_country_specific_data("allergies", self._country_code, self._domain_path)

    def get_specimen_types(self) -> list[tuple[str, float]]:
        """Get specimen types.

        Returns:
            A list of tuples containing specimen types and weights.
        """
        return self.get_country_specific_data("specimen_types", self._country_code, self._domain_path)

    def get_labs(self) -> list[tuple[str, float]]:
        """Get labs.

        Returns:
            A list of tuples containing labs and weights.
        """
        return self.get_country_specific_data("labs", self._country_code, self._domain_path)

    def get_statuses(self) -> list[tuple[str, float]]:
        """Get statuses.

        Returns:
            A list of tuples containing statuses and weights.
        """
        return self.get_country_specific_data("statuses", self._country_code, self._domain_path)

    def get_medical_conditions(self) -> list[tuple[str, float]]:
        """Get medical conditions.

        Returns:
            A list of tuples containing medical conditions and weights.
        """
        return self.get_country_specific_data("medical_conditions", self._country_code, self._domain_path)

    @classmethod
    def _get_default_values(cls, data_type: str) -> list[tuple[str, float]]:
        """Get default values for a data type.

        Args:
            data_type: Type of data to retrieve

        Returns:
            List of tuples containing default values and weights
        """
        # Return an empty list to force the use of data files
        # No hardcoded fallbacks
        return []

    @classmethod
    def _get_cache_for_data_type(cls, data_type: str) -> dict[str, list[tuple[str, float]]]:
        """Get the appropriate cache for the data type.

        Args:
            data_type: Type of data to retrieve

        Returns:
            The appropriate cache dictionary
        """
        cache_dict = {
            "visit_types": cls._VISIT_TYPES_CACHE,
            "chief_complaints": cls._CHIEF_COMPLAINTS_CACHE,
            "diagnosis_codes": cls._DIAGNOSIS_CODES_CACHE,
            "procedure_codes": cls._PROCEDURE_CODES_CACHE,
            "medications": cls._MEDICATIONS_CACHE,
            "lab_tests": cls._LAB_TESTS_CACHE,
            "allergies": cls._ALLERGIES_CACHE,
            "specimen_types": cls._SPECIMEN_TYPES_CACHE,
            "labs": cls._LABS_CACHE,
            "statuses": cls._STATUSES_CACHE,
            "medical_conditions": cls._MEDICAL_CONDITIONS_CACHE,
        }

        return cache_dict.get(data_type, super()._get_cache_for_data_type(data_type))
