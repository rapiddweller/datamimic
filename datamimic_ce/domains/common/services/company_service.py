# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import List, Dict, Any, Optional

from datamimic_ce.domains.common.models.company import Company


class CompanyService:
    """Service for creating and managing company entities.
    
    Provides high-level methods for creating, managing, and exporting
    company entities, with support for bulk operations and filtering.
    """
    
    @staticmethod
    def create_company(
        dataset: str = "US",
        count: int = 1,
    ) -> Company:
        """Create a single company entity.
        
        Args:
            dataset: Country code for country-specific generation
            count: Number of companies to generate
            
        Returns:
            A new company entity
        """
        return Company(dataset=dataset, count=count)
    
    @staticmethod
    def create_companies(
        count: int,
        dataset: str = "US",
    ) -> List[Company]:
        """Create multiple company entities.
        
        Args:
            count: Number of companies to create
            dataset: Country code for country-specific generation
            
        Returns:
            List of company entities
        """
        return [
            Company(dataset=dataset, count=count)
            for _ in range(count)
        ]
    
    @staticmethod
    def filter_companies_by_sector(
        companies: List[Company],
        sector: str,
    ) -> List[Company]:
        """Filter companies by sector.
        
        Args:
            companies: List of companies to filter
            sector: Sector to filter by
            
        Returns:
            Filtered list of companies
        """
        return [company for company in companies if company.sector == sector]
    
    @staticmethod
    def filter_companies_by_country(
        companies: List[Company],
        country_code: str,
    ) -> List[Company]:
        """Filter companies by country code.
        
        Args:
            companies: List of companies to filter
            country_code: Country code to filter by
            
        Returns:
            Filtered list of companies
        """
        return [company for company in companies if company.country_code == country_code]
    
    @staticmethod
    def companies_to_dict(companies: List[Company]) -> List[Dict[str, Any]]:
        """Convert a list of companies to a list of dictionaries.
        
        Args:
            companies: List of companies to convert
            
        Returns:
            List of dictionaries representing companies
        """
        return [company.to_dict() for company in companies]