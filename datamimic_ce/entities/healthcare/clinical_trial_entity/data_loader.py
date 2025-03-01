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
        self._domain_path = "medical/clinical_trials"

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

    @classmethod
    def _get_default_values(cls, data_type: str) -> list[tuple[str, float]]:
        """Get default values for a data type.

        Args:
            data_type: Type of data to retrieve

        Returns:
            List of tuples containing default values and weights
        """
        default_values = {
            "phases": [
                ("Phase 1", 20.0),
                ("Phase 2", 30.0),
                ("Phase 3", 30.0),
                ("Phase 4", 10.0),
                ("Early Phase 1", 5.0),
                ("Not Applicable", 5.0),
            ],
            "statuses": [
                ("Recruiting", 40.0),
                ("Completed", 30.0),
                ("Active, not recruiting", 15.0),
                ("Not yet recruiting", 10.0),
                ("Terminated", 3.0),
                ("Withdrawn", 2.0),
            ],
            "sponsors": [
                ("National Institutes of Health", 20.0),
                ("Mayo Clinic", 15.0),
                ("Johns Hopkins University", 15.0),
                ("Stanford University", 10.0),
                ("Harvard Medical School", 10.0),
                ("University of California", 10.0),
                ("Pfizer", 5.0),
                ("Novartis", 5.0),
                ("Merck", 5.0),
                ("GlaxoSmithKline", 5.0),
            ],
            "medical_conditions": [
                ("Diabetes", 15.0),
                ("Hypertension", 15.0),
                ("Cancer", 10.0),
                ("Heart Disease", 10.0),
                ("Alzheimer's Disease", 5.0),
                ("Parkinson's Disease", 5.0),
                ("Multiple Sclerosis", 5.0),
                ("Asthma", 5.0),
                ("COPD", 5.0),
                ("Depression", 5.0),
                ("Anxiety", 5.0),
                ("Obesity", 5.0),
                ("Arthritis", 5.0),
                ("Osteoporosis", 5.0),
            ],
            "intervention_types": [
                ("Drug", 40.0),
                ("Behavioral", 15.0),
                ("Device", 15.0),
                ("Procedure", 10.0),
                ("Diagnostic Test", 10.0),
                ("Dietary Supplement", 5.0),
                ("Radiation", 5.0),
            ],
        }

        return default_values.get(data_type, [])
