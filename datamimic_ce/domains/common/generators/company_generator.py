# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from typing import List, Optional, Tuple

import numpy as np

from datamimic_ce.generators.company_name_generator import CompanyNameGenerator
from datamimic_ce.generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.domains.common.generators.phone_number_generator import PhoneNumberGenerator


class CompanyGenerator:
    """Generator for company-related attributes.
    
    Provides methods to generate company-related attributes such as
    company names, emails, URLs, and other information.
    """
    
    def __init__(self, dataset: str, count: int = 1):
        """Initialize the company generator.
        
        Args:
            dataset: Country code for country-specific generation
            count: Number of companies to generate
        """
        self.dataset = dataset
        self.count = count
        self.company_name_generator = CompanyNameGenerator()
        self.email_generator = EmailAddressGenerator(dataset=dataset, generated_count=count)
        self.phone_generator = PhoneNumberGenerator(dataset=dataset)
    
    def generate_company_name(self) -> str:
        """Generate a company name.
        
        Returns:
            A generated company name
        """
        return self.company_name_generator.generate()
    
    def generate_full_name(
        self, 
        short_name: Optional[str],
        sector: Optional[str],
        legal_forms: Optional[List[str]],
        legal_weights: Optional[List[float]]
    ) -> str:
        """Generate the full name of the company.

        Args:
            short_name: The short name of the company
            sector: The sector in which the company operates
            legal_forms: List of legal forms
            legal_weights: Weights for the legal forms

        Returns:
            The full company name including sector and legal form
        """
        legal_form = None
        if legal_forms and legal_weights and len(legal_forms) > 0:
            legal_form = random.choices(legal_forms, legal_weights, k=1)[0]

        builder = [""] if short_name is None else [short_name]
        if sector is not None:
            builder.append(" " + sector)
        if legal_form is not None:
            builder.append(" " + legal_form)
        return "".join(builder)
    
    def generate_company_email(self, company_name: str) -> str:
        """Generate a company email address based on company name.
        
        Args:
            company_name: The name of the company
            
        Returns:
            A generated email address for the company
        """
        return self.email_generator.generate_with_company_name(company_name)
    
    def generate_company_url(self, email: str) -> Optional[str]:
        """Generate a company URL from the email domain.
        
        Args:
            email: The company email address
            
        Returns:
            A generated URL or None if email is None
        """
        if email is None:
            return None

        list_of_schemes = ["http", "https"]
        scheme = np.random.choice(list_of_schemes)
        company_domain = email.split("@")[1]
        return f"{scheme}://{company_domain}"
    
    def generate_phone_number(self) -> Optional[str]:
        """Generate a phone number.
        
        Returns:
            A generated phone number
        """
        return self.phone_generator.generate()
    
    def generate_company_id(self, company_name: str) -> str:
        """Generate a company ID based on the company name.
        
        Args:
            company_name: The name of the company
            
        Returns:
            A generated company ID
        """
        return company_name.lower().replace(" ", "_") if company_name is not None else None