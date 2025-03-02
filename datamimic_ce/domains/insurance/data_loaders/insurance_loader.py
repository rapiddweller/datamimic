# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance data loader.

This module provides data loading functionality for insurance-related data,
loading reference data from CSV files for insurance companies, products, and coverages.
"""

from pathlib import Path
from typing import Any, ClassVar, List, Optional, Tuple, cast, Dict

from datamimic_ce.core.base_data_loader import BaseDataLoader
from datamimic_ce.utils.data_path_util import DataPathUtil
from datamimic_ce.utils.file_util import FileUtil


class InsuranceDataLoader(BaseDataLoader):
    """Data loader for insurance related data.

    This class loads insurance information from CSV files and provides methods to access this data.
    """

    # Cache for loaded data
    _COMPANIES_CACHE: ClassVar[Dict[str, List[Dict[str, Any]]]] = {}
    _COMPANIES_BY_WEIGHT_CACHE: ClassVar[Dict[str, List[Tuple[Dict[str, Any], float]]]] = {}
    _PRODUCTS_CACHE: ClassVar[Dict[str, List[Dict[str, Any]]]] = {}
    _PRODUCTS_BY_WEIGHT_CACHE: ClassVar[Dict[str, List[Tuple[Dict[str, Any], float]]]] = {}
    _COVERAGES_CACHE: ClassVar[Dict[str, Dict[str, List[Dict[str, Any]]]]] = {}
    _COVERAGES_BY_WEIGHT_CACHE: ClassVar[Dict[str, Dict[str, List[Tuple[Dict[str, Any], float]]]]] = {}

    @classmethod
    def _get_file_path_for_data_type(cls, data_type: str, dataset: Optional[str] = None) -> str:
        """Get the file path for the specified data type.

        Args:
            data_type: The type of data to get the file path for
            dataset: Optional dataset code (country code)

        Returns:
            The file path for the data type
        """
        # Map of data types to their base file names
        file_map = {
            "companies": "insurance/companies",
            "products": "insurance/products",
            "coverages": "insurance/coverages",
        }
        
        # Handle regular data types
        if data_type in file_map:
            base_name = file_map[data_type]
            # Use country-specific file if dataset (country) is provided
            if dataset:
                return f"{base_name}_{dataset}.csv"
            else:
                # First try with 'US' as default dataset
                file_path = f"{base_name}_US.csv"
                data_file_path = DataPathUtil.get_data_file_path(file_path)
                if Path(data_file_path).exists():
                    return file_path
                # Fallback to generic file without country code
                return f"{base_name}.csv"
        
        return ""

    @classmethod
    def load_companies(cls, dataset: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load insurance company data for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of insurance company dictionaries
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"
        
        # Check if the data is already cached
        if dataset_key in cls._COMPANIES_CACHE:
            return cls._COMPANIES_CACHE[dataset_key]
        
        # Get the file path
        file_path = cls._get_file_path_for_data_type("companies", dataset)
        
        # If file path is empty, return default data
        if not file_path:
            default_data = cls._get_default_companies(dataset)
            cls._COMPANIES_CACHE[dataset_key] = default_data
            return default_data
        
        try:
            # Get the data file path using DataPathUtil
            data_file_path = DataPathUtil.get_data_file_path(file_path)
            
            if not Path(data_file_path).exists():
                # If file doesn't exist, return default data
                default_data = cls._get_default_companies(dataset)
                cls._COMPANIES_CACHE[dataset_key] = default_data
                return default_data
            
            # Load data from CSV
            header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(data_file_path)
            
            result = []
            
            # Process each row
            for row in data:
                company = {}
                
                # Extract all fields from the row
                for key, idx in header_dict.items():
                    if key != "weight":  # Skip the weight field
                        company[key] = row[idx]
                
                # Add the company to the result
                result.append(company)
            
            # Cache the data
            cls._COMPANIES_CACHE[dataset_key] = result
            
            # Also load as weighted data
            cls._load_companies_by_weight(dataset)
            
            return result
        
        except Exception as e:
            print(f"Error loading insurance company data: {e}")
            default_data = cls._get_default_companies(dataset)
            cls._COMPANIES_CACHE[dataset_key] = default_data
            return default_data

    @classmethod
    def _load_companies_by_weight(cls, dataset: Optional[str] = None) -> List[Tuple[Dict[str, Any], float]]:
        """Load insurance company data with weights for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing insurance company dictionaries and weights
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"
        
        # Check if the data is already cached
        if dataset_key in cls._COMPANIES_BY_WEIGHT_CACHE:
            return cls._COMPANIES_BY_WEIGHT_CACHE[dataset_key]
        
        # Get the file path
        file_path = cls._get_file_path_for_data_type("companies", dataset)
        
        # If file path is empty, return default data
        if not file_path:
            default_data = cls._get_default_companies_by_weight(dataset)
            cls._COMPANIES_BY_WEIGHT_CACHE[dataset_key] = default_data
            return default_data
        
        try:
            # Get the data file path using DataPathUtil
            data_file_path = DataPathUtil.get_data_file_path(file_path)
            
            if not Path(data_file_path).exists():
                # If file doesn't exist, return default data
                default_data = cls._get_default_companies_by_weight(dataset)
                cls._COMPANIES_BY_WEIGHT_CACHE[dataset_key] = default_data
                return default_data
            
            # Load data from CSV
            header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(data_file_path)
            
            # Skip if weight column doesn't exist
            if "weight" not in header_dict:
                default_data = cls._get_default_companies_by_weight(dataset)
                cls._COMPANIES_BY_WEIGHT_CACHE[dataset_key] = default_data
                return default_data
            
            weight_idx = header_dict["weight"]
            
            result = []
            
            # Process each row
            for row in data:
                company = {}
                
                # Extract all fields from the row
                for key, idx in header_dict.items():
                    if key != "weight":  # Skip the weight field
                        company[key] = row[idx]
                
                # Get the weight
                try:
                    weight = float(row[weight_idx])
                except (ValueError, TypeError):
                    weight = 1.0
                
                # Add the company and weight to the result
                result.append((company, weight))
            
            # Cache the data
            cls._COMPANIES_BY_WEIGHT_CACHE[dataset_key] = result
            
            return result
        
        except Exception as e:
            print(f"Error loading insurance company data with weights: {e}")
            default_data = cls._get_default_companies_by_weight(dataset)
            cls._COMPANIES_BY_WEIGHT_CACHE[dataset_key] = default_data
            return default_data

    @classmethod
    def _get_default_companies(cls, dataset: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get default insurance company data for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of insurance company dictionaries
        """
        if dataset == "DE":
            return [
                {"name": "Allianz", "code": "ALNZ", "founded_year": "1890", "headquarters": "Munich, Bavaria", "website": "www.allianz.de"},
                {"name": "HUK-Coburg", "code": "HUKCO", "founded_year": "1933", "headquarters": "Coburg, Bavaria", "website": "www.huk.de"},
                {"name": "Generali Deutschland", "code": "GNDEU", "founded_year": "1831", "headquarters": "Munich, Bavaria", "website": "www.generali.de"},
            ]
        else:  # Default to US
            return [
                {"name": "State Farm", "code": "STFRM", "founded_year": "1922", "headquarters": "Bloomington, IL", "website": "www.statefarm.com"},
                {"name": "Geico", "code": "GEICO", "founded_year": "1936", "headquarters": "Chevy Chase, MD", "website": "www.geico.com"},
                {"name": "Progressive", "code": "PRGRS", "founded_year": "1937", "headquarters": "Mayfield Village, OH", "website": "www.progressive.com"},
            ]

    @classmethod
    def _get_default_companies_by_weight(cls, dataset: Optional[str] = None) -> List[Tuple[Dict[str, Any], float]]:
        """Get default insurance company data with weights for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing insurance company dictionaries and weights
        """
        if dataset == "DE":
            return [
                ({"name": "Allianz", "code": "ALNZ", "founded_year": "1890", "headquarters": "Munich, Bavaria", "website": "www.allianz.de"}, 0.4),
                ({"name": "HUK-Coburg", "code": "HUKCO", "founded_year": "1933", "headquarters": "Coburg, Bavaria", "website": "www.huk.de"}, 0.35),
                ({"name": "Generali Deutschland", "code": "GNDEU", "founded_year": "1831", "headquarters": "Munich, Bavaria", "website": "www.generali.de"}, 0.25),
            ]
        else:  # Default to US
            return [
                ({"name": "State Farm", "code": "STFRM", "founded_year": "1922", "headquarters": "Bloomington, IL", "website": "www.statefarm.com"}, 0.4),
                ({"name": "Geico", "code": "GEICO", "founded_year": "1936", "headquarters": "Chevy Chase, MD", "website": "www.geico.com"}, 0.35),
                ({"name": "Progressive", "code": "PRGRS", "founded_year": "1937", "headquarters": "Mayfield Village, OH", "website": "www.progressive.com"}, 0.25),
            ]

    @classmethod
    def load_products(cls, dataset: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load insurance product data for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of insurance product dictionaries
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"
        
        # Check if the data is already cached
        if dataset_key in cls._PRODUCTS_CACHE:
            return cls._PRODUCTS_CACHE[dataset_key]
        
        # Get the file path
        file_path = cls._get_file_path_for_data_type("products", dataset)
        
        # If file path is empty, return default data
        if not file_path:
            default_data = cls._get_default_products(dataset)
            cls._PRODUCTS_CACHE[dataset_key] = default_data
            return default_data
        
        try:
            # Get the data file path using DataPathUtil
            data_file_path = DataPathUtil.get_data_file_path(file_path)
            
            if not Path(data_file_path).exists():
                # If file doesn't exist, return default data
                default_data = cls._get_default_products(dataset)
                cls._PRODUCTS_CACHE[dataset_key] = default_data
                return default_data
            
            # Load data from CSV
            header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(data_file_path)
            
            result = []
            
            # Process each row
            for row in data:
                product = {}
                
                # Extract all fields from the row
                for key, idx in header_dict.items():
                    if key != "weight":  # Skip the weight field
                        product[key] = row[idx]
                
                # Add the product to the result
                result.append(product)
            
            # Cache the data
            cls._PRODUCTS_CACHE[dataset_key] = result
            
            # Also load as weighted data
            cls._load_products_by_weight(dataset)
            
            return result
        
        except Exception as e:
            print(f"Error loading insurance product data: {e}")
            default_data = cls._get_default_products(dataset)
            cls._PRODUCTS_CACHE[dataset_key] = default_data
            return default_data

    @classmethod
    def _load_products_by_weight(cls, dataset: Optional[str] = None) -> List[Tuple[Dict[str, Any], float]]:
        """Load insurance product data with weights for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing insurance product dictionaries and weights
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"
        
        # Check if the data is already cached
        if dataset_key in cls._PRODUCTS_BY_WEIGHT_CACHE:
            return cls._PRODUCTS_BY_WEIGHT_CACHE[dataset_key]
        
        # Get the file path
        file_path = cls._get_file_path_for_data_type("products", dataset)
        
        # If file path is empty, return default data
        if not file_path:
            default_data = cls._get_default_products_by_weight(dataset)
            cls._PRODUCTS_BY_WEIGHT_CACHE[dataset_key] = default_data
            return default_data
        
        try:
            # Get the data file path using DataPathUtil
            data_file_path = DataPathUtil.get_data_file_path(file_path)
            
            if not Path(data_file_path).exists():
                # If file doesn't exist, return default data
                default_data = cls._get_default_products_by_weight(dataset)
                cls._PRODUCTS_BY_WEIGHT_CACHE[dataset_key] = default_data
                return default_data
            
            # Load data from CSV
            header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(data_file_path)
            
            # Skip if weight column doesn't exist
            if "weight" not in header_dict:
                default_data = cls._get_default_products_by_weight(dataset)
                cls._PRODUCTS_BY_WEIGHT_CACHE[dataset_key] = default_data
                return default_data
            
            weight_idx = header_dict["weight"]
            
            result = []
            
            # Process each row
            for row in data:
                product = {}
                
                # Extract all fields from the row
                for key, idx in header_dict.items():
                    if key != "weight":  # Skip the weight field
                        product[key] = row[idx]
                
                # Get the weight
                try:
                    weight = float(row[weight_idx])
                except (ValueError, TypeError):
                    weight = 1.0
                
                # Add the product and weight to the result
                result.append((product, weight))
            
            # Cache the data
            cls._PRODUCTS_BY_WEIGHT_CACHE[dataset_key] = result
            
            return result
        
        except Exception as e:
            print(f"Error loading insurance product data with weights: {e}")
            default_data = cls._get_default_products_by_weight(dataset)
            cls._PRODUCTS_BY_WEIGHT_CACHE[dataset_key] = default_data
            return default_data

    @classmethod
    def _get_default_products(cls, dataset: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get default insurance product data for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of insurance product dictionaries
        """
        if dataset == "DE":
            return [
                {"type": "Kfz-Versicherung", "code": "AUTO", "description": "Absicherung gegen finanzielle Risiken bei Autounfällen oder Schäden"},
                {"type": "Wohngebäudeversicherung", "code": "HOME", "description": "Absicherung von Schäden an Wohngebäuden"},
                {"type": "Krankenversicherung", "code": "HLTH", "description": "Deckung medizinischer Kosten bei Krankheiten und Verletzungen"},
            ]
        else:  # Default to US
            return [
                {"type": "Auto Insurance", "code": "AUTO", "description": "Provides financial protection in case of vehicle accidents or damage"},
                {"type": "Homeowners Insurance", "code": "HOME", "description": "Covers damage to a home and its contents"},
                {"type": "Health Insurance", "code": "HLTH", "description": "Covers medical expenses for illnesses and injuries"},
            ]

    @classmethod
    def _get_default_products_by_weight(cls, dataset: Optional[str] = None) -> List[Tuple[Dict[str, Any], float]]:
        """Get default insurance product data with weights for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing insurance product dictionaries and weights
        """
        if dataset == "DE":
            return [
                ({"type": "Kfz-Versicherung", "code": "AUTO", "description": "Absicherung gegen finanzielle Risiken bei Autounfällen oder Schäden"}, 0.5),
                ({"type": "Wohngebäudeversicherung", "code": "HOME", "description": "Absicherung von Schäden an Wohngebäuden"}, 0.3),
                ({"type": "Krankenversicherung", "code": "HLTH", "description": "Deckung medizinischer Kosten bei Krankheiten und Verletzungen"}, 0.2),
            ]
        else:  # Default to US
            return [
                ({"type": "Auto Insurance", "code": "AUTO", "description": "Provides financial protection in case of vehicle accidents or damage"}, 0.5),
                ({"type": "Homeowners Insurance", "code": "HOME", "description": "Covers damage to a home and its contents"}, 0.3),
                ({"type": "Health Insurance", "code": "HLTH", "description": "Covers medical expenses for illnesses and injuries"}, 0.2),
            ]

    @classmethod
    def load_coverages(cls, product_code: str, dataset: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load insurance coverage data for the specified product and dataset.

        Args:
            product_code: The product code to load coverages for
            dataset: Optional dataset code (country code)

        Returns:
            A list of insurance coverage dictionaries
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"
        
        # Initialize the dataset's coverages cache if it doesn't exist
        if dataset_key not in cls._COVERAGES_CACHE:
            cls._COVERAGES_CACHE[dataset_key] = {}
        
        # Check if the data is already cached
        if product_code in cls._COVERAGES_CACHE[dataset_key]:
            return cls._COVERAGES_CACHE[dataset_key][product_code]
        
        # Get the file path
        file_path = cls._get_file_path_for_data_type("coverages", dataset)
        
        # If file path is empty, return default data
        if not file_path:
            default_data = cls._get_default_coverages(product_code, dataset)
            cls._COVERAGES_CACHE[dataset_key][product_code] = default_data
            return default_data
        
        try:
            # Get the data file path using DataPathUtil
            data_file_path = DataPathUtil.get_data_file_path(file_path)
            
            if not Path(data_file_path).exists():
                # If file doesn't exist, return default data
                default_data = cls._get_default_coverages(product_code, dataset)
                cls._COVERAGES_CACHE[dataset_key][product_code] = default_data
                return default_data
            
            # Load data from CSV
            header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(data_file_path)
            
            result = []
            
            # Process each row
            for row in data:
                # Get the product code from the row
                row_product_code_idx = header_dict.get("product_code")
                if row_product_code_idx is None:
                    continue
                
                row_product_code = row[row_product_code_idx]
                
                # Skip if the product code doesn't match
                if row_product_code != product_code:
                    continue
                
                coverage = {}
                
                # Extract all fields from the row
                for key, idx in header_dict.items():
                    if key != "weight" and key != "product_code":  # Skip the weight and product_code fields
                        if key in ["min_coverage", "max_coverage"]:
                            # Convert coverage values to integers if possible
                            value = row[idx]
                            if value.lower() == "unlimited":
                                coverage[key] = float('inf')
                            else:
                                try:
                                    coverage[key] = int(value)
                                except (ValueError, TypeError):
                                    coverage[key] = value
                        else:
                            coverage[key] = row[idx]
                
                # Add the coverage to the result
                result.append(coverage)
            
            # Cache the data
            cls._COVERAGES_CACHE[dataset_key][product_code] = result
            
            # Also load as weighted data
            cls._load_coverages_by_weight(product_code, dataset)
            
            return result
        
        except Exception as e:
            print(f"Error loading insurance coverage data: {e}")
            default_data = cls._get_default_coverages(product_code, dataset)
            cls._COVERAGES_CACHE[dataset_key][product_code] = default_data
            return default_data

    @classmethod
    def _load_coverages_by_weight(cls, product_code: str, dataset: Optional[str] = None) -> List[Tuple[Dict[str, Any], float]]:
        """Load insurance coverage data with weights for the specified product and dataset.

        Args:
            product_code: The product code to load coverages for
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing insurance coverage dictionaries and weights
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"
        
        # Initialize the dataset's coverages cache if it doesn't exist
        if dataset_key not in cls._COVERAGES_BY_WEIGHT_CACHE:
            cls._COVERAGES_BY_WEIGHT_CACHE[dataset_key] = {}
        
        # Check if the data is already cached
        if product_code in cls._COVERAGES_BY_WEIGHT_CACHE[dataset_key]:
            return cls._COVERAGES_BY_WEIGHT_CACHE[dataset_key][product_code]
        
        # Get the file path
        file_path = cls._get_file_path_for_data_type("coverages", dataset)
        
        # If file path is empty, return default data
        if not file_path:
            default_data = cls._get_default_coverages_by_weight(product_code, dataset)
            cls._COVERAGES_BY_WEIGHT_CACHE[dataset_key][product_code] = default_data
            return default_data
        
        try:
            # Get the data file path using DataPathUtil
            data_file_path = DataPathUtil.get_data_file_path(file_path)
            
            if not Path(data_file_path).exists():
                # If file doesn't exist, return default data
                default_data = cls._get_default_coverages_by_weight(product_code, dataset)
                cls._COVERAGES_BY_WEIGHT_CACHE[dataset_key][product_code] = default_data
                return default_data
            
            # Load data from CSV
            header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(data_file_path)
            
            # Skip if weight column doesn't exist
            if "weight" not in header_dict:
                default_data = cls._get_default_coverages_by_weight(product_code, dataset)
                cls._COVERAGES_BY_WEIGHT_CACHE[dataset_key][product_code] = default_data
                return default_data
            
            weight_idx = header_dict["weight"]
            
            result = []
            
            # Process each row
            for row in data:
                # Get the product code from the row
                row_product_code_idx = header_dict.get("product_code")
                if row_product_code_idx is None:
                    continue
                
                row_product_code = row[row_product_code_idx]
                
                # Skip if the product code doesn't match
                if row_product_code != product_code:
                    continue
                
                coverage = {}
                
                # Extract all fields from the row
                for key, idx in header_dict.items():
                    if key != "weight" and key != "product_code":  # Skip the weight and product_code fields
                        if key in ["min_coverage", "max_coverage"]:
                            # Convert coverage values to integers if possible
                            value = row[idx]
                            if value.lower() == "unlimited":
                                coverage[key] = float('inf')
                            else:
                                try:
                                    coverage[key] = int(value)
                                except (ValueError, TypeError):
                                    coverage[key] = value
                        else:
                            coverage[key] = row[idx]
                
                # Get the weight
                try:
                    weight = float(row[weight_idx])
                except (ValueError, TypeError):
                    weight = 1.0
                
                # Add the coverage and weight to the result
                result.append((coverage, weight))
            
            # Cache the data
            cls._COVERAGES_BY_WEIGHT_CACHE[dataset_key][product_code] = result
            
            return result
        
        except Exception as e:
            print(f"Error loading insurance coverage data with weights: {e}")
            default_data = cls._get_default_coverages_by_weight(product_code, dataset)
            cls._COVERAGES_BY_WEIGHT_CACHE[dataset_key][product_code] = default_data
            return default_data

    @classmethod
    def _get_default_coverages(cls, product_code: str, dataset: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get default insurance coverage data for the specified product and dataset.

        Args:
            product_code: The product code to get coverages for
            dataset: Optional dataset code (country code)

        Returns:
            A list of insurance coverage dictionaries
        """
        if dataset == "DE":
            if product_code == "AUTO":
                return [
                    {"name": "Kfz-Haftpflicht", "code": "LIAB", "description": "Deckt Schäden an anderen Personen und Eigentum", "min_coverage": 7500000, "max_coverage": 100000000},
                    {"name": "Teilkasko", "code": "TEIL", "description": "Deckt teilweise Schäden am eigenen Fahrzeug", "min_coverage": 5000, "max_coverage": 50000},
                ]
            elif product_code == "HOME":
                return [
                    {"name": "Gebäudeversicherung", "code": "GEBA", "description": "Schutz für die Bausubstanz", "min_coverage": 100000, "max_coverage": 2000000},
                    {"name": "Hausratversicherung", "code": "HAUS", "description": "Schutz für persönliches Eigentum", "min_coverage": 20000, "max_coverage": 500000},
                ]
            elif product_code == "HLTH":
                return [
                    {"name": "Stationäre Behandlung", "code": "STAT", "description": "Deckt Krankenhausaufenthalte", "min_coverage": float('inf'), "max_coverage": float('inf')},
                    {"name": "Ambulante Behandlung", "code": "AMBU", "description": "Deckt ambulante Leistungen", "min_coverage": float('inf'), "max_coverage": float('inf')},
                ]
            else:
                return []
        else:  # Default to US
            if product_code == "AUTO":
                return [
                    {"name": "Liability", "code": "LIAB", "description": "Covers damages to other people and property", "min_coverage": 15000, "max_coverage": 1000000},
                    {"name": "Collision", "code": "COLL", "description": "Covers damage to your vehicle from an accident", "min_coverage": 5000, "max_coverage": 100000},
                ]
            elif product_code == "HOME":
                return [
                    {"name": "Dwelling Coverage", "code": "DWEL", "description": "Covers the structure of your home", "min_coverage": 100000, "max_coverage": 2000000},
                    {"name": "Personal Property", "code": "PROP", "description": "Covers personal belongings", "min_coverage": 50000, "max_coverage": 1000000},
                ]
            elif product_code == "HLTH":
                return [
                    {"name": "Hospitalization", "code": "HOSP", "description": "Covers hospital stays", "min_coverage": 5000, "max_coverage": float('inf')},
                    {"name": "Prescription Drugs", "code": "PRES", "description": "Covers prescription medications", "min_coverage": 500, "max_coverage": float('inf')},
                ]
            else:
                return []

    @classmethod
    def _get_default_coverages_by_weight(cls, product_code: str, dataset: Optional[str] = None) -> List[Tuple[Dict[str, Any], float]]:
        """Get default insurance coverage data with weights for the specified product and dataset.

        Args:
            product_code: The product code to get coverages for
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing insurance coverage dictionaries and weights
        """
        coverages = cls._get_default_coverages(product_code, dataset)
        # Assign equal weights to all coverages
        weight = 1.0 / len(coverages) if coverages else 0.0
        return [(coverage, weight) for coverage in coverages]