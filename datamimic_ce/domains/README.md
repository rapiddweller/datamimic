# DATAMIMIC Domain Architecture

This directory contains the domain-based implementation of DATAMIMIC entities. Each subdirectory represents a specific business domain with its own set of entities, data loaders, and generators.

## Directory Structure

Each domain follows a consistent structure:

```
domains/
├── common/           # Common entities like Address, Person, Company
│   ├── data_loaders/ # Data loading components
│   ├── generators/   # Specialized data generators
│   ├── models/       # Entity models
│   ├── services/     # High-level domain services
│   └── utils/        # Domain-specific utilities
├── healthcare/       # Healthcare-specific entities
├── finance/          # Finance domain entities
├── ecommerce/        # E-commerce domain entities
└── ...               # Other domains
```

## Domain Overview

| Domain        | Description                                 | Key Entities                                  |
|---------------|---------------------------------------------|-----------------------------------------------|
| common        | Generally useful entities                   | Person, Address, Company, City, Country       |
| healthcare    | Medical and healthcare entities             | Patient, Doctor, Hospital, MedicalDevice      |
| finance       | Financial services entities                 | BankAccount, CreditCard, Transaction, Payment |
| ecommerce     | Online shopping and retail                  | Product, Order, UserAccount, CRM              |
| insurance     | Insurance industry entities                 | InsurancePolicy, InsuranceCompany             |
| public_sector | Government and public administration        | AdministrationOffice, EducationalInstitution  |

## Usage in XML Configurations

Entities from these domains can be used in XML configurations with a simple syntax:

```xml
<variable name="company" entity="Company" dataset="US" />
<variable name="patient" entity="Patient" dataset="US" />
<variable name="product" entity="Product" dataset="US" />
```

The framework automatically maps entity names to their domain-specific implementations.

## Adding New Domains

To add a new domain:

1. Create a new subdirectory with the domain name
2. Follow the standard domain structure (models, data_loaders, etc.)
3. Implement domain-specific entities following the entity implementation guide
4. Register the new entities in the entity mapping in `variable_task.py`
5. Add documentation for the new domain

## Documentation

For more information on the domain architecture and entity implementation, see:

- [Domain Architecture](../../docs/architecture/domain_architecture.md)
- [Entity Implementation Guide](../../docs/architecture/entity_implementation.md)
- [Entity Domains](../../docs/architecture/entity_domains.md)