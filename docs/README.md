# DATAMIMIC Documentation

Welcome to the official documentation for DATAMIMIC, a powerful synthetic data generation platform that combines domain-driven approaches with weighted distributions to produce high-quality, realistic data for development, testing, and demonstration.

> **Note**: For comprehensive documentation including detailed model descriptions, exporters, importers, platform UI, and more, please visit our official online documentation at [https://docs.datamimic.io/](https://docs.datamimic.io/)

This project documentation focuses specifically on:
- Using data domains
- Command-line interface
- Getting started with the Community Edition
- Developer integration

## Documentation Sections

- [Core Concepts](#core-concepts)
- [Getting Started](#getting-started)
- [Domain-Driven Framework](data-domains/README.md)
- [Examples](examples/README.md)
- [API Reference](api/README.md)
- [Advanced Topics](advanced/README.md)
- [Developer Guide](developer_guide.md)

## Core Concepts

DATAMIMIC is built around several core concepts:

- **Domain-Driven Generation** - Industry-specific data models with realistic properties and relationships
- **Weighted Distributions** - Statistical accuracy through real-world distribution patterns
- **Entity Relationships** - Create complex, interconnected data entities
- **Data Privacy** - Built-in tools for anonymization and pseudonymization
- **Multi-Domain Support** - Healthcare, Finance, Insurance, E-commerce, and more

For detailed information on DATAMIMIC's architecture and model descriptions, please refer to our [online documentation](https://docs.datamimic.io/).

## Getting Started

### Installation

To install DATAMIMIC Community Edition:

```bash
pip install datamimic-ce
```

### Quick Start - Python API

The fastest way to get started with DATAMIMIC is using the Python API:

```python
from datamimic_ce.domains.common.services import PersonService

# Create a service instance
person_service = PersonService(dataset="US")

# Generate a single person
person = person_service.generate()

# Access person attributes
print(f"Name: {person.name}")
print(f"Age: {person.age}")
print(f"Email: {person.email}")
print(f"Address: {person.address.street}, {person.address.city}, {person.address.state}")
```

### Generate Healthcare Data

DATAMIMIC provides specialized services for different domains:

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

### Generate Multiple Entities

You can easily generate multiple entities at once:

```python
# Generate a batch of people
people = person_service.generate_batch(count=100)
print(f"Generated {len(people)} unique people")

# Export to other formats if needed
for person in people[:5]:
    print(f"{person.name}, {person.age} years old")
```

## Domain-Driven Framework

DATAMIMIC's domain-driven framework organizes synthetic data generation by industry domains:

- **Common Domain** - [Person](examples/person_generation.md), Address, Company
- **Healthcare Domain** - [Patient](examples/healthcare_generation.md), Doctor, Hospital
- **Finance Domain** - BankAccount, Transaction, Loan
- **Insurance Domain** - Policy, Claim, Insured
- **E-commerce Domain** - Product, Order, Customer

For detailed documentation on the domain-driven framework, see the [domain-specific documentation](data-domains/README.md).

## Examples

DATAMIMIC includes detailed examples demonstrating various use cases:

- [Person Generation](examples/person_generation.md) - Generate and work with person entities
- [Healthcare Data Generation](examples/healthcare_generation.md) - Create realistic healthcare data

## API Reference

The API reference documentation covers:

- Python SDK for all domains
- Configuration options
- Extension APIs

For complete API documentation, see the [API Reference](api/README.md).

## Advanced Topics

DATAMIMIC offers advanced capabilities for power users:

- [Enterprise Features](advanced/enterprise-features.md) - Advanced features available in the Enterprise Edition
- Custom generators and extensions
- Performance optimization
- Database integration

For detailed information on advanced topics, see the [Advanced Topics](advanced/README.md) documentation.

For comprehensive information on the DATAMIMIC platform UI, advanced models, and enterprise capabilities, please visit our [official online documentation](https://docs.datamimic.io/).

## Developer Guide

For developers looking to integrate DATAMIMIC into their applications or extend its functionality, we provide a comprehensive [Developer Guide](developer_guide.md).

## Verified Examples

All the examples included in this documentation have been tested and verified to work with the current version of DATAMIMIC. The test results can be found in our test scripts that validate each example. 