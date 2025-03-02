# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Example script for generating company data using the domain-based architecture.

This example demonstrates how to:
1. Generate single company instances with specific parameters
2. Generate multiple companies in bulk
3. Filter companies by sector or country
4. Access company properties and export to dictionaries
"""

import json
import os
import sys
from typing import List

# Add the parent directory to sys.path to make datamimic_ce importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from datamimic_ce.domains.common.models.company import Company
from datamimic_ce.domains.common.services.company_service import CompanyService


def print_company_details(company: Company, index: int = None) -> None:
    """Print details of a company entity.

    Args:
        company: The company entity to print
        index: Optional index for numbering in a list
    """
    prefix = f"{index}. " if index is not None else ""
    print(f"\n{prefix}{company.full_name}")
    print(f"   ID: {company.id}")
    print(f"   Sector: {company.sector}")
    print(f"   Country: {company.country} ({company.country_code})")
    print(f"   Contact: {company.email}, {company.phone_number}")
    print(f"   Website: {company.url}")
    print(f"   Address: {company.street} {company.house_number}, {company.city}, {company.zip_code}")


def generate_single_company() -> None:
    """Generate a single company entity with default parameters."""
    print("\n=== Generating a single company with default parameters ===")
    company = CompanyService.create_company()
    print_company_details(company)


def generate_single_company_with_parameters() -> None:
    """Generate a single company entity with specific parameters."""
    print("\n=== Generating a single company with specific parameters ===")
    company = CompanyService.create_company(dataset="DE", count=1)
    print_company_details(company)


def generate_multiple_companies() -> None:
    """Generate multiple company entities with different country codes."""
    print("\n=== Generating multiple companies from different countries ===")
    
    # Create companies from different countries
    companies: List[Company] = []
    
    # Create US companies
    us_companies = CompanyService.create_companies(count=3, dataset="US")
    companies.extend(us_companies)
    
    # Create German companies
    de_companies = CompanyService.create_companies(count=2, dataset="DE")
    companies.extend(de_companies)
    
    # Create UK companies
    uk_companies = CompanyService.create_companies(count=2, dataset="GB")
    companies.extend(uk_companies)
    
    # Print all companies
    print("\nAll Companies:")
    print(f"Total count: {len(companies)}")
    for idx, company in enumerate(companies, 1):
        print_company_details(company, idx)


def filter_companies_by_sector() -> None:
    """Generate multiple companies and filter them by sector."""
    print("\n=== Filtering companies by sector ===")
    
    # Create a batch of companies
    companies = CompanyService.create_companies(count=10, dataset="US")
    
    # Find sectors represented in our data
    sectors = set(company.sector for company in companies if company.sector)
    
    # If we have at least one sector, filter companies by the first sector
    if sectors:
        selected_sector = next(iter(sectors))
        print(f"\nFiltering companies by sector: {selected_sector}")
        
        # Filter companies by sector
        filtered_companies = CompanyService.filter_companies_by_sector(companies, selected_sector)
        
        # Print filtered companies
        print(f"\nCompanies in {selected_sector} sector:")
        print(f"Total count: {len(filtered_companies)}")
        for idx, company in enumerate(filtered_companies, 1):
            print_company_details(company, idx)


def filter_companies_by_country() -> None:
    """Generate companies from multiple countries and filter by country."""
    print("\n=== Filtering companies by country ===")
    
    # Create mixed-country companies
    companies = []
    companies.extend(CompanyService.create_companies(count=3, dataset="US"))
    companies.extend(CompanyService.create_companies(count=3, dataset="DE"))
    companies.extend(CompanyService.create_companies(count=3, dataset="GB"))
    
    # Filter companies by country
    us_companies = CompanyService.filter_companies_by_country(companies, "US")
    
    # Print US companies
    print("\nUS Companies:")
    print(f"Total count: {len(us_companies)}")
    for idx, company in enumerate(us_companies, 1):
        print_company_details(company, idx)


def export_companies_to_json() -> None:
    """Generate companies and export them to JSON format."""
    print("\n=== Exporting companies to JSON ===")
    
    # Create companies
    companies = CompanyService.create_companies(count=5, dataset="US")
    
    # Convert to dictionaries
    company_dicts = CompanyService.companies_to_dict(companies)
    
    # Convert to JSON
    company_json = json.dumps(company_dicts, indent=2)
    
    # Print JSON
    print("\nCompanies in JSON format:")
    print(company_json)


def main() -> None:
    """Run all company generation examples."""
    print("=== Company Generation Examples ===")

    # Example 1: Generate a single company with default parameters
    generate_single_company()
    
    # Example 2: Generate a single company with specific parameters
    generate_single_company_with_parameters()
    
    # Example 3: Generate multiple companies from different countries
    generate_multiple_companies()
    
    # Example 4: Filter companies by sector
    filter_companies_by_sector()
    
    # Example 5: Filter companies by country
    filter_companies_by_country()
    
    # Example 6: Export companies to JSON
    export_companies_to_json()


if __name__ == "__main__":
    main()