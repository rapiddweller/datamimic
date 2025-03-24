# DATAMIMIC Domain-Driven Framework Documentation

Welcome to the documentation for the Domain-Driven Framework component of DATAMIMIC, a sophisticated synthetic data generation platform. This documentation specifically covers the domain-driven architecture for generating weighted, statistically accurate synthetic data.

> **Note**: This documentation focuses specifically on the Domain-Driven Architecture features of DATAMIMIC. DATAMIMIC offers many additional capabilities beyond what is documented here.

## Core Documentation

- [Domain Framework Overview](domain_overview.md) - Introduction to DATAMIMIC's domain framework architecture
- [Domain Models](domain_models.md) - Detailed entity models organized by domain
- [Using Domain Services](domain_services.md) - Guide to using the domain service APIs
- [Weighted Distributions System](weighted_distributions.md) - How DATAMIMIC's distribution system works
- [Testing with DATAMIMIC](testing_with_datamimic.md) - Using synthetic data for testing
- [DATAMIMIC vs Other Libraries](comparison.md) - Comparison with other data generation tools

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
patient_service = PatientService(dataset="US")

# Generate a single patient
patient = patient_service.generate()

# Access patient properties
print(f"Patient ID: {patient.patient_id}")
print(f"Name: {patient.given_name} {patient.family_name}")
print(f"Blood Type: {patient.blood_type}")
print(f"Medical Conditions: {patient.conditions}")
```

### 3. Generate Finance Data

```python
from datamimic_ce.domains.finance.services import BankAccountService, TransactionService

# Create finance services
account_service = BankAccountService(dataset="US")
transaction_service = TransactionService(dataset="US")

# Generate an account
account = account_service.generate()

# Generate transactions for that account
transactions = transaction_service.generate_for_account(account, count=5)

# Access financial data
print(f"Account: {account.account_number}")
print(f"Balance: {account.balance} {account.currency}")
print(f"Transactions: {len(transactions)}")
``` 