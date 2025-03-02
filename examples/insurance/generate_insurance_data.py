# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Generate insurance data example.

This script demonstrates how to generate insurance-related data using the DataMimic library.
"""

import json
import os
import sys
from pathlib import Path

# Add the project root to the Python path to allow importing the DataMimic modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datamimic_ce.domains.insurance.generators.insurance_generators import (
    InsuranceCompanyGenerator,
    InsuranceDataGenerator,
    InsurancePolicyGenerator,
    InsuranceProductGenerator,
)
from datamimic_ce.domains.insurance.services.insurance_company_service import InsuranceCompanyService
from datamimic_ce.domains.insurance.services.insurance_policy_service import InsurancePolicyService
from datamimic_ce.domains.insurance.services.insurance_product_service import InsuranceProductService


def generate_insurance_companies(count: int = 5, dataset: str = "US"):
    """Generate insurance company data.
    
    Args:
        count: The number of insurance companies to generate
        dataset: The country code to use for data generation
    """
    print(f"\nGenerating {count} insurance companies for dataset {dataset}:")
    service = InsuranceCompanyService(dataset=dataset)
    companies = service.generate_insurance_companies(count=count)
    
    for i, company in enumerate(companies, 1):
        print(f"\nCompany {i}:")
        print(f"  Name: {company.name}")
        print(f"  Code: {company.code}")
        print(f"  Founded: {company.founded_year}")
        print(f"  Headquarters: {company.headquarters}")
        print(f"  Website: {company.website}")
        
    # Save to JSON file
    os.makedirs("output", exist_ok=True)
    output_file = f"output/insurance_companies_{dataset}.json"
    with open(output_file, "w") as f:
        json.dump([company.dict() for company in companies], f, indent=2)
    print(f"\nSaved insurance companies to {output_file}")


def generate_insurance_products(count: int = 5, dataset: str = "US"):
    """Generate insurance product data.
    
    Args:
        count: The number of insurance products to generate
        dataset: The country code to use for data generation
    """
    print(f"\nGenerating {count} insurance products for dataset {dataset}:")
    service = InsuranceProductService(dataset=dataset)
    products = service.generate_insurance_products(count=count)
    
    for i, product in enumerate(products, 1):
        print(f"\nProduct {i}:")
        print(f"  Type: {product.type}")
        print(f"  Code: {product.code}")
        print(f"  Description: {product.description}")
        print(f"  Coverages ({len(product.coverages)}):")
        for j, coverage in enumerate(product.coverages, 1):
            print(f"    Coverage {j}:")
            print(f"      Name: {coverage.name}")
            print(f"      Code: {coverage.code}")
            if coverage.max_coverage == float('inf'):
                max_coverage = "Unlimited"
            else:
                max_coverage = f"{coverage.max_coverage:,.2f}"
            print(f"      Coverage Range: {coverage.min_coverage:,.2f} - {max_coverage}")
        
    # Save to JSON file
    os.makedirs("output", exist_ok=True)
    output_file = f"output/insurance_products_{dataset}.json"
    with open(output_file, "w") as f:
        json.dump([json.loads(product.json()) for product in products], f, indent=2)
    print(f"\nSaved insurance products to {output_file}")


def generate_insurance_policies(count: int = 5, dataset: str = "US"):
    """Generate insurance policy data.
    
    Args:
        count: The number of insurance policies to generate
        dataset: The country code to use for data generation
    """
    print(f"\nGenerating {count} insurance policies for dataset {dataset}:")
    service = InsurancePolicyService(dataset=dataset)
    policies = service.generate_insurance_policies(count=count)
    
    for i, policy in enumerate(policies, 1):
        print(f"\nPolicy {i}:")
        print(f"  Policy Number: {policy.policy_number}")
        print(f"  Company: {policy.company.name}")
        print(f"  Product: {policy.product.type}")
        print(f"  Policy Holder: {policy.policy_holder.first_name} {policy.policy_holder.last_name}")
        print(f"  Premium: ${policy.premium:.2f} ({policy.premium_frequency})")
        print(f"  Start Date: {policy.start_date}")
        print(f"  End Date: {policy.end_date}")
        print(f"  Status: {policy.status}")
        print(f"  Is Active: {policy.is_active}")
        print(f"  Total Coverage: ${policy.total_coverage:,.2f}")
        print(f"  Annual Premium: ${policy.annual_premium:,.2f}")
        
    # Save to JSON file
    os.makedirs("output", exist_ok=True)
    output_file = f"output/insurance_policies_{dataset}.json"
    with open(output_file, "w") as f:
        json.dump([json.loads(policy.json()) for policy in policies], f, indent=2)
    print(f"\nSaved insurance policies to {output_file}")


def generate_comprehensive_insurance_data(dataset: str = "US"):
    """Generate comprehensive insurance data including companies, products, and policies.
    
    Args:
        dataset: The country code to use for data generation
    """
    print(f"\nGenerating comprehensive insurance data for dataset {dataset}:")
    generator = InsuranceDataGenerator(
        dataset=dataset,
        include_companies=True,
        include_products=True,
        include_policies=True,
        num_companies=3,
        num_products=5,
        num_policies=10,
    )
    insurance_data = generator.generate()
    
    print("\nInsurance Data Summary:")
    print(f"  Dataset: {insurance_data['dataset']}")
    print(f"  Companies: {len(insurance_data['companies'])}")
    print(f"  Products: {len(insurance_data['products'])}")
    print(f"  Policies: {len(insurance_data['policies'])}")
    
    # Save to JSON file
    os.makedirs("output", exist_ok=True)
    output_file = f"output/insurance_data_{dataset}.json"
    with open(output_file, "w") as f:
        json.dump(insurance_data, f, indent=2)
    print(f"\nSaved comprehensive insurance data to {output_file}")


def main():
    """Main function to demonstrate insurance data generation."""
    print("Insurance Data Generation Examples")
    print("=================================")
    
    # Generate insurance companies
    generate_insurance_companies(count=3, dataset="US")
    generate_insurance_companies(count=3, dataset="DE")
    
    # Generate insurance products
    generate_insurance_products(count=3, dataset="US")
    generate_insurance_products(count=3, dataset="DE")
    
    # Generate insurance policies
    generate_insurance_policies(count=3, dataset="US")
    generate_insurance_policies(count=3, dataset="DE")
    
    # Generate comprehensive insurance data
    generate_comprehensive_insurance_data(dataset="US")
    generate_comprehensive_insurance_data(dataset="DE")


if __name__ == "__main__":
    main()