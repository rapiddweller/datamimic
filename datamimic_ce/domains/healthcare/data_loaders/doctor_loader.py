# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Doctor data loader.

This module provides a data loader for doctor-related data such as specialties,
hospitals, medical schools, certifications, and languages.
"""

from typing import ClassVar

from datamimic_ce.core.base_data_loader import BaseDataLoader
from datamimic_ce.domain_core.interfaces import DataLoader


class DoctorDataLoader(BaseDataLoader, DataLoader):
    """Data loader for doctor-related data.

    This class loads and caches doctor-related data such as specialties,
    hospitals, medical schools, certifications, and languages from CSV files.
    """

    # Cache dictionaries for different types of doctor data
    _SPECIALTIES_CACHE: ClassVar[dict[str, list[tuple[str, float]]]] = {}
    _HOSPITALS_CACHE: ClassVar[dict[str, list[tuple[str, float]]]] = {}
    _MEDICAL_SCHOOLS_CACHE: ClassVar[dict[str, list[tuple[str, float]]]] = {}
    _CERTIFICATIONS_CACHE: ClassVar[dict[str, list[tuple[str, float]]]] = {}
    _LANGUAGES_CACHE: ClassVar[dict[str, list[tuple[str, float]]]] = {}

    def get_data(self, data_type: str, country_code: str = "US") -> list[tuple[str, float]]:
        """Get data for a specific type and country code.

        Args:
            data_type: The type of data to retrieve (specialties, hospitals, etc.)
            country_code: The country code to use

        Returns:
            A list of tuples containing values and weights
        """
        domain_path = "healthcare/doctor"
        cache_dict = self._get_cache_for_data_type(data_type)
        return self.get_country_specific_data(data_type, country_code, domain_path, cache_dict)

    @classmethod
    def _get_cache_for_data_type(cls, data_type: str) -> dict[str, list[tuple[str, float]]]:
        """Get the appropriate cache dictionary for a data type.

        Args:
            data_type: The type of data

        Returns:
            A cache dictionary for the data type
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
        else:
            # Default to an empty dictionary for unknown data types
            return {}

    @classmethod
    def _get_default_values(cls, data_type: str) -> list[tuple[str, float]]:
        """Get default values for a data type when no data files are available.

        Args:
            data_type: The type of data

        Returns:
            A list of tuples containing default values and weights
        """
        if data_type == "specialties":
            return [
                ("Cardiology", 1.0),
                ("Dermatology", 1.0),
                ("Emergency Medicine", 1.0),
                ("Family Medicine", 1.0),
                ("Gastroenterology", 1.0),
                ("Internal Medicine", 1.0),
                ("Neurology", 1.0),
                ("Obstetrics and Gynecology", 1.0),
                ("Oncology", 1.0),
                ("Ophthalmology", 1.0),
                ("Orthopedic Surgery", 1.0),
                ("Pediatrics", 1.0),
                ("Psychiatry", 1.0),
                ("Radiology", 1.0),
                ("Surgery", 1.0),
                ("Urology", 1.0),
            ]
        elif data_type == "hospitals":
            return [
                ("General Hospital", 1.0),
                ("Memorial Hospital", 1.0),
                ("University Medical Center", 1.0),
                ("Community Hospital", 1.0),
                ("Regional Medical Center", 1.0),
                ("St. Mary's Hospital", 1.0),
                ("Mercy Hospital", 1.0),
                ("County Hospital", 1.0),
                ("Children's Hospital", 1.0),
                ("Veterans Hospital", 1.0),
            ]
        elif data_type == "medical_schools":
            return [
                ("Harvard Medical School", 1.0),
                ("Johns Hopkins School of Medicine", 1.0),
                ("Stanford University School of Medicine", 1.0),
                ("University of California, San Francisco", 1.0),
                ("Columbia University Vagelos College of Physicians and Surgeons", 1.0),
                ("Mayo Clinic Alix School of Medicine", 1.0),
                ("University of Pennsylvania Perelman School of Medicine", 1.0),
                ("Washington University School of Medicine", 1.0),
                ("Yale School of Medicine", 1.0),
                ("Duke University School of Medicine", 1.0),
            ]
        elif data_type == "certifications":
            return [
                ("Board Certified", 1.0),
                ("American Board of Medical Specialties", 1.0),
                ("Fellow of the American College of Physicians", 1.0),
                ("Fellow of the American College of Surgeons", 1.0),
                ("American Board of Internal Medicine", 1.0),
                ("American Board of Pediatrics", 1.0),
                ("American Board of Surgery", 1.0),
                ("American Board of Psychiatry and Neurology", 1.0),
                ("American Board of Radiology", 1.0),
                ("American Board of Family Medicine", 1.0),
            ]
        elif data_type == "languages":
            return [
                ("English", 1.0),
                ("Spanish", 0.5),
                ("French", 0.3),
                ("German", 0.2),
                ("Mandarin", 0.2),
                ("Arabic", 0.1),
                ("Russian", 0.1),
                ("Hindi", 0.1),
                ("Portuguese", 0.1),
                ("Japanese", 0.1),
            ]
        else:
            return []
