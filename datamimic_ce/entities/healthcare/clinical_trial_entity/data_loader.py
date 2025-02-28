# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Data loader for the Clinical Trial Entity.

This module provides functionality for loading data from CSV files for clinical trials.
"""

import csv
from pathlib import Path

from datamimic_ce.logger import logger
from datamimic_ce.utils.data_path_util import DataPathUtil


class ClinicalTrialDataLoader:
    """Load data from CSV files for clinical trials."""

    # Class-level caches to optimize file I/O
    _PHASES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _STATUSES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _SPONSORS_CACHE: dict[str, list[tuple[str, float]]] = {}
    _CONDITIONS_CACHE: dict[str, list[tuple[str, float]]] = {}
    _INTERVENTION_TYPES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _INCLUSION_CRITERIA_CACHE: dict[str, list[tuple[str, float]]] = {}
    _EXCLUSION_CRITERIA_CACHE: dict[str, list[tuple[str, float]]] = {}

    @classmethod
    def _load_simple_csv(cls, file_path: Path) -> list[tuple[str, float]]:
        """Load a simple CSV file and return a list of values with weights.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of tuples containing values and weights
        """
        if not file_path.exists():
            logger.warning(f"CSV file not found: {file_path}")
            return []

        try:
            with open(file_path, encoding="utf-8") as f:
                reader = csv.reader(f)
                values = []
                for row in reader:
                    if not row:
                        continue
                    if len(row) >= 2:
                        try:
                            weight = float(row[1])
                            values.append((row[0], weight))
                        except (ValueError, IndexError):
                            # If weight is not a valid number, use default weight of 1.0
                            values.append((row[0], 1.0))
                    else:
                        # If no weight is provided, use default weight of 1.0
                        values.append((row[0], 1.0))
                return values
        except Exception as e:
            logger.error(f"Error loading CSV file {file_path}: {e}")
            return []

    @classmethod
    def get_country_specific_data(cls, data_type: str, country_code: str = "US") -> list[tuple[str, float]]:
        """Get country-specific data from CSV files.

        Args:
            data_type: Type of data to retrieve (e.g., "phases", "statuses")
            country_code: Country code (default: "US")

        Returns:
            List of tuples containing values and weights
        """
        # Get the appropriate cache for the data type
        cache = cls._get_cache_for_data_type(data_type)
        cache_key = f"{data_type}_{country_code}"

        # Check if the data is already cached
        if cache_key in cache:
            return cache[cache_key]

        # Determine the file path based on data type and country code
        file_path = DataPathUtil.get_country_specific_data_file_path("medical/clinical_trials", data_type, country_code)

        # Load the data from the CSV file
        data = cls._load_simple_csv(file_path)

        # If no data was found, try to load the default (US) data
        if not data and country_code != "US":
            file_path = DataPathUtil.get_country_specific_data_file_path("medical/clinical_trials", data_type, "US")
            data = cls._load_simple_csv(file_path)

        # If still no data, use default values
        if not data:
            data = cls._get_default_values(data_type)

        # Cache the data for future use
        cache[cache_key] = data
        return data

    @classmethod
    def _get_cache_for_data_type(cls, data_type: str) -> dict[str, list[tuple[str, float]]]:
        """Get the appropriate cache for the data type.

        Args:
            data_type: Type of data to retrieve

        Returns:
            The appropriate cache dictionary
        """
        if data_type == "phases":
            return cls._PHASES_CACHE
        elif data_type == "statuses":
            return cls._STATUSES_CACHE
        elif data_type == "sponsors":
            return cls._SPONSORS_CACHE
        elif data_type == "medical_conditions":
            return cls._CONDITIONS_CACHE
        elif data_type == "intervention_types":
            return cls._INTERVENTION_TYPES_CACHE
        elif data_type == "inclusion_criteria":
            return cls._INCLUSION_CRITERIA_CACHE
        elif data_type == "exclusion_criteria":
            return cls._EXCLUSION_CRITERIA_CACHE
        else:
            # For unknown data types, create a new cache entry
            logger.warning(f"Unknown data type: {data_type}, creating new cache entry")
            setattr(cls, f"_{data_type.upper()}_CACHE", {})
            return getattr(cls, f"_{data_type.upper()}_CACHE")

    @classmethod
    def _get_default_values(cls, data_type: str) -> list[tuple[str, float]]:
        """Get default values for a data type.

        Args:
            data_type: Type of data to retrieve

        Returns:
            List of tuples containing default values and weights
        """
        if data_type == "phases":
            return [
                ("Phase 1", 20),
                ("Phase 2", 30),
                ("Phase 3", 30),
                ("Phase 4", 10),
                ("Early Phase 1", 5),
                ("Not Applicable", 5),
            ]
        elif data_type == "statuses":
            return [
                ("Recruiting", 40),
                ("Completed", 30),
                ("Active, not recruiting", 15),
                ("Not yet recruiting", 10),
                ("Terminated", 3),
                ("Withdrawn", 2),
            ]
        elif data_type == "sponsors":
            return [
                ("National Institutes of Health", 20),
                ("Mayo Clinic", 15),
                ("Johns Hopkins University", 15),
                ("Stanford University", 10),
                ("Harvard Medical School", 10),
                ("University of California", 10),
                ("Pfizer", 5),
                ("Novartis", 5),
                ("Merck", 5),
                ("GlaxoSmithKline", 5),
            ]
        elif data_type == "medical_conditions":
            return [
                ("Diabetes", 15),
                ("Hypertension", 15),
                ("Cancer", 10),
                ("Heart Disease", 10),
                ("Alzheimer's Disease", 5),
                ("Parkinson's Disease", 5),
                ("Multiple Sclerosis", 5),
                ("Asthma", 5),
                ("COPD", 5),
                ("Depression", 5),
                ("Anxiety", 5),
                ("Obesity", 5),
                ("Arthritis", 5),
                ("Osteoporosis", 5),
            ]
        elif data_type == "intervention_types":
            return [
                ("Drug", 40),
                ("Behavioral", 15),
                ("Device", 15),
                ("Procedure", 10),
                ("Diagnostic Test", 10),
                ("Dietary Supplement", 5),
                ("Radiation", 5),
            ]
        else:
            logger.warning(f"No default values for data type: {data_type}")
            return []
