# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Data loader for doctor entity.
"""

from pathlib import Path

from datamimic_ce.logger import logger
from datamimic_ce.utils.data_path_util import DataPathUtil


class DoctorDataLoader:
    """Load data for doctor entity from CSV files."""

    # Cache for loaded data to reduce file I/O
    _specialties_cache: dict[str, list[tuple[str, float]]] = {}
    _hospitals_cache: dict[str, list[tuple[str, float]]] = {}
    _medical_schools_cache: dict[str, list[tuple[str, float]]] = {}
    _certifications_cache: dict[str, list[tuple[str, float]]] = {}
    _languages_cache: dict[str, list[tuple[str, float]]] = {}
    _institutions_cache: dict[str, list[tuple[str, float]]] = {}
    _degrees_cache: dict[str, list[tuple[str, float]]] = {}

    @classmethod
    def _load_simple_csv(cls, file_path: Path) -> list[tuple[str, float]]:
        """Load a simple CSV file and return a list of values with weights.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of tuples (value, weight) from the CSV file
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                result = []
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    # Check if the line contains a comma (indicating a weighted value)
                    if "," in line:
                        parts = line.split(",", 1)
                        if len(parts) == 2:
                            value = parts[0].strip()
                            try:
                                # Try to convert the weight to a float
                                weight = float(parts[1].strip())
                                result.append((value, weight))
                                continue
                            except ValueError:
                                # If weight is not a number, treat the whole line as a single value
                                pass

                    # If no comma or invalid weight, add the line as a single value with weight 1.0
                    result.append((line, 1.0))

                return result
        except Exception as e:
            logger.error(f"Error loading simple CSV file {file_path}: {e}")
            return []

    @classmethod
    def get_country_specific_data(cls, data_type: str, country_code: str | None = None) -> list[tuple[str, float]]:
        """Get country-specific data from CSV files.

        Args:
            data_type: Type of data to retrieve (e.g., "specialties", "hospitals")
            country_code: Country code (default: None, which will use "US")

        Returns:
            List of tuples (value, weight) from the CSV file
        """
        # Use US as default country code if none provided
        if not country_code:
            country_code = "US"

        # Create a cache key based on data type and country code
        cache_key = f"{data_type}_{country_code}"

        # Check if data is already in cache
        cache_dict = cls._get_cache_for_data_type(data_type)
        if cache_key in cache_dict:
            return cache_dict[cache_key]

        # Get the file path for the country-specific data
        file_path = DataPathUtil.get_country_specific_data_file_path("medical", data_type, country_code)

        # If country-specific file doesn't exist, try US as fallback
        if not DataPathUtil.file_exists(file_path) and country_code != "US":
            fallback_file_path = DataPathUtil.get_country_specific_data_file_path("medical", data_type, "US")
            if DataPathUtil.file_exists(fallback_file_path):
                logger.info(f"Using US fallback for {data_type} data as {country_code} not available")
                file_path = fallback_file_path

        # If still no file, try without country code
        if not DataPathUtil.file_exists(file_path):
            # Try to find a generic file (without country code)
            generic_file_path = DataPathUtil.get_data_file_path("medical", f"{data_type}.csv")
            if DataPathUtil.file_exists(generic_file_path):
                logger.warning(f"Using generic data for {data_type} - consider creating country-specific file")
                file_path = generic_file_path

        # If file exists, load it and cache the result
        if DataPathUtil.file_exists(file_path):
            result = cls._load_simple_csv(file_path)
            cache_dict[cache_key] = result
            return result

        # If no file found, return default values
        logger.warning(f"No data file found for {data_type} with country code {country_code}")
        return cls._get_default_values(data_type)

    @classmethod
    def _get_cache_for_data_type(cls, data_type: str) -> dict[str, list[tuple[str, float]]]:
        """Get the appropriate cache dictionary for a data type.

        Args:
            data_type: The type of data

        Returns:
            The cache dictionary for the data type
        """
        if data_type == "specialties":
            return cls._specialties_cache
        elif data_type == "hospitals":
            return cls._hospitals_cache
        elif data_type == "medical_schools":
            return cls._medical_schools_cache
        elif data_type == "certifications":
            return cls._certifications_cache
        elif data_type == "languages":
            return cls._languages_cache
        elif data_type == "institutions":
            return cls._institutions_cache
        elif data_type == "degrees":
            return cls._degrees_cache
        else:
            # For unknown data types, create a new cache
            return {}

    @classmethod
    def _get_default_values(cls, data_type: str) -> list[tuple[str, float]]:
        """Get default values for a data type when no file is found.

        Args:
            data_type: The type of data

        Returns:
            A list of default values with weights
        """
        if data_type == "specialties":
            return [("Family Medicine", 10.0), ("Internal Medicine", 8.0), ("Pediatrics", 6.0)]
        elif data_type == "hospitals":
            return [("General Hospital", 10.0), ("University Medical Center", 8.0), ("Community Hospital", 6.0)]
        elif data_type == "medical_schools":
            return [("University Medical School", 10.0), ("State Medical College", 8.0)]
        elif data_type == "certifications":
            return [("Board Certified", 10.0), ("Advanced Cardiac Life Support", 8.0)]
        elif data_type == "languages":
            return [("English", 10.0), ("Spanish", 5.0), ("French", 3.0)]
        elif data_type == "institutions":
            return [("Medical University", 10.0), ("State University", 8.0)]
        elif data_type == "degrees":
            return [("MD", 10.0), ("DO", 8.0), ("MBBS", 6.0), ("PhD", 4.0)]
        else:
            return [("Default", 1.0)]
