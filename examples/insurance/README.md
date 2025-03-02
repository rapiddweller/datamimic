# Insurance Domain for DataMimic

This directory contains examples showing how to use the Insurance domain in DataMimic to generate realistic insurance data.

## Overview

The Insurance domain provides models and generators for various insurance entities:

- Insurance Companies
- Insurance Products with Coverages
- Insurance Policies with Policy Holders

The domain follows a clean architecture approach with:

- **Models**: Pydantic models defining the structure of insurance entities
- **Data Loaders**: Classes to load reference data from CSV files
- **Services**: Business logic for generating insurance entities
- **Generators**: Classes that implement the DataMimic generator interface

## Usage

### Generating Insurance Companies

```python
from datamimic_ce.domains.insurance.services.insurance_company_service import InsuranceCompanyService

# Create a service for US insurance companies
service = InsuranceCompanyService(dataset="US")

# Generate a single insurance company
company = service.generate_insurance_company()

# Generate multiple insurance companies
companies = service.generate_insurance_companies(count=5)

# Access company properties
print(f"Company: {company.name}")
print(f"Code: {company.code}")
print(f"Founded: {company.founded_year}")
```

### Generating Insurance Products

```python
from datamimic_ce.domains.insurance.services.insurance_product_service import InsuranceProductService

# Create a service for German insurance products
service = InsuranceProductService(dataset="DE")

# Generate a single insurance product with coverages
product = service.generate_insurance_product(include_coverages=True)

# Generate multiple insurance products
products = service.generate_insurance_products(count=3)

# Access product properties
print(f"Product: {product.type}")
print(f"Code: {product.code}")
print(f"Coverages: {len(product.coverages)}")
```

### Generating Insurance Policies

```python
from datamimic_ce.domains.insurance.services.insurance_policy_service import InsurancePolicyService

# Create a service for US insurance policies
service = InsurancePolicyService(dataset="US")

# Generate a single insurance policy
policy = service.generate_insurance_policy()

# Generate multiple insurance policies
policies = service.generate_insurance_policies(count=3)

# Access policy properties
print(f"Policy Number: {policy.policy_number}")
print(f"Company: {policy.company.name}")
print(f"Product: {policy.product.type}")
print(f"Premium: ${policy.premium}")
print(f"Is Active: {policy.is_active}")
```

### Using DataMimic Generators

```python
from datamimic_ce.domains.insurance.generators.insurance_generators import (
    InsuranceCompanyGenerator,
    InsuranceProductGenerator,
    InsurancePolicyGenerator,
    InsuranceDataGenerator,
)

# Generate comprehensive insurance data
generator = InsuranceDataGenerator(
    dataset="US",
    include_companies=True,
    include_products=True,
    include_policies=True,
    num_companies=3,
    num_products=5,
    num_policies=10,
)

insurance_data = generator.generate()

# Access the generated data
print(f"Companies: {len(insurance_data['companies'])}")
print(f"Products: {len(insurance_data['products'])}")
print(f"Policies: {len(insurance_data['policies'])}")
```

## Data Files

The Insurance domain uses reference data from CSV files:

- `datamimic_ce/data/insurance/companies_US.csv`: US insurance company information
- `datamimic_ce/data/insurance/companies_DE.csv`: German insurance company information
- `datamimic_ce/data/insurance/products_US.csv`: US insurance product types
- `datamimic_ce/data/insurance/products_DE.csv`: German insurance product types
- `datamimic_ce/data/insurance/coverages_US.csv`: US insurance coverage types for products
- `datamimic_ce/data/insurance/coverages_DE.csv`: German insurance coverage types for products

## Example Script

The `generate_insurance_data.py` script demonstrates how to generate insurance data with the DataMimic library:

```bash
python generate_insurance_data.py
```

This will generate sample insurance companies, products, and policies for both US and German datasets, 
displaying the results in the console and saving them to JSON files in the `output` directory.