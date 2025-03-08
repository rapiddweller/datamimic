# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
import random
from datamimic_ce.domains.common.generators.company_generator import CompanyGenerator
from datamimic_ce.generators.company_name_generator import CompanyNameGenerator
from datamimic_ce.generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.logger import logger
from datamimic_ce.domain_core.base_data_loader import BaseDataLoader
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil

class CompanyLoader(BaseDataLoader):
    """Data loader for company entity data.
    
    Handles loading and caching of company-related data such as sectors,
    legal forms, and departments from data files.
    """

    # Cache for company data    
    # BaseDataLoader._LOADED_DATA_CACHE["sector"] = {}    
    # _SECTOR_CACHE = BaseDataLoader._LOADED_DATA_CACHE["sector"]
    # BaseDataLoader._LOADED_DATA_CACHE["legalForm"] = {}
    # _LEGAL_FORM_CACHE = BaseDataLoader._LOADED_DATA_CACHE["legalForm"]
    # BaseDataLoader._LOADED_DATA_CACHE["department"] = {}
    # _DEPARTMENT_CACHE = BaseDataLoader._LOADED_DATA_CACHE["department"]

    # @classmethod
    # def _get_cache_for_data_type(cls, data_type: str) -> dict[str, list[tuple[str, float]]]:
    #     """Get the appropriate cache for the data type.

    #     Args:
    #         data_type: Type of data to retrieve

    #     Returns:
    #         The appropriate cache dictionary
    #     """
    #     if data_type == "sector":
    #         return cls._SECTOR_CACHE
    #     elif data_type == "legalForm":
    #         return cls._LEGAL_FORM_CACHE
    #     elif data_type == "department":
    #         return cls._DEPARTMENT_CACHE
    #     else:
    #         # Create a new cache if it doesn't exist
    #         cache_name = f"_{data_type.upper()}_CACHE"
    #         if not hasattr(cls, cache_name):
    #             logger.warning(f"Cache not found for data type: {data_type}, creating new cache")
    #             setattr(cls, cache_name, {})
    #         return getattr(cls, cache_name)

    # @classmethod
    # def _get_default_values(cls, data_type: str) -> list[tuple[str, float]]:
    #     """Get default values for a data type.

    #     Args:
    #         data_type: Type of data to retrieve

    #     Returns:
    #         List of tuples containing default values and weights
    #     """
    #     # Return an empty list to force the use of data files
    #     # No hardcoded fallbacks
    #     return []

    def __init__(self, country_code: str):
        super().__init__()
        self._country_code = country_code
        self._company_name_generator = CompanyNameGenerator()
        self._email_address_generator = EmailAddressGenerator(dataset=country_code)
        self._phone_number_generator = PhoneNumberGenerator(dataset=country_code)
        # self._company_generator = CompanyGenerator(dataset=country_code)

    @property
    def company_name_generator(self) -> CompanyNameGenerator:
        """Get the company name generator.

        Returns:
            The company generator.
        """
        return self._company_name_generator
    
    @property
    def email_address_generator(self) -> EmailAddressGenerator:
        """Get the email address generator.

        Returns:
            The email address generator.
        """
        return self._email_address_generator
    
    @property
    def phone_number_generator(self) -> PhoneNumberGenerator:
        """Get the phone number generator.

        Returns:
            The phone number generator.
        """
        return self._phone_number_generator
    
    def generate_sector(self) -> str:
        """Generate a sector.

        Returns:
            The sector.
        """
        cache_key = f"sector_{self._country_code}"
        if cache_key not in self._LOADED_DATA_CACHE:
            logger.debug("CACHE MISS: Loading sector data from file")
            file_path = Path(__file__).parent.parent.parent.parent / "domain_data" / "common" / "sector.csv"
            sector_df = FileContentStorage.load_file_with_custom_func(cache_key=str(file_path), read_func=lambda: FileUtil.read_csv_to_list_of_tuples_without_header(file_path, delimiter=";"))
            sector_list = [row[0] for row in sector_df]
            self._LOADED_DATA_CACHE[cache_key] = sector_list
        return random.choice(self._LOADED_DATA_CACHE[cache_key])

    # @classmethod
    # def get_sectors(cls, country_code: str) -> list[tuple[str, float]]:
    #     """Get sectors for a specific country.

    #     Args:
    #         country_code: Country code to get sectors for

    #     Returns:
    #         List of tuples containing sectors and their weights
    #     """
    #     return cls.get_country_specific_data(
    #         data_type="sector", country_code=country_code, domain_path="organization"
    #     )

    # @classmethod
    # def get_legal_forms(cls, country_code: str) -> list[tuple[str, float]]:
    #     """Get legal forms for a specific country.

    #     Args:
    #         country_code: Country code to get legal forms for

    #     Returns:
    #         List of tuples containing legal forms and their weights
    #     """
    #     return cls.get_country_specific_data(
    #         data_type="legalForm", country_code=country_code, domain_path="organization"
    #     )

    # @classmethod
    # def get_departments(cls, country_code: str) -> list[tuple[str, float]]:
    #     """Get departments for a specific country.

    #     Args:
    #         country_code: Country code to get departments for

    #     Returns:
    #         List of tuples containing departments and their weights
    #     """
    #     return cls.get_country_specific_data(
    #         data_type="department", country_code=country_code, domain_path="organization"
    #     )