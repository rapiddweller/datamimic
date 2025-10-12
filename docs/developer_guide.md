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

### Dataset Loading (TL;DR)

Follow the dataset standard in `docs/standards/datasets.md` for all file access:

- Always resolve files via `dataset_path(...)` or the lightweight loaders in `datamimic_ce.utils.dataset_loader`.
- Pass base filenames to loaders; the helper appends `_{CC}.csv` using the generator’s normalized dataset.
- Honor strict mode with `DATAMIMIC_STRICT_DATASET=1` to validate presence without US fallback.
- Keep all dataset I/O in generators; models remain pure and only read values from their generator.

Examples

Headerless weighted CSV (value,weight):

```python
from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset, pick_one_weighted

values, weights = load_weighted_values_try_dataset(
    "ecommerce", "order", "coupon_prefixes.csv", dataset=self._dataset, start=Path(__file__)
)
prefix = pick_one_weighted(self._rng, values, weights)
```

Headered weighted CSV (with `weight` column):

```python
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil

path = dataset_path("ecommerce", f"product_categories_{self._dataset}.csv", start=Path(__file__))
header, rows = FileUtil.read_csv_to_dict_of_tuples_with_header(path, ",")
weights = [float(r[header["weight"]]) for r in rows]
category = self._rng.choices(rows, weights=weights, k=1)[0][header["category"]]
```

Per‑category specialization (base filename carries the key):

```python
values, weights = load_weighted_values_try_dataset(
    "ecommerce", f"product_nouns_{category}.csv", dataset=self._dataset, start=Path(__file__)
)
```

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

# Reproducible run: inject a seeded RNG
from random import Random
seeded = Random(42)

# Create a service instance (pass rng when supported by the service)
person_service = PersonService(dataset="US", rng=seeded)  # Specify dataset + seed

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

# Generate a batch of people (deterministic when seeded)
person_service = PersonService(dataset="US", rng=Random(1234))
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
        # Create services (seed for reproducibility)
        from random import Random
        rng = Random(2025)
        self.account_service = BankAccountService(dataset="US")
        self.transaction_service = TransactionService(dataset="US")

        # Generate test data
        self.test_account = self.account_service.generate()
        self.test_transactions = self.transaction_service.generate_batch(count=10)
        
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
6. **Keep models pure** - No dataset I/O or module `random` in models; use the generator’s RNG
7. **Declare supported datasets** - Services should report supported ISO codes via `compute_supported_datasets([...], start=Path(__file__))`

### Strict Dataset Mode

Set `DATAMIMIC_STRICT_DATASET=1` to enforce that dataset‑suffixed files must exist for the selected dataset (no US fallback). This is useful in CI and when validating new datasets.

## Seeding & Reproducibility

DATAMIMIC favors explicit seeding via injected RNGs instead of hidden global seeds.

- When a service exposes `rng` in its constructor (e.g., `PersonService`, `PatientService`), pass a seeded `random.Random`:

```python
from random import Random
from datamimic_ce.domains.healthcare.services import PatientService

svc = PatientService(dataset="US", rng=Random(99))
pat1 = svc.generate()
pat2 = svc.generate()  # deterministic sequence for the same seed
```

- When a service does not expose `rng`, seed the underlying generator directly and construct the model:

```python
from random import Random
from datamimic_ce.domains.ecommerce.generators.product_generator import ProductGenerator
from datamimic_ce.domains.ecommerce.models.product import Product

gen = ProductGenerator(dataset="US", rng=Random(42))
prod = Product(gen)
```

- Composite generators propagate the injected RNG to sub-generators (e.g., policy → company/product/coverage), keeping all draws in one deterministic stream.

Tip: reuse the same seeded `Random` instance for related generators if you want stable cross-entity correlation; create separate `Random` instances to isolate streams.

### XML Demographics & Seeding

Entity variables in XML can pass demographic constraints and a deterministic seed directly to services that support `Person`-based generation (e.g., `Person`, `Patient`, `Doctor`, `PoliceOfficer`).

Example:

```xml
<setup>
  <generate name="seeded_doctors" count="3" target="CSV">
    <variable
      name="doc"
      entity="Doctor"
      dataset="US"
      ageMin="30"
      ageMax="45"
      conditionsInclude="Diabetes"
      conditionsExclude="Hypertension"
      rngSeed="1234" />
    <key name="full_name" script="doc.full_name" />
    <key name="age" script="doc.age" />
    <array name="certifications" script="doc.certifications" />
  </generate>
</setup>
```

Notes:
- `ageMin`, `ageMax`, `conditionsInclude`, `conditionsExclude` map to the service’s `DemographicConfig`.
- `rngSeed` seeds the service RNG for deterministic sequences.
- When attributes are omitted, defaults apply; models remain pure and never access module-level randomness.

## Extending DATAMIMIC

To create custom domain entities:

1. Extend the appropriate base class
2. Implement domain-specific attributes
3. Create a corresponding service
4. Add weighted datasets for realistic distributions

Example of a custom entity:

```python
from datamimic_ce.domains.domain_core import BaseEntity


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
