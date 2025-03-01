# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Data loader for the Clinical Trial Entity.

This module provides functionality for loading data from CSV files for clinical trials.
"""

from datamimic_ce.entities.base_data_loader import BaseDataLoader
from datamimic_ce.utils.data_path_util import DataPathUtil


class ClinicalTrialDataLoader(BaseDataLoader):
    """Load data from CSV files for clinical trials."""

    # Class-level caches to optimize file I/O
    _PHASES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _STATUSES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _SPONSORS_CACHE: dict[str, list[tuple[str, float]]] = {}
    _CONDITIONS_CACHE: dict[str, list[tuple[str, float]]] = {}
    _INTERVENTION_TYPES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _INCLUSION_CRITERIA_CACHE: dict[str, list[tuple[str, float]]] = {}
    _EXCLUSION_CRITERIA_CACHE: dict[str, list[tuple[str, float]]] = {}

    def __init__(self) -> None:
        """Initialize a new ClinicalTrialDataLoader."""
        # Setting the entity type and subdirectory separately for correct path handling
        self._entity_type = "medical"
        self._subdirectory = "clinical_trials"
        # Combine them for domain_path to ensure compatibility with get_country_specific_data
        self._domain_path = f"{self._entity_type}/{self._subdirectory}"

    def get_data(self, data_type: str, country_code: str = "US") -> list[tuple[str, float]]:
        """Get data for a specific type and country code.

        Args:
            data_type: The type of data to retrieve
            country_code: The country code to use

        Returns:
            A list of tuples containing values and weights
        """
        # First try using the country_specific_data method which uses domain_path
        data = self.get_country_specific_data(data_type, country_code, self._domain_path)
        
        # If that fails, try more directly with subdirectory path
        if not data:
            # Get the subdirectory path for clinical trials
            subdir_path = DataPathUtil.get_subdirectory_path(self._entity_type, self._subdirectory)
            
            # Construct the file path manually with correct subdirectories
            file_path = subdir_path / f"{data_type}_{country_code}.csv"
            
            # Try to load data using the manual path
            data = self._load_simple_csv(file_path)
            
        # If still no data was found, fall back to default values
        if not data:
            return self._get_default_values(data_type)
            
        return data

    @classmethod
    def _get_default_values(cls, data_type: str) -> list[tuple[str, float]]:
        """Get default values for a specific data type when CSV loading fails.
        
        Args:
            data_type: The type of data to retrieve
            
        Returns:
            A list of tuples containing default values and weights
        """
        default_values = {
            "phases": [
                ("Phase 1", 100.0),
                ("Phase 2", 150.0),
                ("Phase 3", 120.0),
                ("Phase 4", 80.0),
                ("Early Phase 1", 50.0),
                ("Phase 1/Phase 2", 70.0),
                ("Phase 2/Phase 3", 60.0),
                ("Not Applicable", 40.0),
            ],
            "statuses": [
                ("Not yet recruiting", 80.0),
                ("Recruiting", 150.0),
                ("Enrolling by invitation", 60.0),
                ("Active, not recruiting", 100.0),
                ("Suspended", 30.0),
                ("Terminated", 40.0),
                ("Completed", 120.0),
                ("Withdrawn", 20.0),
                ("Unknown status", 10.0),
            ],
            "sponsors": [
                ("Pfizer Inc.", 100.0),
                ("Novartis Pharmaceuticals", 90.0),
                ("Merck & Co., Inc.", 85.0),
                ("Johnson & Johnson", 80.0),
                ("GlaxoSmithKline", 75.0),
                ("AstraZeneca", 70.0),
                ("National Institutes of Health", 65.0),
            ],
            "medical_conditions": [
                ("Alzheimer's Disease", 50.0),
                ("Arthritis", 60.0),
                ("Asthma", 70.0),
                ("Diabetes Type 2", 80.0),
                ("Heart Failure", 70.0),
                ("Hypertension", 100.0),
                ("Cancer", 90.0),
            ],
            "intervention_types": [
                ("Drug", 150.0),
                ("Device", 80.0),
                ("Biological", 70.0),
                ("Procedure", 60.0),
                ("Behavioral", 50.0),
                ("Dietary Supplement", 40.0),
            ],
        }
        
        return default_values.get(data_type, [])

    @classmethod
    def _get_cache_for_data_type(cls, data_type: str) -> dict[str, list[tuple[str, float]]]:
        """Get the appropriate cache for the data type.

        Args:
            data_type: Type of data to retrieve

        Returns:
            The appropriate cache dictionary
        """
        cache_dict = {
            "phases": cls._PHASES_CACHE,
            "statuses": cls._STATUSES_CACHE,
            "sponsors": cls._SPONSORS_CACHE,
            "medical_conditions": cls._CONDITIONS_CACHE,
            "intervention_types": cls._INTERVENTION_TYPES_CACHE,
            "inclusion_criteria": cls._INCLUSION_CRITERIA_CACHE,
            "exclusion_criteria": cls._EXCLUSION_CRITERIA_CACHE,
        }

        return cache_dict.get(data_type, super()._get_cache_for_data_type(data_type))
