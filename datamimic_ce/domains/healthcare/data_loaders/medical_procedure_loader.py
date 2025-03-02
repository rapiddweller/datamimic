# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Medical Procedure data loader.

This module provides the MedicalProcedureLoader class for loading medical procedure-related data.
"""

import os
from typing import Any

from datamimic_ce.core.base_data_loader import BaseDataLoader


class MedicalProcedureLoader(BaseDataLoader):
    """Load medical procedure-related data from files.

    This class loads data for medical procedure entities, including procedure categories,
    specialties, equipment, complications, and other procedure-related information.

    Data is loaded from country-specific CSV files when available,
    falling back to generic data files if needed.
    """

    # Cache for loaded data to avoid repeated file reads
    _data_cache: dict[str, dict[str, Any]] = {}

    def __init__(self):
        """Initialize the MedicalProcedureLoader."""
        super().__init__()
        self._base_path = self._get_data_path("healthcare")

    def get_data(self, data_type: str, country_code: str = "US") -> list[Any]:
        """Get data of the specified type for the specified country.

        Args:
            data_type: The type of data to get (e.g., "categories", "specialties").
            country_code: The country code to get data for.

        Returns:
            A list of data items.
        """
        # Check if data is already cached
        cache_key = f"{data_type}_{country_code}"
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        # Define file paths
        country_specific_path = os.path.join(
            self._base_path, "medical_procedure", f"{data_type}_{country_code.lower()}.csv"
        )
        generic_path = os.path.join(self._base_path, "medical_procedure", f"{data_type}.csv")

        # Try to load country-specific data first, then fall back to generic data
        data = self._load_data_with_fallback(country_specific_path, generic_path, data_type)

        # Cache the data
        self._data_cache[cache_key] = data

        return data

    def _load_data_with_fallback(self, primary_path: str, fallback_path: str, data_type: str) -> list[Any]:
        """Load data from the primary path, falling back to the fallback path if needed.

        Args:
            primary_path: The primary file path to load data from.
            fallback_path: The fallback file path to load data from.
            data_type: The type of data being loaded.

        Returns:
            A list of data items.
        """
        # Try to load from primary path
        if os.path.exists(primary_path):
            return self._load_csv_data(primary_path)

        # Fall back to generic path
        if os.path.exists(fallback_path):
            return self._load_csv_data(fallback_path)

        # If neither file exists, return default data
        return self._get_default_data(data_type)

    def _get_default_data(self, data_type: str) -> list[Any]:
        """Get default data for the specified type.

        Args:
            data_type: The type of data to get defaults for.

        Returns:
            A list of default data items.
        """
        # Default data for different types
        defaults = {
            "categories": [
                "Cardiovascular",
                "Digestive",
                "Endocrine",
                "Eye",
                "Female Genital",
                "Hemic and Lymphatic",
                "Integumentary",
                "Male Genital",
                "Maternity Care and Delivery",
                "Musculoskeletal",
                "Nervous",
                "Respiratory",
                "Urinary",
                "Radiology",
                "Pathology and Laboratory",
                "Medicine",
                "Evaluation and Management",
            ],
            "specialties": [
                "Anesthesiology",
                "Cardiology",
                "Dermatology",
                "Emergency Medicine",
                "Endocrinology",
                "Family Medicine",
                "Gastroenterology",
                "General Surgery",
                "Hematology",
                "Infectious Disease",
                "Internal Medicine",
                "Nephrology",
                "Neurology",
                "Neurosurgery",
                "Obstetrics and Gynecology",
                "Oncology",
                "Ophthalmology",
                "Orthopedic Surgery",
                "Otolaryngology",
                "Pathology",
                "Pediatrics",
                "Plastic Surgery",
                "Psychiatry",
                "Pulmonology",
                "Radiology",
                "Rheumatology",
                "Urology",
                "Vascular Surgery",
            ],
            "equipment": [
                "Anesthesia machine",
                "Autoclave",
                "Blood pressure monitor",
                "Cardiac monitor",
                "CT scanner",
                "Defibrillator",
                "ECG machine",
                "Endoscope",
                "Infusion pump",
                "Laparoscope",
                "Laryngoscope",
                "MRI machine",
                "Microscope",
                "Operating table",
                "Oxygen concentrator",
                "Patient monitor",
                "Pulse oximeter",
                "Stethoscope",
                "Surgical instruments",
                "Ultrasound machine",
                "Ventilator",
                "X-ray machine",
            ],
            "complications": [
                "Allergic reaction",
                "Bleeding",
                "Blood clots",
                "Breathing problems",
                "Cardiac complications",
                "Delayed healing",
                "Infection",
                "Nerve damage",
                "Pain",
                "Pneumonia",
                "Reaction to anesthesia",
                "Scarring",
                "Swelling",
                "Urinary retention",
                "Wound dehiscence",
            ],
        }

        return defaults.get(data_type, [])
