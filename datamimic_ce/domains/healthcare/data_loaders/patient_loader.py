# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Patient data loader.

This module provides the PatientDataLoader class for loading patient-related data.
"""

import os
from typing import Any

from datamimic_ce.core.base_data_loader import BaseDataLoader


class PatientDataLoader(BaseDataLoader):
    """Load patient-related data from files.

    This class loads data for patient entities, including allergies, medications,
    conditions, insurance providers, and other patient-related information.

    Data is loaded from country-specific CSV files when available,
    falling back to generic data files if needed.
    """

    # Cache for loaded data to avoid repeated file reads
    _data_cache: dict[str, dict[str, Any]] = {}

    def __init__(self):
        """Initialize the PatientDataLoader."""
        super().__init__()
        self._base_path = self._get_data_path("healthcare")

    def get_data(self, data_type: str, country_code: str = "US") -> list[Any]:
        """Get data of the specified type for the specified country.

        Args:
            data_type: The type of data to get (e.g., "allergies", "medications").
            country_code: The country code to get data for.

        Returns:
            A list of data items.
        """
        # Check if data is already cached
        cache_key = f"{data_type}_{country_code}"
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        # Define file paths
        country_specific_path = os.path.join(self._base_path, "patient", f"{data_type}_{country_code.lower()}.csv")
        generic_path = os.path.join(self._base_path, "patient", f"{data_type}.csv")

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
            "allergies": [
                "Penicillin",
                "Peanuts",
                "Shellfish",
                "Dairy",
                "Eggs",
                "Tree nuts",
                "Soy",
                "Wheat",
                "Fish",
                "Sulfa drugs",
                "NSAIDs",
                "Latex",
                "Bee stings",
                "Pollen",
                "Dust mites",
                "Mold",
                "Pet dander",
                "Sesame",
                "Iodine",
                "Contrast dye",
            ],
            "medications": [
                "Lisinopril",
                "Atorvastatin",
                "Levothyroxine",
                "Metformin",
                "Amlodipine",
                "Metoprolol",
                "Omeprazole",
                "Simvastatin",
                "Losartan",
                "Albuterol",
                "Gabapentin",
                "Hydrochlorothiazide",
                "Sertraline",
                "Acetaminophen",
                "Ibuprofen",
                "Aspirin",
                "Furosemide",
                "Fluoxetine",
                "Pantoprazole",
                "Prednisone",
            ],
            "conditions": [
                "Hypertension",
                "Type 2 Diabetes",
                "Asthma",
                "Osteoarthritis",
                "Hyperlipidemia",
                "Depression",
                "Anxiety",
                "GERD",
                "Hypothyroidism",
                "Obesity",
                "Chronic kidney disease",
                "COPD",
                "Atrial fibrillation",
                "Coronary artery disease",
                "Heart failure",
                "Migraine",
                "Osteoporosis",
                "Rheumatoid arthritis",
                "Sleep apnea",
                "Allergic rhinitis",
            ],
            "insurance_providers": [
                "Blue Cross Blue Shield",
                "UnitedHealthcare",
                "Aetna",
                "Cigna",
                "Humana",
                "Kaiser Permanente",
                "Medicare",
                "Medicaid",
                "Anthem",
                "Centene",
                "Molina Healthcare",
                "Health Net",
                "WellCare",
                "Highmark",
                "TRICARE",
                "AmeriHealth",
                "Harvard Pilgrim",
                "Tufts Health Plan",
                "Emblem Health",
                "Carefirst",
            ],
            "first_names": [
                "James",
                "Mary",
                "John",
                "Patricia",
                "Robert",
                "Jennifer",
                "Michael",
                "Linda",
                "William",
                "Elizabeth",
                "David",
                "Susan",
                "Richard",
                "Jessica",
                "Joseph",
                "Sarah",
                "Thomas",
                "Karen",
                "Charles",
                "Nancy",
                "Christopher",
                "Lisa",
                "Daniel",
                "Margaret",
                "Matthew",
                "Betty",
                "Anthony",
                "Sandra",
                "Mark",
                "Ashley",
                "Donald",
                "Dorothy",
                "Steven",
                "Kimberly",
                "Paul",
                "Emily",
                "Andrew",
                "Donna",
                "Joshua",
                "Michelle",
                "Kenneth",
                "Carol",
                "Kevin",
                "Amanda",
                "Brian",
                "Melissa",
                "George",
                "Deborah",
                "Timothy",
                "Stephanie",
                "Ronald",
                "Rebecca",
                "Jason",
                "Laura",
                "Edward",
                "Sharon",
                "Jeffrey",
                "Cynthia",
                "Ryan",
                "Kathleen",
                "Jacob",
                "Amy",
                "Gary",
                "Shirley",
            ],
            "last_names": [
                "Smith",
                "Johnson",
                "Williams",
                "Brown",
                "Jones",
                "Garcia",
                "Miller",
                "Davis",
                "Rodriguez",
                "Martinez",
                "Hernandez",
                "Lopez",
                "Gonzalez",
                "Wilson",
                "Anderson",
                "Thomas",
                "Taylor",
                "Moore",
                "Jackson",
                "Martin",
                "Lee",
                "Perez",
                "Thompson",
                "White",
                "Harris",
                "Sanchez",
                "Clark",
                "Ramirez",
                "Lewis",
                "Robinson",
                "Walker",
                "Young",
                "Allen",
                "King",
                "Wright",
                "Scott",
                "Torres",
                "Nguyen",
                "Hill",
                "Flores",
                "Green",
                "Adams",
                "Nelson",
                "Baker",
                "Hall",
                "Rivera",
                "Campbell",
                "Mitchell",
                "Carter",
                "Roberts",
                "Gomez",
                "Phillips",
                "Evans",
                "Turner",
                "Diaz",
                "Parker",
                "Cruz",
                "Edwards",
                "Collins",
                "Reyes",
                "Stewart",
                "Morris",
                "Morales",
                "Murphy",
            ],
            "doctor_first_names": [
                "James",
                "Mary",
                "John",
                "Patricia",
                "Robert",
                "Jennifer",
                "Michael",
                "Linda",
                "William",
                "Elizabeth",
                "David",
                "Susan",
                "Richard",
                "Jessica",
                "Joseph",
                "Sarah",
                "Thomas",
                "Karen",
                "Charles",
                "Nancy",
                "Christopher",
                "Lisa",
                "Daniel",
                "Margaret",
                "Matthew",
                "Betty",
                "Anthony",
                "Sandra",
                "Mark",
                "Ashley",
                "Donald",
                "Dorothy",
            ],
            "doctor_last_names": [
                "Smith",
                "Johnson",
                "Williams",
                "Brown",
                "Jones",
                "Garcia",
                "Miller",
                "Davis",
                "Rodriguez",
                "Martinez",
                "Hernandez",
                "Lopez",
                "Gonzalez",
                "Wilson",
                "Anderson",
                "Thomas",
                "Taylor",
                "Moore",
                "Jackson",
                "Martin",
                "Lee",
                "Perez",
                "Thompson",
                "White",
                "Harris",
                "Sanchez",
                "Clark",
                "Ramirez",
                "Lewis",
                "Robinson",
                "Walker",
            ],
        }

        return defaults.get(data_type, [])
