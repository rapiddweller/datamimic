# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from typing import Optional, Dict, Any

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.common.generators.company_generator import CompanyGenerator


class Company(BaseEntity):
    """Company entity model representing a business organization.
    
    Provides methods and properties to generate and access company-related
    information such as name, address, contact details, etc.
    """

    def __init__(self, company_generator: CompanyGenerator):
        """Initialize a company entity.
        
        Args:
            dataset: Country code for country-specific generation
            count: Number of companies to generate
            address: Optional pre-defined address for the company
        """
        super().__init__()
        self._company_generator = company_generator
        
        # # Load sector data
        # sector_data = CompanyLoader.get_sectors(country_code=self.dataset)
        # self._sectors = [item[0] for item in sector_data] if sector_data else []
        
        # # Load legal form data
        # legal_form_data = CompanyLoader.get_legal_forms(country_code=self.dataset)
        # if legal_form_data:
        #     self._legal_forms = [item[0] for item in legal_form_data]
        #     self._legal_weights = [item[1] for item in legal_form_data]
        # else:
        #     self._legal_forms, self._legal_weights = None, None
        
        # # Initialize address if not provided
        # self._address = address or Address(dataset=dataset)
        
        # # Initialize generators
        # self._company_generator = CompanyGenerator(dataset=dataset, count=count)
        
        # # Initialize property cache
        # self._property_cache = PropertyCache()
    
    @property
    @property_cache
    def short_name(self) -> str:
        """Get the short name of the company.
        
        Returns:
            The short name of the company
        """
        return self._company_generator.company_name_generator.generate()
    
    
    @property
    @property_cache
    def sector(self) -> Optional[str]:
        """Get the sector in which the company operates.
        
        Returns:
            The sector in which the company operates
        """
        return self._company_generator.generate_sector()
    
    # @property
    # def full_name(self) -> str:
    #     """Get the full name of the company including sector and legal form.
        
    #     Returns:
    #         The full name of the company
    #     """
    #     return self._property_cache.get_or_generate(
    #         "full_name", 
    #         lambda: self._company_generator.generate_full_name(
    #             self.short_name, 
    #             self.sector, 
    #             self._legal_forms, 
    #             self._legal_weights
    #         )
    #     )
    
    @property
    @property_cache
    def email(self) -> str:
        """Get the email address of the company.
        
        Returns:
            The email address of the company
        """
        return self._company_generator.email_address_generator.generate_with_company_name(self.short_name)
    
    @property
    @property_cache
    def url(self) -> Optional[str]:
        """Get the URL of the company.
        
        Returns:
            The URL of the company
        """
        scheme = random.choice(["http", "https"])
        company_email_domain = self.email.split("@")[1]
        return f"{scheme}://{company_email_domain}"
    
    @property
    @property_cache
    def phone_number(self) -> Optional[str]:
        """Get the phone number of the company.
        
        Returns:
            The phone number of the company
        """
        return self._company_generator.phone_number_generator.generate()
    
    @property
    @property_cache
    def office_phone(self) -> Optional[str]:
        """Get the office phone number of the company.
        
        Returns:
            The office phone number of the company
        """
        return self._company_generator.phone_number_generator.generate()
    
    @property
    @property_cache
    def fax(self) -> Optional[str]:
        """Get the fax number of the company.
        
        Returns:
            The fax number of the company
        """
        return self._company_generator.phone_number_generator.generate()
    
    # TODO: Add related address generator
    # Address-related properties
    # @property
    # def street(self) -> str:
    #     """Get the street address of the company.
        
    #     Returns:
    #         The street address of the company
    #     """
    #     return self._data_loader.address_generator.generate_street()
    
    # @property
    # def house_number(self) -> str:
    #     """Get the house number of the company.
        
    #     Returns:
    #         The house number of the company
    #     """
    #     return self._address.house_number
    
    # @property
    # def city(self) -> str:
    #     """Get the city where the company is located.
        
    #     Returns:
    #         The city where the company is located
    #     """
    #     return self._address.city
    
    # @property
    # def state(self) -> Optional[str]:
    #     """Get the state where the company is located.
        
    #     Returns:
    #         The state where the company is located
    #     """
    #     return self._address.state
    
    # @property
    # def zip_code(self) -> str:
    #     """Get the zip code of the company.
        
    #     Returns:
    #         The zip code of the company
    #     """
    #     return self._address.zip_code
    
    # @property
    # def country(self) -> str:
    #     """Get the country where the company is located.
        
    #     Returns:
    #         The country where the company is located
    #     """
    #     return self._address.country
    
    # @property
    # def country_code(self) -> str:
    #     """Get the country code of the company.
        
    #     Returns:
    #         The country code of the company
    #     """
    #     return self.dataset
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert company entity to a dictionary.
        
        Returns:
            Dictionary representation of the company
        """
        return {
            "short_name": self.short_name,
            "sector": self.sector,
            "email": self.email,
            "url": self.url,
            "phone_number": self.phone_number,
            "office_phone": self.office_phone,
            "fax": self.fax,
            # "street": self.street,
            # "house_number": self.house_number,
            # "city": self.city,
            # "state": self.state,
            # "zip_code": self.zip_code,
            # "country": self.country,
            # "country_code": self.country_code,
        }
    