# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Data loader for lab test entity.

This module provides functionality for loading data from CSV files for lab test entities.
"""

from pathlib import Path

from datamimic_ce.entities.base_data_loader import BaseDataLoader


class LabTestDataLoader(BaseDataLoader):
    """Load data for lab test entity from CSV files."""

    # Cache for loaded data to reduce file I/O
    _LAB_TESTS_CACHE: dict[str, list[tuple[str, float]]] = {}
    _LAB_TEST_UNITS_CACHE: dict[str, list[tuple[str, float]]] = {}
    _SPECIMEN_TYPES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _COLLECTION_METHODS_CACHE: dict[str, list[tuple[str, float]]] = {}
    _LAB_TEST_STATUSES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _LAB_NAMES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _TEST_COMPONENTS_CACHE: dict[str, dict[str, list[dict[str, str]]]] = {}

    def __init__(self) -> None:
        """Initialize a new LabTestDataLoader."""
        self._domain_path = "medical/lab_tests"

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
        if data_type == "lab_tests":
            return cls._LAB_TESTS_CACHE
        elif data_type == "lab_test_units":
            return cls._LAB_TEST_UNITS_CACHE
        elif data_type == "specimen_types":
            return cls._SPECIMEN_TYPES_CACHE
        elif data_type == "collection_methods":
            return cls._COLLECTION_METHODS_CACHE
        elif data_type == "lab_test_statuses":
            return cls._LAB_TEST_STATUSES_CACHE
        elif data_type == "lab_names":
            return cls._LAB_NAMES_CACHE
        else:
            # Use the BaseDataLoader implementation to create a new cache if needed
            return super()._get_cache_for_data_type(data_type)

    @classmethod
    def _get_default_values(cls, data_type: str, country_code: str = "US") -> list[tuple[str, float]]:
        """Get default values for a data type when no file is found.

        Args:
            data_type: The type of data
            country_code: The country code to use for country-specific defaults

        Returns:
            A list of default values with weights
        """
        # Dictionary of default values for US data types
        default_values = {
            "lab_tests": [
                ("Complete Blood Count (CBC)", 10.0),
                ("Basic Metabolic Panel (BMP)", 10.0),
                ("Comprehensive Metabolic Panel (CMP)", 8.0),
                ("Lipid Panel", 8.0),
                ("Liver Function Tests", 7.0),
                ("Thyroid Function Tests", 7.0),
                ("Hemoglobin A1C", 6.0),
                ("Urinalysis", 6.0),
                ("Prothrombin Time", 5.0),
                ("C-Reactive Protein", 5.0),
            ],
            "lab_test_units": [
                ("mg/dL", 10.0),
                ("g/dL", 8.0),
                ("mmol/L", 8.0),
                ("mEq/L", 7.0),
                ("μmol/L", 6.0),
                ("ng/mL", 5.0),
                ("pg/mL", 5.0),
                ("IU/L", 5.0),
                ("U/L", 5.0),
                ("%", 5.0),
            ],
            "specimen_types": [
                ("Blood", 10.0),
                ("Urine", 8.0),
                ("Serum", 7.0),
                ("Plasma", 7.0),
                ("Cerebrospinal Fluid", 5.0),
                ("Saliva", 4.0),
                ("Stool", 4.0),
                ("Tissue", 3.0),
                ("Sputum", 3.0),
                ("Swab", 2.0),
            ],
            "collection_methods": [
                ("Venipuncture", 10.0),
                ("Fingerstick", 8.0),
                ("Clean Catch", 7.0),
                ("Catheterization", 6.0),
                ("Swab", 5.0),
                ("Aspiration", 4.0),
                ("Biopsy", 3.0),
                ("Brushing", 2.0),
                ("Washing", 2.0),
                ("Scraping", 1.0),
            ],
            "lab_test_statuses": [
                ("Completed", 10.0),
                ("Pending", 8.0),
                ("Processing", 7.0),
                ("Specimen Received", 5.0),
                ("Awaiting Specimen", 5.0),
                ("Rejected", 3.0),
                ("Canceled", 2.0),
            ],
        }

        # Country-specific values
        country_specific_values = {
            "DE": {
                "lab_names": [
                    ("Synlab", 10.0),
                    ("Labor Berlin", 9.0),
                    ("Amedes", 8.0),
                    ("Sonic Healthcare Germany", 7.0),
                    ("Bioscientia", 6.0),
                    ("Labor Dr. Wisplinghoff", 5.0),
                    ("MVZ Labor Diagnostik Karlsruhe", 4.0),
                    ("Labor 28", 3.0),
                    ("Medizinisches Labor Bremen", 2.0),
                    ("Labor Lademannbogen", 1.0),
                ],
            },
            "US": {
                "lab_names": [
                    ("Quest Diagnostics", 10.0),
                    ("LabCorp", 9.0),
                    ("Mayo Clinic Laboratories", 8.0),
                    ("ARUP Laboratories", 7.0),
                    ("BioReference Laboratories", 6.0),
                    ("Sonic Healthcare", 5.0),
                    ("Medical Diagnostic Laboratories", 4.0),
                    ("Clinical Reference Laboratory", 3.0),
                    ("Spectra Laboratories", 2.0),
                    ("Eurofins", 1.0),
                ],
            },
        }

        # Check if this is a lab_names request with a country-specific value
        if data_type == "lab_names" and country_code in country_specific_values:
            return country_specific_values[country_code].get("lab_names", [])

        # Return the default values for the data type or an empty list if not found
        return default_values.get(data_type, [])

    @classmethod
    def get_test_components(cls, test_type: str, country_code: str = "US") -> list[dict[str, str]]:
        """Get the components for a specific test type.

        Args:
            test_type: The test type to get components for
            country_code: The country code to use

        Returns:
            A list of component dictionaries with component name and unit
        """
        # Check if we have this test type in the cache
        if test_type not in cls._TEST_COMPONENTS_CACHE:
            cls._TEST_COMPONENTS_CACHE[test_type] = {}

        # Check if we have this country code in the cache for this test type
        if country_code not in cls._TEST_COMPONENTS_CACHE[test_type]:
            # Define default components for common test types
            if test_type == "Complete Blood Count (CBC)" or test_type == "Blutbild":
                cls._TEST_COMPONENTS_CACHE[test_type][country_code] = [
                    {"component": "White Blood Cell Count (WBC)", "unit": "10^3/μL", "reference_range": "4.5-11.0"},
                    {"component": "Red Blood Cell Count (RBC)", "unit": "10^6/μL", "reference_range": "4.5-5.9"},
                    {"component": "Hemoglobin (Hgb)", "unit": "g/dL", "reference_range": "13.5-17.5"},
                    {"component": "Hematocrit (Hct)", "unit": "%", "reference_range": "41-53"},
                    {"component": "Mean Corpuscular Volume (MCV)", "unit": "fL", "reference_range": "80-100"},
                    {"component": "Platelet Count", "unit": "10^3/μL", "reference_range": "150-450"},
                ]
            elif test_type == "Basic Metabolic Panel (BMP)" or test_type == "Elektrolyte":
                cls._TEST_COMPONENTS_CACHE[test_type][country_code] = [
                    {"component": "Sodium", "unit": "mmol/L", "reference_range": "135-145"},
                    {"component": "Potassium", "unit": "mmol/L", "reference_range": "3.5-5.0"},
                    {"component": "Chloride", "unit": "mmol/L", "reference_range": "98-107"},
                    {"component": "Carbon Dioxide", "unit": "mmol/L", "reference_range": "23-29"},
                    {"component": "Blood Urea Nitrogen (BUN)", "unit": "mg/dL", "reference_range": "7-20"},
                    {"component": "Creatinine", "unit": "mg/dL", "reference_range": "0.6-1.2"},
                    {"component": "Glucose", "unit": "mg/dL", "reference_range": "70-99"},
                ]
            elif test_type == "Comprehensive Metabolic Panel (CMP)" or test_type == "Leberfunktionstest":
                cls._TEST_COMPONENTS_CACHE[test_type][country_code] = [
                    {"component": "Albumin", "unit": "g/dL", "reference_range": "3.4-5.4"},
                    {"component": "Alkaline Phosphatase", "unit": "U/L", "reference_range": "44-147"},
                    {"component": "ALT (SGPT)", "unit": "U/L", "reference_range": "7-56"},
                    {"component": "AST (SGOT)", "unit": "U/L", "reference_range": "5-40"},
                    {"component": "Bilirubin, Total", "unit": "mg/dL", "reference_range": "0.1-1.2"},
                    {"component": "Calcium", "unit": "mg/dL", "reference_range": "8.5-10.5"},
                    {"component": "Protein, Total", "unit": "g/dL", "reference_range": "6.0-8.3"},
                ]
            elif test_type == "Lipid Panel" or test_type == "Lipidprofil":
                cls._TEST_COMPONENTS_CACHE[test_type][country_code] = [
                    {"component": "Cholesterol, Total", "unit": "mg/dL", "reference_range": "<200"},
                    {"component": "Triglycerides", "unit": "mg/dL", "reference_range": "<150"},
                    {"component": "HDL Cholesterol", "unit": "mg/dL", "reference_range": ">40"},
                    {"component": "LDL Cholesterol (calculated)", "unit": "mg/dL", "reference_range": "<100"},
                    {"component": "Cholesterol/HDL Ratio", "unit": "", "reference_range": "<5.0"},
                ]
            elif test_type == "Thyroid Stimulating Hormone (TSH)" or test_type == "Schilddrüsenfunktionstest":
                cls._TEST_COMPONENTS_CACHE[test_type][country_code] = [
                    {"component": "TSH", "unit": "mIU/L", "reference_range": "0.4-4.0"},
                    {"component": "Free T4", "unit": "ng/dL", "reference_range": "0.8-1.8"},
                    {"component": "Free T3", "unit": "pg/mL", "reference_range": "2.3-4.2"},
                ]
            else:
                # Default to an empty list for unknown test types
                cls._TEST_COMPONENTS_CACHE[test_type][country_code] = []

        return cls._TEST_COMPONENTS_CACHE[test_type][country_code]

    @classmethod
    def get_country_specific_data(
        cls,
        data_type: str,
        country_code: str = "US",
        domain_path: str = "",
        cache_dict: dict[str, list[tuple[str, float]]] | None = None,
    ) -> list[tuple[str, float]]:
        """Get country-specific data from CSV files.

        This method tries to load data in the following order:
        1. Country-specific file (e.g., "specimen_types_US.csv")
        2. Generic file (e.g., "specimen_types.csv")
        3. Default values from _get_default_values

        Args:
            data_type: Type of data to retrieve (e.g., "labs", "providers")
            country_code: Country code (default: "US")
            domain_path: Optional subdirectory path
            cache_dict: Optional cache dictionary to use instead of the default (default: None)

        Returns:
            List of tuples (value, weight) from the data file
        """
        # Get the cache for this data type
        cache = cache_dict if cache_dict is not None else cls._get_cache_for_data_type(data_type)

        # Check if data is already cached for this country code
        if country_code in cache:
            return cache[country_code]

        # Get the base path for data files
        base_path = cls._get_base_path(domain_path)

        # Try loading the country-specific file first
        country_specific_path = base_path / f"{data_type}_{country_code}.csv"
        if Path.exists(country_specific_path):
            data = cls._load_simple_csv(country_specific_path)
            cache[country_code] = data
            return data

        # If country-specific file doesn't exist, try loading the generic file
        generic_path = base_path / f"{data_type}.csv"
        if Path.exists(generic_path):
            data = cls._load_simple_csv(generic_path)
            cache[country_code] = data
            return data

        # If no file exists, use default values
        default_values = cls._get_default_values(data_type, country_code)
        cache[country_code] = default_values
        return default_values

    @classmethod
    def _get_base_path(cls, domain_path: str = "") -> Path:
        """Get the base path for lab test entity data files.

        Args:
            domain_path: Optional subdirectory within the data directory (default: "")

        Returns:
            Path: The base path for data files
        """
        # Import here to avoid circular imports
        from datamimic_ce.utils.data_path_util import DataPathUtil

        if domain_path:
            # If a specific domain path is provided, use it
            return DataPathUtil.get_base_data_dir() / domain_path
        else:
            # Default to medical directory
            return DataPathUtil.get_base_data_dir() / "medical"
