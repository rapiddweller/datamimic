# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Data loader for doctor entity.

This module provides functionality for loading data from CSV files for doctor entities.
"""

import csv
from pathlib import Path

from datamimic_ce.logger import logger
from datamimic_ce.utils.data_path_util import DataPathUtil


class DoctorDataLoader:
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

    @classmethod
    def _load_simple_csv(cls, file_path: Path) -> list[tuple[str, float]]:
        """Load a simple CSV file and return a list of values with weights.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of tuples (value, weight) from the CSV file
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
            data_type: Type of data to retrieve (e.g., "specialties", "hospitals")
            country_code: Country code (default: "US")

        Returns:
            List of tuples (value, weight) from the CSV file
        """
        # Get the appropriate cache for the data type
        cache = cls._get_cache_for_data_type(data_type)
        cache_key = f"{data_type}_{country_code}"

        # Check if data is already in cache
        if cache_key in cache:
            return cache[cache_key]

        # Get the file path for the country-specific data
        file_path = DataPathUtil.get_country_specific_data_file_path("medical", data_type, country_code)

        # Load the data from the CSV file
        data = cls._load_simple_csv(file_path)

        # If no data was found, try to load the default (US) data
        if not data and country_code != "US":
            file_path = DataPathUtil.get_country_specific_data_file_path("medical", data_type, "US")
            data = cls._load_simple_csv(file_path)

        # If still no data, use default values
        if not data:
            data = cls._get_default_values(data_type)

        # Cache the data for future use
        cache[cache_key] = data
        return data

    @classmethod
    def _get_cache_for_data_type(cls, data_type: str) -> dict[str, list[tuple[str, float]]]:
        """Get the appropriate cache dictionary for a data type.

        Args:
            data_type: The type of data

        Returns:
            The cache dictionary for the data type
        """
        if data_type == "specialties":
            return cls._SPECIALTIES_CACHE
        elif data_type == "hospitals":
            return cls._HOSPITALS_CACHE
        elif data_type == "medical_schools":
            return cls._MEDICAL_SCHOOLS_CACHE
        elif data_type == "certifications":
            return cls._CERTIFICATIONS_CACHE
        elif data_type == "languages":
            return cls._LANGUAGES_CACHE
        elif data_type == "institutions":
            return cls._INSTITUTIONS_CACHE
        elif data_type == "degrees":
            return cls._DEGREES_CACHE
        elif data_type == "doctor_titles":
            return cls._DOCTOR_TITLES_CACHE
        else:
            # For unknown data types, create a new cache entry
            logger.warning(f"Unknown data type: {data_type}, creating new cache entry")
            setattr(cls, f"_{data_type.upper()}_CACHE", {})
            return getattr(cls, f"_{data_type.upper()}_CACHE")

    @classmethod
    def _get_default_values(cls, data_type: str) -> list[tuple[str, float]]:
        """Get default values for a data type when no file is found.

        Args:
            data_type: The type of data

        Returns:
            A list of default values with weights
        """
        if data_type == "specialties":
            return [
                ("Family Medicine", 10),
                ("Internal Medicine", 8),
                ("Pediatrics", 6),
                ("Cardiology", 5),
                ("Neurology", 5),
                ("Oncology", 5),
                ("Orthopedics", 5),
                ("Psychiatry", 5),
                ("Dermatology", 4),
                ("Emergency Medicine", 4),
            ]
        elif data_type == "hospitals":
            return [
                ("General Hospital", 10),
                ("University Medical Center", 8),
                ("Community Hospital", 6),
                ("Regional Medical Center", 5),
                ("Memorial Hospital", 5),
                ("Children's Hospital", 4),
                ("Veterans Hospital", 3),
            ]
        elif data_type == "medical_schools":
            return [
                ("Harvard Medical School", 10),
                ("Johns Hopkins School of Medicine", 9),
                ("Stanford University School of Medicine", 8),
                ("University of California, San Francisco", 7),
                ("Mayo Clinic Alix School of Medicine", 6),
                ("University of Pennsylvania Perelman School of Medicine", 5),
                ("Columbia University Vagelos College of Physicians and Surgeons", 5),
                ("University of California, Los Angeles", 4),
                ("Washington University School of Medicine", 4),
                ("Yale School of Medicine", 4),
            ]
        elif data_type == "certifications":
            return [
                ("Board Certified", 10),
                ("Advanced Cardiac Life Support", 8),
                ("Basic Life Support", 8),
                ("Pediatric Advanced Life Support", 6),
                ("Advanced Trauma Life Support", 6),
                ("Neonatal Resuscitation Program", 5),
                ("Certified Diabetes Educator", 4),
                ("Certified Wound Specialist", 3),
                ("Certified Stroke Rehabilitation Specialist", 3),
                ("Pain Management Certification", 3),
            ]
        elif data_type == "languages":
            return [
                ("English", 10),
                ("Spanish", 5),
                ("French", 3),
                ("German", 2),
                ("Mandarin", 2),
                ("Arabic", 2),
                ("Russian", 1),
                ("Portuguese", 1),
                ("Italian", 1),
                ("Japanese", 1),
            ]
        elif data_type == "institutions":
            return [
                ("Mayo Clinic", 10),
                ("Cleveland Clinic", 9),
                ("Massachusetts General Hospital", 8),
                ("Johns Hopkins Hospital", 8),
                ("UCLA Medical Center", 7),
                ("New York-Presbyterian Hospital", 7),
                ("UCSF Medical Center", 6),
                ("Stanford Health Care", 6),
                ("Cedars-Sinai Medical Center", 5),
                ("Northwestern Memorial Hospital", 5),
            ]
        elif data_type == "degrees":
            return [
                ("MD", 10),
                ("DO", 8),
                ("MBBS", 6),
                ("PhD", 4),
                ("MPH", 3),
                ("MS", 3),
                ("MBA", 2),
                ("PA", 2),
                ("NP", 2),
                ("RN", 1),
            ]
        elif data_type == "doctor_titles":
            return [
                ("Dr.", 10),
                ("Professor", 5),
                ("Associate Professor", 4),
                ("Assistant Professor", 3),
                ("Chief", 2),
                ("Director", 2),
                ("Head", 1),
            ]
        else:
            logger.warning(f"No default values for data type: {data_type}")
            return []
