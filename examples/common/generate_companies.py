#!/usr/bin/env python
# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Example script demonstrating the usage of Company model and CompanyService.
This example shows how to:
1. Create multiple company instances with different country codes
2. Filter companies by sector
3. Print company information
"""

from typing import List
from datamimic_ce.domains.common.models.company import Company
from datamimic_ce.domains.common.services.company_service import CompanyService


def main():
    """Create, filter, and display company information using the domain architecture."""
    
    # Create companies from different countries
    print("Creating companies from different countries...")
    companies: List[Company] = []
    
    # Create US companies
    us_companies = CompanyService.create_companies(count=5, dataset="US")
    companies.extend(us_companies)
    
    # Create German companies
    de_companies = CompanyService.create_companies(count=3, dataset="DE")
    companies.extend(de_companies)
    
    # Create UK companies
    uk_companies = CompanyService.create_companies(count=4, dataset="GB")
    companies.extend(uk_companies)
    
    # Print all companies
    print("\nAll Companies:")
    print(f"Total count: {len(companies)}")
    for idx, company in enumerate(companies, 1):
        print(f"\n{idx}. {company.full_name}")
        print(f"   Sector: {company.sector}")
        print(f"   Country: {company.country} ({company.country_code})")
        print(f"   Contact: {company.email}, {company.phone_number}")
        print(f"   Address: {company.street} {company.house_number}, {company.city}, {company.zip_code}")
    
    # Find sectors represented in our data
    sectors = set(company.sector for company in companies if company.sector)
    
    # If we have at least one sector, filter companies by the first sector in our set
    if sectors:
        selected_sector = next(iter(sectors))
        print(f"\n\nFiltering companies by sector: {selected_sector}")
        
        # Filter companies by sector
        filtered_companies = CompanyService.filter_companies_by_sector(companies, selected_sector)
        
        # Print filtered companies
        print(f"\nCompanies in {selected_sector} sector:")
        print(f"Total count: {len(filtered_companies)}")
        for idx, company in enumerate(filtered_companies, 1):
            print(f"\n{idx}. {company.full_name}")
            print(f"   Country: {company.country} ({company.country_code})")
            print(f"   Contact: {company.email}, {company.phone_number}")
            print(f"   Address: {company.street} {company.house_number}, {company.city}, {company.zip_code}")
    
    # Filter companies by country
    print("\n\nFiltering companies by country: US")
    us_filtered = CompanyService.filter_companies_by_country(companies, "US")
    
    # Print US companies
    print("\nUS Companies:")
    print(f"Total count: {len(us_filtered)}")
    for idx, company in enumerate(us_filtered, 1):
        print(f"\n{idx}. {company.full_name}")
        print(f"   Sector: {company.sector}")
        print(f"   URL: {company.url}")
        print(f"   Address: {company.street} {company.house_number}, {company.city}, {company.state or ''}, {company.zip_code}")


if __name__ == "__main__":
    main()