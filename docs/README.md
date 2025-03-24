# DATAMIMIC Documentation

Welcome to the official documentation for DATAMIMIC, a powerful synthetic data generation platform that combines model-driven approaches with AI to produce high-quality, realistic data for development, testing, and demonstration.

## Documentation Sections

- [Core Concepts](#core-concepts)
- [Getting Started](#getting-started)
- [Domain-Driven Framework](#domain-driven-framework)
- [API Reference](#api-reference)
- [Advanced Topics](#advanced-topics)
- [Synthetic Data Quality](#synthetic-data-quality)

## Core Concepts

DATAMIMIC is built around several core concepts:

- **Model-Driven Generation** - Define your data models and let DATAMIMIC generate the appropriate instances
- **Domain-Specific Data** - Industry-specific data models with realistic properties and relationships
- **Weighted Distributions** - Statistical accuracy through real-world distribution patterns
- **Data Privacy** - Built-in tools for anonymization and pseudonymization
- **Advanced Features** - Comprehensive set of features for enterprise-grade synthetic data generation

## Getting Started

### Installation

To install DATAMIMIC Community Edition:

```bash
pip install datamimic-ce
```

For the Enterprise Edition with additional features:

```bash
pip install datamimic-ee
```

### Quick Start - XML Configuration

DATAMIMIC can be used with XML configuration files:

```xml
<setup>
    <generate name="users" count="100" target="CSV,JSON">
        <variable name="person" entity="Person(dataset='US')"/>
        <key name="id" generator="IncrementGenerator"/>
        <key name="first_name" script="person.given_name"/>
        <key name="last_name" script="person.family_name"/>
        <key name="email" script="person.email"/>
        <key name="age" script="person.age"/>
    </generate>
</setup>
```

Run with the command-line tool:

```bash
datamimic run config.xml
```

### Quick Start - Python SDK

DATAMIMIC can also be used directly in Python:

```python
from datamimic_ce.domains.common.services import PersonService
from datamimic_ce.domains.healthcare.services import PatientService

# Generate common entities
person_service = PersonService(dataset="US")
person = person_service.generate()
print(f"Generated person: {person.name}, {person.age} years old")

# Generate healthcare entities
patient_service = PatientService(dataset="US")
patient = patient_service.generate()
print(f"Patient {patient.patient_id}: {patient.given_name} {patient.family_name}")
print(f"Medical conditions: {', '.join(patient.conditions)}")

# Generate a batch of entities
patients = patient_service.generate_batch(count=100)
print(f"Generated {len(patients)} unique patients")
```

## Domain-Driven Framework

The Domain-Driven Framework is a powerful component of DATAMIMIC that provides industry-specific entities and realistic data generation based on weighted distributions.

For detailed documentation on the Domain-Driven Framework, see the [domain-specific documentation](data-domains/README.md).

Key domains include:
- **Common** - Basic entities like Person, Address, Company
- **Healthcare** - Medical entities like Patient, Doctor, Hospital
- **Finance** - Banking entities like Account, Transaction
- **Insurance** - Policy, Claim, and other insurance-specific entities
- **E-commerce** - Products, Orders, and online retail entities
- **Public Sector** - Government and public administration entities

## API Reference

Detailed API documentation is available for all DATAMIMIC components:

- [Command Line Interface](api/cli.md)
- [Configuration XML](api/xml-config.md)
- [Python SDK](api/python-sdk.md)
- [Extension APIs](api/extensions.md)

## Advanced Topics

DATAMIMIC offers a wide range of advanced capabilities:

- [Customizing Generators](advanced/custom-generators.md)
- [Database Integration](advanced/database-integration.md)
- [Data Privacy & Compliance](advanced/data-privacy.md)
- [Performance Optimization](advanced/performance.md)
- [Enterprise Features](advanced/enterprise-features.md)

Additional advanced capabilities include:

- **Custom Generators** - Extend the built-in generators with your own logic
- **Complex Relationships** - Define sophisticated relationships between entities
- **Multiple Export Formats** - Support for JSON, XML, CSV, RDBMS, MongoDB, and more
- **Data Anonymization** - GDPR-compliant data anonymization and masking
- **Validation Rules** - Define and enforce data validation rules
- **Scripting** - Extend functionality with Python scripts
- **Domain-Specific Models** - Industry-specific entities with realistic properties

## Synthetic Data Quality

The Enterprise Edition of DATAMIMIC delivers synthetic data with superior quality compared to open-source alternatives:

- **Statistical Accuracy** - Preserves statistical relationships with higher fidelity
- **Column Correlations** - Maintains dependencies between variables
- **Distribution Matching** - Creates realistic distribution patterns
- **ML Utility** - Produces synthetic data that maintains utility for machine learning

For detailed information about DATAMIMIC's synthetic data quality and benchmarks, see the [Enterprise Features](advanced/enterprise-features.md) documentation. 