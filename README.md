# DATAMIMIC — Deterministic Synthetic Test Data That Makes Sense

**Generate realistic, interconnected, and reproducible test data for finance, healthcare, and beyond.**

Faker gives you *random* data.
**DATAMIMIC** gives you *consistent, explainable datasets* that respect business logic and domain constraints.

* 🧬 Patient medical histories that match age and demographics
* 💳 Bank transactions that obey balance constraints
* 🛡 Insurance policies aligned with real risk profiles

[![CI](https://img.shields.io/badge/CI-passing-brightgreen.svg)](https://github.com/rapiddweller/datamimic/actions)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=coverage)](https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic)
[![Maintainability](https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🧠 What Problem DATAMIMIC Solves

Typical data generators (like Faker) produce **isolated random values**.
That’s fine for unit tests — but meaningless for system, analytics, or compliance testing.

**Example:**

```python
# Faker – broken relationships
patient_name = fake.name()
patient_age = fake.random_int(1, 99)
conditions = [fake.word()]
# "25-year-old with Alzheimer's" – nonsense data.
```

**DATAMIMIC – contextual realism**

```python
from datamimic_ce.domains.healthcare.services import PatientService

patient = PatientService().generate()
print(f"{patient.full_name}, {patient.age}, {patient.conditions}")
# "Shirley Thompson, 72, ['Diabetes', 'Hypertension']"
```

---

## ⚙️ Quickstart (Community Edition)

Install and run:

```bash
pip install datamimic-ce
```

## Deterministic Data Generation

DATAMIMIC lets you generate the *same* data, every time across machines, environments, or CI pipelines.
Seeds, clocks, and UUIDv5 namespaces ensure your synthetic datasets remain reproducible and traceable, no matter where or when they’re generated.

```python
from datamimic_ce.domains.facade import generate_domain

request = {
    "domain": "person",
    "version": "v1",
    "count": 1,
    "seed": "docs-demo",                # identical seed → identical output
    "locale": "en_US",
    "clock": "2025-01-01T00:00:00Z"     # fixed clock = stable time context
}

response = generate_domain(request)
print(response["items"][0]["id"])
```

**Result:**
`Same input → same output.`

Behind the scenes, every deterministic request combines:

* A **stable seed** (for idempotent randomness),
* A **frozen clock** (for time-dependent values), and
* A **UUIDv5 namespace** (for globally consistent identifiers).

Together, they form a reproducibility contract. Ideal for CI/CD pipelines, agentic pipelines, and analytics verification.

Agents can safely re-invoke the same generation call and receive byte-for-byte identical data. 

---

## 🧩 Domains & Examples

### 🏥 Healthcare

```python
from datamimic_ce.domains.healthcare.services import PatientService
patient = PatientService().generate()
print(patient.full_name, patient.conditions)
```

* **PatientService** – Demographically realistic patients
* **DoctorService** – Specialties match conditions
* **HospitalService** – Realistic bed capacities and types
* **MedicalRecordService** – Longitudinal health records

### 💰 Finance

```python
from datamimic_ce.domains.finance.services import BankAccountService
account = BankAccountService().generate()
print(account.account_number, account.balance)
```

* Balances respect transactions
* Card/IBAN formats per locale
* Distributions tuned for fraud analytics and reconciliation

### 👤 Demographics

* `PersonService` – Culturally consistent names, addresses, phone patterns
* Locale packs for DE / US / VN, versioned and auditable

---

## 🔒 Deterministic by Design

* **Frozen clocks** and **canonical hashing** → reproducible IDs
* **Seeded random generators** → identical outputs across runs
* **Schema validation** (XSD, JSONSchema) → structural integrity
* **Provenance hashing** → audit-friendly lineage

📘 See [Developer Guide](docs/developer_guide.md)

---

## 🧮 XML / Python Model Workflow

Python-based generation:

```python
from random import Random
from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.healthcare.services import PatientService

cfg = DemographicConfig(age_min=70, age_max=75)
svc = PatientService(dataset="US", demographic_config=cfg, rng=Random(1337))
print(svc.generate().to_dict())
```

Equivalent XML model:

```xml
<setup>
  <generate name="seeded_seniors" count="3" target="CSV">
    <variable name="patient" entity="Patient" dataset="US" ageMin="70" ageMax="75" rngSeed="1337" />
    <key name="full_name" script="patient.full_name" />
    <key name="age" script="patient.age" />
    <array name="conditions" script="patient.conditions" />
  </generate>
</setup>
```

---

## ⚖️ CE vs EE Comparison

| Feature                                 | Community (CE) | Enterprise (EE) |
| --------------------------------------- | -------------- | --------------- |
| Deterministic domain generation         | ✅              | ✅               |
| XML + Python pipelines                  | ✅              | ✅               |
| Healthcare & Finance domains            | ✅              | ✅               |
| Multi-user collaboration                | ❌              | ✅               |
| Governance & lineage dashboards         | ❌              | ✅               |
| ML engines (Mostly AI, Gretel, Sklearn) | ❌              | ✅               |
| RBAC & audit logging (HIPAA/GDPR/PCI)   | ❌              | ✅               |
| Managed EDIFACT / SWIFT adapters        | ❌              | ✅               |

👉 [Compare editions](https://datamimic.io) • [Book a strategy call](https://datamimic.io/contact)

---

## 🧰 CLI & Automation

```bash
# Run instant healthcare demo
datamimic demo create healthcare-example
datamimic run ./healthcare-example/datamimic.xml

# Verify version
datamimic version
```

---

## 🧭 Architecture Snapshot

* **Core pipeline:** Determinism kit + domain services + schema validators
* **Governance layer:** Group tables, linkage audits, provenance hashing
* **Execution layer:** CLI, API, and XML runners

---

## 🌍 Industry Blueprints

### Finance

* Simulate SWIFT / ISO 20022 flows
* Replay hashed PCI transaction histories
* Validate fraud and reconciliation pipelines

### Healthcare

* Generate deterministic patient journeys
* Integrate HL7/FHIR/EDIFACT exchanges
* Reproduce QA datasets for regression testing

---

## 📚 Documentation & Community

* [📘 Full Documentation](https://docs.datamimic.io)
* [💬 GitHub Discussions](https://github.com/rapiddweller/datamimic/discussions)
* [🐛 Issue Tracker](https://github.com/rapiddweller/datamimic/issues)
* [📧 Email Support](mailto:support@rapiddweller.com)

---

## 🚀 Get Started

```bash
pip install datamimic-ce
```

**Generate data that makes sense — deterministically.**
⭐ Star us on GitHub if DATAMIMIC improves your testing workflow.
