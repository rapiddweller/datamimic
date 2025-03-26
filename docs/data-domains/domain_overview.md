# DATAMIMIC Domain Framework Overview

## Introduction

DATAMIMIC is a sophisticated synthetic data generation platform with multiple components. This documentation focuses specifically on the Domain-Driven Framework component of DATAMIMIC, which generates high-quality synthetic data that accurately reflects real-world distributions.

Unlike generic random data generators, DATAMIMIC's domain-driven approach organizes its functionality around specific industry domains to produce coherent, realistic data for testing, development, and demonstration purposes.

> **Note**: DATAMIMIC includes many additional capabilities beyond the Domain-Driven Framework documented here, such as data anonymization, schema-driven generation, and integration with various databases.

## Philosophy

The core philosophy of DATAMIMIC's Domain-Driven Framework is to generate synthetic data that:

1. **Reflects reality** - Uses weighted distributions based on real-world frequencies
2. **Maintains coherence** - Ensures logical relationships between data fields
3. **Preserves privacy** - Creates synthetic data without exposing private information
4. **Supports domains** - Tailors data generation to specific industry requirements

## Architecture Overview

The DATAMIMIC Domain-Driven Framework is organized into three primary components:

### 1. Domain Core (`domain_core/`)

Provides the foundation classes for all domain implementations:

- **BaseEntity**: Abstract base class for all domain entities
- **BaseDomainService**: Generic service class for entity generation
- **BaseDomainGenerator**: Base generator for domain-specific data
- **BaseLiteralGenerator**: Base class for primitive data generators
- **PropertyCache**: Utility for efficient property value caching

### 2. Domains (`domains/`)

Contains implementations for specific industry domains:

- **Common**: Shared entities (Person, Address, Company)
- **Healthcare**: Medical-related entities and data
- **Finance**: Banking and financial entities
- **Insurance**: Insurance-specific models
- **E-commerce**: Online retail data models
- **Public Sector**: Government and public administration models

Each domain package follows a consistent structure:

```
domains/
├── common/
│   ├── data_loaders/
│   ├── generators/
│   ├── literal_generators/
│   ├── models/
│   ├── services/
│   └── utils/
├── healthcare/
│   ├── data_loaders/
│   ├── generators/
│   ├── models/
│   └── services/
└── [other domains]
```

### 3. Domain Data (`domain_data/`)

Reference data organized by domain with distributions and realistic values:

- Country-specific datasets (US, DE, etc.)
- Distribution tables reflecting real-world frequencies
- Domain-specific terminology and reference data

## Getting Started

Here's a simple example to get started with DATAMIMIC's Domain-Driven Framework:

```python
# Import the required service
from datamimic_ce.domains.common.services import PersonService

# Create a service with specific parameters
person_service = PersonService(
    dataset="US",         # Use US-specific data
    min_age=18,           # Minimum age
    max_age=65,           # Maximum age
    female_quota=0.5      # Gender distribution
)

# Generate a person entity
person = person_service.generate()

# Access entity properties
print(f"Name: {person.name}")
print(f"Age: {person.age}")
print(f"Email: {person.email}")
```

## Key Benefits

DATAMIMIC's Domain-Driven Framework offers several advantages over traditional synthetic data generation approaches:

1. **Domain Specialization**: Industry-specific entities and attributes
2. **Realistic Distributions**: Weighted rather than uniform random selection
3. **Data Coherence**: Logically consistent relationships between entities
4. **Configurable Parameters**: Fine-tuned control over data characteristics
5. **Multiple Locales**: Support for region-specific data formats and distributions

## Next Steps

- [Domain Models Documentation](domain_models.md) - Detailed entity models by domain
- [Using Domain Services](domain_services.md) - Guide to using the service APIs
- [Weighted Distributions System](weighted_distributions.md) - How distributions work
- [Testing with DATAMIMIC](testing_with_datamimic.md) - Using synthetic data for testing