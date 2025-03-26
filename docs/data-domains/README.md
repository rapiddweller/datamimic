# DATAMIMIC Domain-Driven Framework Documentation

Welcome to the documentation for the Domain-Driven Framework component of DATAMIMIC, a sophisticated synthetic data generation platform. This documentation specifically covers the domain-driven architecture for generating weighted, statistically accurate synthetic data.

> **Note**: This documentation focuses specifically on the Domain-Driven Architecture features of DATAMIMIC. For comprehensive documentation including detailed model descriptions, exporters, importers, platform UI, and more, please visit our official online documentation at [https://docs.datamimic.io/](https://docs.datamimic.io/)

## Core Documentation

- [Domain Framework Overview](domain_overview.md) - Introduction to DATAMIMIC's domain framework architecture
- [Domain Models](domain_models.md) - Detailed entity models organized by domain
- [Using Domain Services](domain_services.md) - Guide to using the domain service APIs
- [Weighted Distributions System](weighted_distributions.md) - How DATAMIMIC's distribution system works
- [Testing with DATAMIMIC](testing_with_datamimic.md) - Using synthetic data for testing

> For more detailed information on domain models, exporters, importers, and platform integration, please refer to our [official online documentation](https://docs.datamimic.io/).

## Available Domains

DATAMIMIC implements several industry-specific domains:

| Domain        | Description                                 | Key Entities                                        |
|---------------|---------------------------------------------|-----------------------------------------------------|
| Common        | Generally useful entities                   | Person, Address, Company, City, Country             |
| Healthcare    | Medical and healthcare entities             | Patient, Doctor, Hospital, MedicalProcedure,        |
| Finance       | Financial services entities                 | BankAccount, Transaction, Bank, CreditCard          |
| E-commerce    | Online shopping and retail                  | Product, Order                                      |
| Insurance     | Insurance industry entities                 | Policy, Product, Company, Coverage                  |
| Public Sector | Government and public administration        | Citizen, Agency, EducationalInstitution             |

## Quick Start Guide

### 1. Generate a Person Entity

```python
from datamimic_ce.domains.common.services import PersonService

# Create a service
person_service = PersonService(dataset="US")

# Generate a single entity
person = person_service.generate()

# Access entity properties
print(f"Name: {person.name}")
print(f"Gender: {person.gender}")
print(f"Age: {person.age}")
print(f"Email: {person.email}")
```

### 2. Generate Healthcare Data

```python
from datamimic_ce.domains.healthcare.services import PatientService

# Create a healthcare service
patient_service = PatientService()

# Generate a single patient
patient = patient_service.generate()

# Access patient properties
print(f"Patient ID: {patient.patient_id}")
print(f"Name: {patient.full_name}")
print(f"Blood Type: {patient.blood_type}")
print(f"Medical Conditions: {patient.conditions}")
```

### 3. Generate Finance Data

```python
from datamimic_ce.domains.finance.services import BankAccountService, TransactionService

# Create finance services
account_service = BankAccountService()
transaction_service = TransactionService()

# Generate an account
account = account_service.generate()

# Generate transactions
transactions = transaction_service.generate_batch(count=5)

# Access financial data
print(f"Account: {account.account_number}")
print(f"Balance: ${account.balance:.2f}")
print(f"Transactions: {len(transactions)}")
```

## Complete Examples

For complete working examples, see:

- [Person Generation Example](../examples/person_generation.md)
- [Healthcare Data Example](../examples/healthcare_generation.md)

## Domain Service Reference

Each domain includes specialized services for generating entities:

- **Common Domain**: `PersonService`, `AddressService`, `CompanyService`, `CountryService`, `CityService`
- **Healthcare Domain**: `PatientService`, `DoctorService`, `HospitalService`, `MedicalProcedureService`, `MedicalDeviceService`
- **Finance Domain**: `BankAccountService`, `TransactionService`, `CrediCardService`, `BankService`
- **E-commerce Domain**: `ProductService`, `OrderService`
- **Insurance Domain**: `InsurancePolicyService`, `InsuranceCompanyService`, `InsuranceCoverageService`, `InsuranceProductService`

See the [Domain Services](domain_services.md) documentation for detailed API reference.

## Implementation Status

All examples and documentation in this section have been verified to work with the current version of DATAMIMIC. Our continuous testing ensures that the documented functionality is accurate and reliable. 