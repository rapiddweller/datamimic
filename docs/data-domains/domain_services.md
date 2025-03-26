# Using DATAMIMIC Domain Services

> **Note:** This documentation focuses specifically on the domain services within DATAMIMIC's Domain-Driven Framework component for generating synthetic data. DATAMIMIC has many additional capabilities beyond what is documented here.

## Installation

To start using DATAMIMIC, install it via pip:

```bash
pip install datamimic-ce
```

## Service Architecture

Each domain service in DATAMIMIC is built on the `BaseDomainService` class, which provides common functionality:

- **Entity Generation**: `generate()` and `generate_batch(count)` methods
- **Dataset Selection**: Support for country-specific data (e.g., `US`, `DE`)
- **Data Caching**: Efficient generation with property caching
- **Rich Domain Models**: Access to fully-populated domain entities

## Available Services

DATAMIMIC provides domain services across various industries:

### Common Services

```python
from datamimic_ce.domains.common.services.person_service import PersonService

# Generate a single person
person_service = PersonService()
person = person_service.generate()

# Access properties
print(f"Name: {person.name}")
print(f"Email: {person.email}")
print(f"Address: {person.address.street}, {person.address.city}")

# Generate multiple people
people = person_service.generate_batch(10)
for p in people:
    print(p.name)
```

### Healthcare Services

```python
from datamimic_ce.domains.healthcare.services.patient_service import PatientService

# Generate a patient with medical data
patient_service = PatientService()
patient = patient_service.generate()

# Access healthcare-specific properties
print(f"Patient ID: {patient.patient_id}")
print(f"Medical Record Number: {patient.medical_record_number}")
print(f"Blood Type: {patient.blood_type}")
print(f"Conditions: {', '.join(patient.conditions)}")
print(f"Medications: {', '.join(patient.medications)}")
```

### Financial Services

```python
from datamimic_ce.domains.financial.services.bank_account_service import BankAccountService

# Generate bank account data
account_service = BankAccountService()
account = account_service.generate()

# Access financial properties
print(f"Account Number: {account.account_number}")
print(f"Account Type: {account.account_type}")
print(f"Balance: ${account.balance:.2f}")
print(f"Transactions: {len(account.transactions)}")
```

## Using Country-Specific Data

Many DATAMIMIC services support country-specific datasets:

```python
# US-specific person data
us_person_service = PersonService(dataset="US")
us_person = us_person_service.generate()

# German-specific person data
de_person_service = PersonService(dataset="DE")
de_person = de_person_service.generate()

print(f"US Address: {us_person.address.street}, {us_person.address.postal_code}")
print(f"German Address: {de_person.address.street}, {de_person.address.postal_code}")
```

## Service Composition

DATAMIMIC services can be composed to create complex data scenarios:

```python
from datamimic_ce.domains.healthcare.services.patient_service import PatientService
from datamimic_ce.domains.healthcare.services.hospital_service import HospitalService

# Generate a hospital with patients
hospital_service = HospitalService()
hospital = hospital_service.generate()

patient_service = PatientService()
patients = patient_service.generate_batch(20)

# Associate patients with hospital
for patient in patients:
    print(f"Patient {patient.full_name} admitted to {hospital.name}")
    print(f"Department: {hospital.departments[0].name}")
```

## Best Practices

1. **Cache service instances** for better performance
2. **Use batch generation** when creating multiple entities
3. **Access entity properties** directly (they're cached automatically)
4. **Leverage domain-specific properties** for realistic scenarios
5. **Compose services** to create complex relationships 