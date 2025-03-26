# DATAMIMIC Developer Guide

## Introduction

DATAMIMIC is a powerful synthetic data generation framework built on a domain-driven architecture that produces high-quality, weighted dataset-driven synthetic data for various industries. Unlike generic data generation libraries, DATAMIMIC focuses on creating data that accurately mimics real-world distributions and relationships, making it ideal for testing, training, and demonstration purposes.

> **Note**: For comprehensive documentation including detailed model descriptions, exporters, importers, platform UI, and more, please visit our official online documentation at [https://docs.datamimic.io/](https://docs.datamimic.io/)

## Installation

To install DATAMIMIC Community Edition:

```bash
pip install datamimic-ce
```

## Core Architecture

DATAMIMIC is built on three main architectural components:

1. **Domain Core** - Provides the foundational classes and interfaces for all domain models
2. **Domains** - Industry-specific implementations of entities and business logic
3. **Domain Data** - Contains weighted datasets that ensure realistic data distributions

### Domain Core Components

The core components define the base interfaces and abstract classes:

- **BaseEntity** - The foundational class for all domain entities
- **BaseDomainService** - Service layer for generating and managing domain entities
- **BaseDomainGenerator** - Handles generation of complete domain entities
- **BaseLiteralGenerator** - Generates primitive values with weighted distributions

## Using Domain Services

Domain services are the primary entry point for generating synthetic data. Each industry domain has specialized services for generating domain-specific entities.

### Example 1: Generating a Person

```python
from datamimic_ce.domains.common.services import PersonService

# Create a service instance
person_service = PersonService(dataset="US")  # Specify locale/dataset

# Generate a single person
person = person_service.generate()

# Access person attributes
print(f"Name: {person.name}")
print(f"Age: {person.age}")
print(f"Email: {person.email}")
print(f"Address: {person.address.street}, {person.address.city}, {person.address.state}")
```

### Example 2: Generating Healthcare Data

```python
from datamimic_ce.domains.healthcare.services import PatientService

# Create a patient service
patient_service = PatientService()

# Generate a patient with medical information
patient = patient_service.generate()

# Access patient-specific attributes
print(f"Patient ID: {patient.patient_id}")
print(f"Blood Type: {patient.blood_type}")
print(f"Medical Conditions: {patient.conditions}")
```

### Example 3: Generating Batch Data

```python
from datamimic_ce.domains.common.services import PersonService
import json
from datetime import datetime

# Create a JSON encoder for datetime objects
class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Generate a batch of people
person_service = PersonService(dataset="US")
people = person_service.generate_batch(count=100)

# Convert to JSON for storage or transmission
people_json = json.dumps([p.to_dict() for p in people], cls=DatetimeEncoder)
```

## Domain Models

DATAMIMIC includes specialized models for various industry domains:

### Healthcare Domain

- **Patient** - Complete patient profile with medical history
- **Doctor** - Medical professional with specialty and credentials
- **Hospital** - Medical facility with departments and services
- **MedicalRecord** - Patient medical history and documentation

### Finance Domain

- **BankAccount** - Account details including type and balance
- **Transaction** - Financial transactions with metadata
- **Loan** - Loan products with terms and interest rates
- **Investment** - Investment vehicles and portfolios

### Insurance Domain

- **Policy** - Insurance policies across different lines
- **Claim** - Insurance claims with status and history
- **Insured** - Policy holder details
- **RiskProfile** - Risk assessment and scoring

### E-commerce Domain

- **Product** - Product catalog items with attributes
- **Order** - Customer orders with line items
- **Customer** - E-commerce customer profiles
- **Review** - Product reviews and ratings

## Weighted Distributions

A key advantage of DATAMIMIC is its use of weighted distributions based on real-world data patterns:

```python
from datamimic_ce.domains.healthcare.services import PatientService

# Generate patients with realistic age distributions
# (weighted toward common age brackets in healthcare settings)
patient_service = PatientService()
elderly_patients = []

# Generate 100 patients - the age distribution will follow
# realistic patterns based on domain-specific weighted datasets
patients = patient_service.generate_batch(count=100)

# The distribution of ages, conditions, etc. will reflect 
# real-world patterns, not random uniform distributions
```

## Unit Testing with DATAMIMIC

DATAMIMIC excels at creating test data for unit and integration tests:

```python
import unittest
from datamimic_ce.domains.finance.services import BankAccountService, TransactionService
from my_application.transaction_processor import TransactionProcessor

class TestTransactionProcessor(unittest.TestCase):
    def setUp(self):
        # Create services
        self.account_service = BankAccountService()
        self.transaction_service = TransactionService()
        
        # Generate test data
        self.test_account = self.account_service.generate()
        self.test_transactions = self.transaction_service.generate_batch(
            count=10,
            account_id=self.test_account.account_id
        )
        
        # Initialize system under test
        self.processor = TransactionProcessor()
        
    def test_transaction_processing(self):
        # Use generated data in test
        result = self.processor.process_transactions(
            self.test_account, 
            self.test_transactions
        )
        
        # Assertions
        self.assertEqual(len(result.processed), 10)
        self.assertEqual(result.error_count, 0)
```

## Comparison with Other Libraries

| Feature | DATAMIMIC | Faker | Mimesis |
|---------|-----------|-------|---------|
| Domain-specific models | ✓ | ✗ | Partial |
| Realistic distributions | ✓ | ✗ | ✗ |
| Related entity generation | ✓ | ✗ | ✗ |
| Industry-specific data | ✓ | Partial | Partial |
| Consistency across entities | ✓ | ✗ | ✗ |
| Weighted datasets | ✓ | ✗ | ✗ |
| Multiple locales/regions | ✓ | ✓ | ✓ |

## Best Practices

1. **Use domain-specific services** - Choose the most specific service for your needs
2. **Generate related entities together** - Use batch generation for consistent relationships
3. **Explore available attributes** - Each entity has rich metadata beyond basic fields
4. **Set the locale** - Use the `dataset` parameter to generate region-specific data
5. **Leverage to_dict()** - Convert entities to dictionaries for serialization

## Extending DATAMIMIC

To create custom domain entities:

1. Extend the appropriate base class
2. Implement domain-specific attributes
3. Create a corresponding service
4. Add weighted datasets for realistic distributions

Example of a custom entity:

```python
from datamimic_ce.domain_core.base_entity import BaseEntity

class CustomEntity(BaseEntity):
    def __init__(self):
        super().__init__()
        self.custom_id = None
        self.custom_attribute = None
        
    @classmethod
    def from_dict(cls, data):
        entity = cls()
        entity.custom_id = data.get("custom_id")
        entity.custom_attribute = data.get("custom_attribute")
        return entity
        
    def to_dict(self):
        return {
            "custom_id": self.custom_id,
            "custom_attribute": self.custom_attribute
        }
```

## Conclusion

DATAMIMIC's domain-driven architecture provides a powerful framework for generating synthetic data that accurately reflects real-world patterns and relationships. By leveraging weighted distributions and domain-specific models, DATAMIMIC enables developers to create high-quality test data, training datasets, and demonstration data that closely mimics production systems.

For further assistance or to contribute to the project, visit our GitHub repository or contact the development team.
