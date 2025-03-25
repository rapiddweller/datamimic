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
├── given_name: str
├── family_name: str
├── name: str
├── gender: str
├── age: int
├── birthdate: datetime
├── email: str
├── phone: str
├── mobile_phone: str
├── address: Address
├── academic_title: str
├── salutation: str
└── nobility_title: str
```

#### Address

```
Address
├── street: str
├── house_number: str
├── city: str
├── state: str
├── postal_code: str
├── zip_code: str
├── country: str
├── country_code: str
├── phone: str
├── mobile_phone: str
├── office_phone: str
├── private_phone: str
├── fax: str
├── organization: str
└── full_address: str
```

#### City

```
City
├── name: str
├── postal_code: str
├── area_code: str
├── state: str
├── language: str
├── population: int
├── name_extension: str
├── country: str
└── country_code: str
```

#### Country

```
Country
├── iso_code: str
├── name: str
├── default_language_locale: str
├── phone_code: str
└── population: str
```

#### Company

```
Company
├── id: str
├── short_name: str
├── full_name: str
├── sector: str
├── legal_form: str
├── email: str
├── url: str
├── phone_number: str
├── office_phone: str
├── fax: str
├── street: str
├── house_number: str
├── city: str
├── state: str
├── zip_code: str
├── country: str
└── country_code: str
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

#### CreditCard

```
CreditCard
├── card_type: str
├── card_number: str
├── card_provider: str
├── card_holder: str
├── expiration_date: datetime | str
├── cvv: str
├── cvc_number: str
├── is_active: bool
├── credit_limit: float
├── current_balance: float
├── issue_date: datetime | str
├── bank_name: str
├── bank_code: str
├── bic: str
├── bin: str
└── iban: str
```

#### Bank

```
Bank
├── name: str
├── swift_code: str
├── routing_number: str
├── bank_code: str
├── bic: str
├── bin: str
└── customer_service_phone: str
```

#### BankAccount

```
BankAccount
├── account_number: str
├── iban: str
├── account_type: str
├── balance: float
├── currency: str
├── created_date: datetime
├── last_transaction_date: datetime
├── bank_name: str
├── bank_code: str
├── bic: str
└── bin: str
```

#### Transaction

```
Transaction
├── transaction_id: str
├── account: BankAccount
├── transaction_date: datetime
├── amount: float
├── transaction_type: str
├── description: str
├── reference_number: str
├── status: str
├── currency: str
├── currency_symbol: str
├── merchant_name: str
├── merchant_category: str
├── location: str
├── is_international: bool
├── channel: str
└── direction: str
```

### Insurance Domain

Insurance-specific entities:

#### InsuranceCompany

```
InsuranceCompany
├── id: str
├── name: str
├── code: str
├── founded_year: str
├── headquarters: str
└── website: str
```

#### InsuranceProduct

```
InsuranceProduct
├── id: str
├── type: str
├── code: str
├── description: str
└── coverages: List[InsuranceCoverage]
```

#### InsuranceCoverage

```
InsuranceCoverage
├── name: str
├── code: str
├── product_code: str
├── description: str
├── min_coverage: str
└── max_coverage: str
```

#### InsurancePolicy

```
InsurancePolicy
├── id: str
├── company: InsuranceCompany
├── product: InsuranceProduct
├── policy_holder: Person
├── coverages: List[InsuranceCoverage]
├── premium: float
├── premium_frequency: str
├── start_date: date
├── end_date: date
├── status: str
└── created_date: datetime
```

### E-commerce Domain

Online retail entities:

#### Product

```
Product
├── product_id: str
├── name: str
├── description: str
├── price: float
├── category: str
├── brand: str
├── sku: str
├── condition: str
├── availability: str
├── currency: str
├── weight: float
├── dimensions: str
├── color: str
├── rating: float
└── tags: List[str]
```

#### Order

```
Order
├── order_id: str
├── user_id: str
├── product_list: List[Product]
├── total_amount: float
├── date: datetime
├── status: str
├── payment_method: str
├── shipping_method: str
├── shipping_address: Address
├── billing_address: Address
├── currency: str
├── tax_amount: float
├── shipping_amount: float
├── discount_amount: float
├── coupon_code: str
└── notes: str
```

### Public Sector Domain

Government and public administration entities:

#### AdministrationOffice

```
AdministrationOffice
├── office_id: str
├── name: str
├── type: str
├── address: Address
├── jurisdiction: str
├── founding_year: int
├── staff_count: int
├── annual_budget: float
├── hours_of_operation: dict
├── website: str
├── email: str
├── phone: str
├── services: List[str]
├── departments: List[str]
└── leadership: dict
```

#### EducationalInstitution

```
EducationalInstitution
├── institution_id: str
├── name: str
├── type: str
├── level: str
├── founding_year: int
├── student_count: int
├── staff_count: int
├── website: str
├── email: str
├── phone: str
├── programs: List[str]
├── accreditations: List[str]
├── facilities: List[str]
└── address: Address
```

#### PoliceOfficer

```
PoliceOfficer
├── officer_id: str
├── badge_number: str
├── given_name: str
├── family_name: str
├── full_name: str
├── gender: str
├── birthdate: str
├── age: int
├── rank: str
├── department: str
├── unit: str
├── hire_date: str
├── years_of_service: int
├── certifications: List[str]
├── languages: List[str]
├── shift: str
├── email: str
├── phone: str
└── address: Address
```

## Entity Relationships

Entities can be related to create complex, realistic data structures:

- A Person can have multiple BankAccounts
- A BankAccount can have multiple Transactions
- A CreditCard is linked to a BankAccount and Person
- An Order contains multiple Products and references shipping/billing Addresses
- An InsurancePolicy is linked to an InsuranceCompany, InsuranceProduct, and Person
- A Transaction references a BankAccount

These relationships maintain logical consistency, ensuring generated data reflects realistic scenarios. 