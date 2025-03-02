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
        default_values = {
            "specialties": [
                ("Family Medicine", 10.0),
                ("Internal Medicine", 8.0),
                ("Pediatrics", 6.0),
                ("Cardiology", 5.0),
                ("Neurology", 5.0),
                ("Oncology", 5.0),
                ("Orthopedics", 5.0),
                ("Psychiatry", 5.0),
                ("Dermatology", 4.0),
                ("Emergency Medicine", 4.0),
            ],
            "hospitals": [
                ("General Hospital", 10.0),
                ("University Medical Center", 8.0),
                ("Community Hospital", 6.0),
                ("Regional Medical Center", 5.0),
                ("Memorial Hospital", 5.0),
                ("Children's Hospital", 4.0),
                ("Veterans Hospital", 3.0),
            ],
            "medical_schools": [
                ("Harvard Medical School", 10.0),
                ("Johns Hopkins School of Medicine", 9.0),
                ("Stanford University School of Medicine", 8.0),
                ("University of California, San Francisco", 7.0),
                ("Mayo Clinic Alix School of Medicine", 6.0),
                ("University of Pennsylvania Perelman School of Medicine", 5.0),
                ("Columbia University Vagelos College of Physicians and Surgeons", 5.0),
                ("University of California, Los Angeles", 4.0),
                ("Washington University School of Medicine", 4.0),
                ("Yale School of Medicine", 4.0),
            ],
            "certifications": [
                ("Board Certified", 10.0),
                ("Advanced Cardiac Life Support", 8.0),
                ("Basic Life Support", 8.0),
                ("Pediatric Advanced Life Support", 6.0),
                ("Advanced Trauma Life Support", 6.0),
                ("Neonatal Resuscitation Program", 5.0),
                ("Certified Diabetes Educator", 4.0),
                ("Certified Wound Specialist", 3.0),
                ("Certified Stroke Rehabilitation Specialist", 3.0),
                ("Pain Management Certification", 3.0),
            ],
            "languages": [
                ("English", 10.0),
                ("Spanish", 5.0),
                ("French", 3.0),
                ("German", 2.0),
                ("Mandarin", 2.0),
                ("Arabic", 2.0),
                ("Russian", 1.0),
                ("Portuguese", 1.0),
                ("Italian", 1.0),
                ("Japanese", 1.0),
            ],
            "institutions": [
                ("Mayo Clinic", 10.0),
                ("Cleveland Clinic", 9.0),
                ("Massachusetts General Hospital", 8.0),
                ("Johns Hopkins Hospital", 8.0),
                ("UCLA Medical Center", 7.0),
                ("New York-Presbyterian Hospital", 7.0),
                ("UCSF Medical Center", 6.0),
                ("Stanford Health Care", 6.0),
                ("Cedars-Sinai Medical Center", 5.0),
                ("Northwestern Memorial Hospital", 5.0),
            ],
            "degrees": [
                ("MD", 10.0),
                ("DO", 8.0),
                ("MBBS", 6.0),
                ("PhD", 4.0),
                ("MPH", 3.0),
                ("MS", 3.0),
                ("MBA", 2.0),
                ("PA", 2.0),
                ("NP", 2.0),
                ("RN", 1.0),
            ],
            "doctor_titles": [
                ("Dr.", 10.0),
                ("Professor", 5.0),
                ("Associate Professor", 4.0),
                ("Assistant Professor", 3.0),
                ("Chief", 2.0),
                ("Director", 2.0),
                ("Head", 1.0),
            ],
        }

        return default_values.get(data_type, [])
