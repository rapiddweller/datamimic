# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Hospital data loader.

This module provides the HospitalDataLoader class for loading hospital-related data.
"""

import os
from typing import Any

from datamimic_ce.core.base_data_loader import BaseDataLoader


class HospitalDataLoader(BaseDataLoader):
    """Load hospital-related data from files.

    This class loads data for hospital entities, including hospital types,
    departments, services, accreditations, and other hospital-related information.

    Data is loaded from country-specific CSV files when available,
    falling back to generic data files if needed.
    """

    # Cache for loaded data to avoid repeated file reads
    _data_cache: dict[str, dict[str, Any]] = {}

    def __init__(self):
        """Initialize the HospitalDataLoader."""
        super().__init__()
        self._base_path = self._get_data_path("healthcare")

    def get_data(self, data_type: str, country_code: str = "US") -> list[Any]:
        """Get data of the specified type for the specified country.

        Args:
            data_type: The type of data to get (e.g., "hospital_types", "departments").
            country_code: The country code to get data for.

        Returns:
            A list of data items.
        """
        # Check if data is already cached
        cache_key = f"{data_type}_{country_code}"
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        # Define file paths
        country_specific_path = os.path.join(self._base_path, "hospital", f"{data_type}_{country_code.lower()}.csv")
        generic_path = os.path.join(self._base_path, "hospital", f"{data_type}.csv")

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
            "hospital_types": [
                "General",
                "Teaching",
                "Community",
                "Specialty",
                "Rehabilitation",
                "Psychiatric",
                "Children's",
                "Veterans",
                "Long-term Care",
            ],
            "departments": [
                "Emergency",
                "Surgery",
                "Internal Medicine",
                "Pediatrics",
                "Obstetrics and Gynecology",
                "Cardiology",
                "Neurology",
                "Orthopedics",
                "Oncology",
                "Radiology",
                "Anesthesiology",
                "Psychiatry",
                "Dermatology",
                "Ophthalmology",
                "Otolaryngology",
                "Urology",
                "Nephrology",
                "Gastroenterology",
                "Pulmonology",
                "Endocrinology",
                "Hematology",
                "Infectious Disease",
                "Rheumatology",
                "Physical Therapy",
                "Occupational Therapy",
                "Speech Therapy",
                "Nutrition",
                "Pharmacy",
                "Laboratory",
                "Pathology",
            ],
            "services": [
                "Emergency Care",
                "Intensive Care",
                "Surgery",
                "Outpatient Care",
                "Inpatient Care",
                "Diagnostic Imaging",
                "Laboratory Services",
                "Physical Therapy",
                "Occupational Therapy",
                "Speech Therapy",
                "Cardiac Rehabilitation",
                "Pulmonary Rehabilitation",
                "Dialysis",
                "Chemotherapy",
                "Radiation Therapy",
                "Maternity Care",
                "Neonatal Care",
                "Pediatric Care",
                "Geriatric Care",
                "Psychiatric Care",
                "Substance Abuse Treatment",
                "Pain Management",
                "Palliative Care",
                "Hospice Care",
                "Telemedicine",
                "Home Health Care",
                "Wound Care",
                "Sleep Studies",
                "Nutrition Counseling",
                "Genetic Counseling",
                "Bariatric Surgery",
                "Organ Transplantation",
                "Trauma Care",
                "Burn Care",
                "Stroke Care",
                "Cardiac Catheterization",
                "Electrophysiology",
                "Endoscopy",
                "Lithotripsy",
                "Mammography",
                "MRI",
                "CT Scan",
                "Ultrasound",
                "X-ray",
                "PET Scan",
                "Nuclear Medicine",
                "Blood Bank",
                "Pharmacy",
                "Rehabilitation Services",
            ],
            "accreditations": [
                "Joint Commission",
                "DNV GL Healthcare",
                "Healthcare Facilities Accreditation Program (HFAP)",
                "Center for Improvement in Healthcare Quality (CIHQ)",
                "Commission on Accreditation of Rehabilitation Facilities (CARF)",
                "American Osteopathic Association (AOA)",
                "National Committee for Quality Assurance (NCQA)",
                "Accreditation Association for Ambulatory Health Care (AAAHC)",
                "American College of Surgeons Commission on Cancer (CoC)",
                "American College of Radiology (ACR)",
                "College of American Pathologists (CAP)",
                "American Association of Blood Banks (AABB)",
                "Foundation for the Accreditation of Cellular Therapy (FACT)",
                "American Society for Histocompatibility and Immunogenetics (ASHI)",
                "American Academy of Sleep Medicine (AASM)",
                "Intersocietal Accreditation Commission (IAC)",
                "National Accreditation Program for Breast Centers (NAPBC)",
                "American College of Emergency Physicians (ACEP)",
                "Society of Cardiovascular Patient Care (SCPC)",
                "American Diabetes Association (ADA)",
            ],
        }

        return defaults.get(data_type, [])
