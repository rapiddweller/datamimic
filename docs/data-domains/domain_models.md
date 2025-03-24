# DATAMIMIC Domain Models

This document describes the entity models available in DATAMIMIC's Domain-Driven Framework, organized by industry domain.

> **Note**: This documentation focuses specifically on the domain models within DATAMIMIC's Domain-Driven Framework. DATAMIMIC offers many additional capabilities beyond what is documented here.

## Entity Structure

DATAMIMIC entities follow a consistent pattern:

1. **Property-based access**: All data is accessed through properties
2. **Lazy generation**: Values are generated only when accessed
3. **Caching**: Generated values are cached to ensure consistency
4. **Based on BaseEntity**: All entities inherit from the core BaseEntity class

The basic structure of a DATAMIMIC entity:

```python
from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache

class ExampleEntity(BaseEntity):
    def __init__(self, generator):
        super().__init__()
        self._generator = generator
        
    @property
    @property_cache
    def id(self) -> str:
        # Generated once and cached
        return self._generator.generate_id()
        
    @property
    @property_cache
    def attribute(self) -> str:
        # Uses weighted distribution
        return self._generator.attribute_generator.generate()
        
    def to_dict(self) -> dict:
        # Convert entity to dictionary
        return {
            "id": self.id,
            "attribute": self.attribute
        }
```

## Domain Models

### Common Domain

Provides shared entities used across all domains:

#### Person

```
Person
├── gender: str
├── given_name: str
├── family_name: str
├── name: str
├── age: int
├── date_of_birth: date
├── email: str
├── phone_number: str
├── address: Address
└── nationality: str
```

#### Address

```
Address
├── street: str
├── house_number: str
├── city: City
├── postal_code: str
├── state: str
├── country: Country
└── full_address: str
```

#### Company

```
Company
├── name: str
├── industry: str
├── size: str
├── address: Address
├── phone_number: str
├── website: str
└── founded_year: int
```

### Healthcare Domain

Specialized entities for healthcare applications:

#### Patient

```
Patient
├── patient_id: str
├── medical_record_number: str
├── ssn: str
├── gender: str
├── given_name: str
├── family_name: str
├── date_of_birth: date
├── blood_type: str
├── allergies: List[str]
├── conditions: List[str]
├── medications: List[str]
├── emergency_contact: Person
└── insurance_provider: str
```

#### Doctor

```
Doctor
├── doctor_id: str
├── license_number: str
├── gender: str
├── given_name: str
├── family_name: str
├── specialty: str
├── qualifications: List[str]
├── hospital: Hospital
└── appointments: List[Appointment]
```

#### Hospital

```
Hospital
├── name: str
├── address: Address
├── departments: List[str]
├── capacity: int
├── staff_count: int
└── specialties: List[str]
```

### Finance Domain

Financial services entities:

#### BankAccount

```
BankAccount
├── account_number: str
├── account_type: str
├── owner: Person
├── balance: Decimal
├── currency: str
├── open_date: date
└── status: str
```

#### Transaction

```
Transaction
├── transaction_id: str
├── account: BankAccount
├── amount: Decimal
├── transaction_type: str
├── date: datetime
├── description: str
├── category: str
└── merchant: str
```

### Insurance Domain

Insurance-specific entities:

#### InsurancePolicy

```
InsurancePolicy
├── policy_number: str
├── policy_type: str
├── policyholder: Person
├── start_date: date
├── end_date: date
├── premium: Decimal
├── coverage_amount: Decimal
└── status: str
```

#### Claim

```
Claim
├── claim_id: str
├── policy: InsurancePolicy
├── date_filed: date
├── amount: Decimal
├── description: str
├── status: str
└── resolution_date: date
```

### E-commerce Domain

Online retail entities:

#### Product

```
Product
├── product_id: str
├── name: str
├── description: str
├── category: str
├── price: Decimal
├── inventory: int
├── manufacturer: str
└── ratings: List[Rating]
```

#### Order

```
Order
├── order_id: str
├── customer: Person
├── items: List[Product]
├── total_amount: Decimal
├── date: datetime
├── shipping_address: Address
├── payment_method: str
└── status: str
```

### Public Sector Domain

Government and public administration entities:

#### PublicOffice

```
PublicOffice
├── name: str
├── type: str
├── address: Address
├── jurisdiction: str
├── staff_count: int
└── services: List[str]
```

#### EducationalInstitution

```
EducationalInstitution
├── name: str
├── type: str
├── address: Address
├── founding_year: int
├── student_count: int
├── staff_count: int
├── programs: List[str]
└── accreditations: List[str]
```

## Entity Relationships

Entities can be related to create complex, realistic data structures:

- A Person can have multiple BankAccounts
- A Patient can have a primary Doctor
- A Doctor can work at a Hospital
- An Order contains multiple Products
- A Claim is linked to an InsurancePolicy

These relationships maintain logical consistency, ensuring generated data reflects realistic scenarios. 