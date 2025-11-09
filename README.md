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
![MCP Ready](https://img.shields.io/badge/MCP-ready-8A2BE2.svg)

---

## ✨ Why DATAMIMIC?

Typical data generators produce **isolated random values**. That’s fine for unit tests — but meaningless for system, analytics, or compliance testing.

```python
# Faker — broken relationships
patient_name = fake.name()
patient_age = fake.random_int(1, 99)
conditions   = [fake.word()]
# "25-year-old with Alzheimer's" — nonsense data
```

```python
# DATAMIMIC — contextual realism
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

### Deterministic Generation

DATAMIMIC produces the *same data for the same request*, across machines and CI runs. Seeds, clocks, and UUIDv5 namespaces enforce reproducibility.

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
# Same input → same output
```

**Determinism Contract**

* **Inputs:** `{seed, clock, uuidv5-namespace, request body}`
* **Guarantees:** byte-identical payloads + stable `determinism_proof.content_hash`
* **Scope:** all CE domains (see docs for domain-specific caveats)

---

## ⚡ MCP (Model Context Protocol)

Run DATAMIMIC as an MCP server so Claude / Cursor (and agents) can call deterministic data tools.

**Install**

```bash
pip install datamimic-ce[mcp]
# Development
pip install -e .[mcp]
```

**Run (SSE transport)**

```bash
export DATAMIMIC_MCP_HOST=127.0.0.1
export DATAMIMIC_MCP_PORT=8765
# Optional auth; clients must send the same token via Authorization: Bearer or X-API-Key
export DATAMIMIC_MCP_API_KEY=changeme
datamimic-mcp
```

**In-proc example (determinism proof)**

```python
import anyio, json
from fastmcp.client import Client
from datamimic_ce.mcp.models import GenerateArgs
from datamimic_ce.mcp.server import create_server

async def main():
    args = GenerateArgs(domain="person", locale="en_US", seed=42, count=2)
    payload = args.model_dump(mode="python")
    async with Client(create_server()) as c:
        a = await c.call_tool("generate", {"args": payload})
        b = await c.call_tool("generate", {"args": payload})
        print(json.loads(a[0].text)["determinism_proof"]["content_hash"]
              == json.loads(b[0].text)["determinism_proof"]["content_hash"])  # True
anyio.run(main)
```

**Config keys**

* `DATAMIMIC_MCP_HOST` (default `127.0.0.1`)
* `DATAMIMIC_MCP_PORT` (default `8765`)
* `DATAMIMIC_MCP_API_KEY` (unset = no auth)
* Requests over cap (`count > 10_000`) are rejected with `422`.

➡️ **Full guide, IDE configs (Claude/Cursor), transports, errors:** [`docs/mcp_quickstart.md`](docs/mcp_quickstart.md)

---

## 🧩 Domains & Examples

### 🏥 Healthcare

```python
from datamimic_ce.domains.healthcare.services import PatientService
patient = PatientService().generate()
print(patient.full_name, patient.conditions)
```

* Demographically realistic patients
* Doctor specialties match conditions
* Hospital capacities and types
* Longitudinal medical records

### 💰 Finance

```python
from datamimic_ce.domains.finance.services import BankAccountService
account = BankAccountService().generate()
print(account.account_number, account.balance)
```

* Balances respect transaction histories
* Card/IBAN formats per locale
* Distributions tuned for fraud/reconciliation tests

### 🌐 Demographics

* `PersonService` with locale packs (DE / US / VN), versioned and auditable

---

## 🔒 Deterministic by Design

* **Frozen clocks** + **canonical hashing** → reproducible IDs
* **Seeded RNG** → identical outputs across runs
* **Schema validation** (XSD/JSONSchema) → structural integrity
* **Provenance hashing** → audit-ready lineage

📘 See [Developer Guide](docs/developer_guide.md)

---

## 🧮 XML / Python Parity

Python:

```python
from random import Random
from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.healthcare.services import PatientService

cfg = DemographicConfig(age_min=70, age_max=75)
svc = PatientService(dataset="US", demographic_config=cfg, rng=Random(1337))
print(svc.generate().to_dict())
```

Equivalent XML:

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

## 🧰 CLI

```bash
# Run instant healthcare demo
datamimic demo create healthcare-example
datamimic run ./healthcare-example/datamimic.xml

# Verify version
datamimic version
```

**Quality gates (repo):**

```bash
make typecheck   # mypy --strict
make lint        # pylint (≥9.0 score target)
make coverage    # target ≥ 90%
```

---

## 🧭 Architecture Snapshot

* **Core pipeline:** Determinism kit • Domain services • Schema validators
* **Governance layer:** Group tables • Linkage audits • Provenance hashing
* **Execution layer:** CLI • API • XML runners • MCP server

---

## ⚖️ CE vs EE

| Feature                               | Community (CE) | Enterprise (EE) |
| ------------------------------------- | -------------- | --------------- |
| Deterministic domain generation       | ✅              | ✅               |
| XML + Python pipelines                | ✅              | ✅               |
| Healthcare & Finance domains          | ✅              | ✅               |
| Multi-user collaboration              | ❌              | ✅               |
| Governance & lineage dashboards       | ❌              | ✅               |
| ML engines (Mostly AI, Synthcity, …)  | ❌              | ✅               |
| RBAC & audit logging (HIPAA/GDPR/PCI) | ❌              | ✅               |
| EDIFACT / SWIFT adapters              | ❌              | ✅               |

👉 [Compare editions](https://datamimic.io) • [Book a strategy call](https://datamimic.io/contact)

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
