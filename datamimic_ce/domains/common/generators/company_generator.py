# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com



from pathlib import Path
import random
from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.logger import logger
from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.generators.company_name_generator import CompanyNameGenerator
from datamimic_ce.domains.common.generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.domains.common.generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil


class CompanyGenerator(BaseDomainGenerator):
    """Generator for company-related attributes.

    Provides methods to generate company-related attributes such as
    company names, emails, URLs, and other information.
    """
    
    def __init__(self, country_code: str = "US"):
        self._country_code = country_code
        self._company_name_generator = CompanyNameGenerator()
        self._email_address_generator = EmailAddressGenerator(dataset=country_code)
        self._phone_number_generator = PhoneNumberGenerator(dataset=country_code)
        self._address_generator = AddressGenerator(country_code=country_code)
        
    @property
    def country_code(self) -> str:
        """Get the country code.

        Returns:
            The country code.
        """
        return self._country_code
    
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
    
    @property
    def address_generator(self) -> AddressGenerator:
        """Get the address generator.

        Returns:    
            The address generator.
        """
        return self._address_generator
    
    def generate_sector(self) -> str:
        """Generate a sector.

        Returns:
            The sector.
        """
        cache_key = f"sector_{self._country_code}"
        if cache_key not in self._LOADED_DATA_CACHE:
            logger.debug("CACHE MISS: Loading sector data from file")
            file_path = Path(__file__).parent.parent.parent.parent / "domain_data" / "common" / "organization" / f"sector_{self._country_code}.csv"
            sector_df = FileContentStorage.load_file_with_custom_func(cache_key=str(file_path), read_func=lambda: FileUtil.read_csv_to_list_of_tuples_without_header(file_path, delimiter=";"))
            sector_list = [row[0] for row in sector_df]
            self._LOADED_DATA_CACHE[cache_key] = sector_list
        return random.choice(self._LOADED_DATA_CACHE[cache_key])
    
    def get_legal_form(self) -> str:
        """Get a legal form.

        Returns:
            The legal form.
        """
        cache_key = f"legal_form_{self._country_code}"
        if cache_key not in self._LOADED_DATA_CACHE:
            logger.debug("CACHE MISS: Loading legal form data from file")
            file_path = Path(__file__).parent.parent.parent.parent / "domain_data" / "common" / "organization" / f"legalForm_{self._country_code}.csv"
            legal_form_df = FileContentStorage.load_file_with_custom_func(cache_key=str(file_path), read_func=lambda: FileUtil.read_wgt_file(file_path))
            self._LOADED_DATA_CACHE[cache_key] = legal_form_df
        legal_values, legal_wgt = self._LOADED_DATA_CACHE[cache_key]
        return random.choices(legal_values, weights=legal_wgt, k=1)[0]
