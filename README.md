# DATAMIMIC - Generate Consistent Test Datasets

**The only tool that generates realistic, interconnected test data that actually makes sense together.**

Faker gives you random data. DATAMIMIC gives you realistic datasets where:
- Patient medical conditions match their age and demographics
- Bank account transactions respect balance constraints
- Insurance policies align with patient risk profiles

[![Maintainability](https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=coverage)](https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-≥3.10-blue.svg)](https://www.python.org/downloads/)

```bash
pip install datamimic-ce
```

## The Problem with Random Test Data

**Faker Example** (broken relationships):
```python
# This creates nonsensical data
patient_name = fake.name()           # "John Smith"
patient_age = fake.random_int(1, 99) # 25
conditions = [fake.word()]           # ["Alzheimer's"]
```
*Result: 25-year-old with Alzheimer's? Your tests miss real edge cases.*

**DATAMIMIC Example** (realistic relationships):
```python
from datamimic_ce.domains.healthcare.services import PatientService

patient_service = PatientService()
patient = patient_service.generate()

print(f"Patient: {patient.full_name}, Age: {patient.age}")
print(f"Conditions: {patient.conditions}")
# Result: 72-year-old with ["Diabetes", "Hypertension", "Arthritis"]
```

## When You Need DATAMIMIC

✅ **Healthcare systems** - Medical records with age-appropriate conditions  
✅ **Financial applications** - Bank accounts with realistic transaction patterns  
✅ **Insurance platforms** - Policies that match patient risk profiles  
✅ **Multi-table databases** - Foreign keys and relationships that actually work  
✅ **Integration testing** - Complete business scenarios, not isolated records  

## Quick Start

### 1. Installation

```bash
pip install datamimic-ce
```

Verify installation:
```bash
datamimic version
```

### 2. Healthcare Data Generation

```python
from datamimic_ce.domains.healthcare.services import PatientService

# Generate realistic patient data
patient_service = PatientService()
patient = patient_service.generate()

# Access patient attributes
print(f"Patient ID: {patient.patient_id}")
print(f"Name: {patient.full_name}")
print(f"Age: {patient.age}")
print(f"Medical Conditions: {patient.conditions}")
print(f"Blood Type: {patient.blood_type}")
```

### Demographics & Seeding (First Example)

Python (DemographicConfig + seeded RNG):
```python
from random import Random
from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.healthcare.services import PatientService

cfg = DemographicConfig(age_min=70, age_max=75)
svc = PatientService(dataset="US", demographic_config=cfg, rng=Random(1337))
patient = svc.generate()
print({"name": patient.full_name, "age": patient.age, "conditions": patient.conditions})
```

XML (Demographic attributes + rngSeed):
```xml
<setup>
  <generate name="seeded_seniors" count="3" target="CSV">
    <variable name="patient" entity="Patient" dataset="US" ageMin="70" ageMax="75" rngSeed="1337" />
    <key name="full_name" script="patient.full_name" />
    <key name="age" script="patient.age" />
    <array name="conditions" script="patient.conditions" />
  </generate>
  <!-- array is for primitives; use nestedKey for lists of dicts -->
  <!-- <nestedKey name="records" script="some_list_of_dicts" /> -->
  
</setup>
```

**Example Output:**
```
Patient ID: PAT-23AEEABA
Name: Shirley Thompson
Age: 65
Medical Conditions: ['Depression']
Blood Type: AB-
```

### 3. Financial Services Data

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

### 4. Complex Healthcare Scenarios

```python
from datamimic_ce.domains.healthcare.services import (
    PatientService, DoctorService, HospitalService
)

# Generate complete healthcare ecosystem
hospital_service = HospitalService()
doctor_service = DoctorService()
patient_service = PatientService()

# Create related entities
hospital = hospital_service.generate()
doctors = doctor_service.generate_batch(count=3)
patients = patient_service.generate_batch(count=10)

print(f"Hospital: {hospital.name} ({hospital.hospital_type})")
print(f"Capacity: {hospital.beds} beds")

print("\nMedical Staff:")
for doctor in doctors:
    print(f"- Dr. {doctor.full_name}, {doctor.specialty}")
    print(f"  Experience: {doctor.years_of_experience} years")

print(f"\nPatients: {len(patients)} total")
```

**Example Output:**
```
Hospital: Cornell Healthcare (Community Hospital)
Capacity: 349 beds

Medical Staff:
- Dr. Teresa Gross, Obstetrics and Gynecology
  Experience: 4 years
- Dr. Isaac Kerr, Family Medicine
  Experience: 12 years

Patients: 10 total
```

## Advanced Use Cases

### Target Specific Patient Demographics

```python
# Generate elderly patients with diabetes
elderly_diabetic_patients = []
all_patients = patient_service.generate_batch(count=100)

for patient in all_patients:
    if patient.age >= 65 and "Diabetes" in patient.conditions:
        elderly_diabetic_patients.append(patient)

print(f"Found {len(elderly_diabetic_patients)} elderly diabetic patients")
for patient in elderly_diabetic_patients[:3]:
    print(f"- {patient.full_name}, {patient.age} years old")
    print(f"  Conditions: {patient.conditions}")
```

### XML-Based Data Generation

```xml
<setup>
    <generate name="customer" count="10">
        <!-- Prefer attributes over constructor strings; deterministic when rngSeed is set -->
        <variable name="person" entity="Person" ageMin="21" ageMax="67" rngSeed="42"/>
        <key name="id" generator="IncrementGenerator"/>
        <key name="first_name" script="person.given_name"/>
        <key name="last_name" script="person.family_name"/>
        <key name="email" script="person.email"/>
        <key name="status" values="'active', 'inactive', 'pending'"/>
    </generate>
</setup>
```

Use in tests:
```python
from datamimic_ce.factory.datamimic_test_factory import DataMimicTestFactory

customer_factory = DataMimicTestFactory("customer.xml", "customer")
customer = customer_factory.create()

print(customer["id"])         # 1
print(customer["first_name"]) # Jose
print(customer["email"])      # jose.ayers@example.com
```

### Export to CSV

```python
import csv

# Generate and export patient data
patients = patient_service.generate_batch(count=50)

with open('patients.csv', 'w', newline='') as csvfile:
    fieldnames = ['patient_id', 'name', 'age', 'gender', 'conditions']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    writer.writeheader()
    for patient in patients:
        writer.writerow({
            'patient_id': patient.patient_id,
            'name': patient.full_name,
            'age': patient.age,
            'gender': patient.gender,
            'conditions': ', '.join(patient.conditions)
        })
```

## Why Not Just Use Faker?

| Scenario | Faker Result | DATAMIMIC Result |
|----------|-------------|------------------|
| Patient Data | 25-year-old with Alzheimer's | 72-year-old with age-appropriate conditions |
| Bank Account | $50M balance with $2 transaction | Balance reflects realistic transaction history |
| Medical Records | Random doctor + random patient | Doctor specialty matches patient conditions |
| Insurance | Any policy for any patient | Coverage appropriate for patient risk profile |

**Faker creates individual random values. DATAMIMIC creates realistic business scenarios.**

## CLI and Batch Processing

```bash
# Run instant healthcare demo
datamimic demo create healthcare-example
datamimic run ./healthcare-example/datamimic.xml

# Verify installation
datamimic version
```

## Available Domains

**🏥 Healthcare**
- `PatientService` - Realistic patient demographics and conditions
- `DoctorService` - Medical professionals with appropriate specialties
- `HospitalService` - Healthcare facilities with realistic capacity
- `MedicalRecordService` - Patient records with consistent history

**💰 Financial Services**  
- `BankAccountService` - Accounts with realistic transaction patterns
- Transaction history that respects balance constraints
- Account types aligned with customer demographics

**👤 General Demographics**
- `PersonService` - Culturally consistent names and locations
- Geographic and demographic correlations

## Enterprise vs Community

| Feature                        | Community | Enterprise |
|--------------------------------|-----------|------------|
| Domain-specific data generation | ✅        | ✅         |
| Python & XML APIs              | ✅        | ✅         |
| Healthcare, Financial domains   | ✅        | ✅         |
| ML-Enhanced Data Generation     | ❌        | ✅         |
| Advanced Enterprise Integrations | ❌      | ✅         |
| Web UI & Team Collaboration    | ❌        | ✅         |
| Priority Support & SLA         | ❌        | ✅         |

👉 [Learn more about Enterprise Edition](https://datamimic.io)  
📞 [Book a Free Strategy Call](https://datamimic.io/contact)

## Documentation & Resources

📚 **[Full Documentation](https://docs.datamimic.io)**

📘 **Additional Resources:**
- [CLI Interface](docs/api/cli.md)
- [Data Domains Details](docs/data-domains/README.md)

🚀 **Try the healthcare demo:**
```bash
datamimic demo create healthcare-example
datamimic run ./healthcare-example/datamimic.xml
```

## FAQ

**Q:** Is Community Edition suitable for commercial projects?

**A:** Absolutely! DATAMIMIC CE uses the MIT License.

**Q:** How is this different from Faker?

**A:** Faker generates random individual values. DATAMIMIC generates domain-specific datasets where related fields follow real-world business rules and correlations.

**Q:** What domains are supported?

**A:** Currently healthcare, financial services, and general demographics. More domains are added regularly.

**Q:** Can I contribute?

**A:** Yes! See [Contributing Guide](CONTRIBUTING.md).

## Support & Community

💬 **[GitHub Discussions](https://github.com/rapiddweller/datamimic/discussions)**  
🐛 **[Issue Tracker](https://github.com/rapiddweller/datamimic/issues)**  
📧 **[Email Support](mailto:support@rapiddweller.com)**

## Stay Connected

🌐 **[Website](https://datamimic.io)**  
💼 **[LinkedIn](https://www.linkedin.com/company/rapiddweller)**

---

**Ready to generate data that makes sense?**

```bash
pip install datamimic-ce
```

⭐ **Star us on GitHub** if DATAMIMIC solves your test data problems!
