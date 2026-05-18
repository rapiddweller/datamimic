# DATAMIMIC — Governed Test Data for Regulated Enterprises

> **This repository contains the DATAMIMIC Community Edition (CE)** — the open-source deterministic data engine at the core of the **DATAMIMIC Enterprise Platform**.
>
> CE is fully usable standalone for deterministic synthetic data generation and PII-aware pseudonymization. The Enterprise Platform builds on a separately optimised EE core and adds governed workflows, PII scanning, role-based access, audit logging, scheduling, multi-system execution, and the full operational layer that regulated enterprises require.
>
> 👉 **Enterprise Platform:** [datamimic.io](https://datamimic.io) &nbsp;|&nbsp; 📘 **Docs:** [docs.datamimic.io](https://docs.datamimic.io) &nbsp;|&nbsp; 📅 **Book a strategy call:** [datamimic.io/contact](https://datamimic.io/contact)

---

[![CI](https://img.shields.io/badge/CI-passing-brightgreen.svg)](https://github.com/rapiddweller/datamimic/actions)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=coverage)](https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic)
[![Maintainability](https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP Ready](https://img.shields.io/badge/MCP-ready-8A2BE2.svg)](docs/mcp_quickstart.md)

---

## What is DATAMIMIC?

**DATAMIMIC is the enterprise standard for governed test data operations.**

Enterprises in banking, insurance, and regulated industries use DATAMIMIC to:

- **Scan** source systems for PII — probability-scored field detection with configurable thresholds *(EE: automated via DataWorkbench; CE: manual model definition)*
- **Generate** fully synthetic, deterministic datasets — model-driven, zero production data
- **Pseudonymize** source data — deterministic (seeded) or privacy-maximized (non-seeded) field transformation from source to target system
- **Execute** repeatable workflows: single-system pipelines in CE; multi-system landscapes (Oracle, PostgreSQL, MongoDB, Kafka, JSON, XML, CSV) in EE
- **Produce audit evidence** — append-only execution logs and provenance hashing on every output; role-based dashboards in EE
- **Govern** test data demand through reusable templates, approval flows, and self-service execution *(EE)*

> Deployed in regulated EU banking environments for deterministic test data across Oracle, MongoDB, and Kafka pipelines.

---

## CE vs Enterprise Platform

CE and EE are **not the same engine with a feature flag**. The EE core is an independently optimised execution engine built for enterprise-scale throughput and operational control.

### Engine comparison

| Capability | Community Edition (CE) | Enterprise Platform (EE) |
|---|---|---|
| Deterministic data generation | ✅ | ✅ |
| **Pseudonymization — seeded (GDPR Art. 25)** | ✅ manual model | ✅ automated via DataWorkbench |
| **Pseudonymization — non-seeded (privacy-maximized)** | ✅ manual model | ✅ automated via DataWorkbench |
| Python API + XML pipelines | ✅ | ✅ |
| Domain models: Finance, Healthcare, Demographics | ✅ | ✅ |
| MCP server for AI agent integration | ✅ | ✅ |
| CLI + local execution | ✅ | ✅ |
| **Scale** | millions of records | **designed for billion-record workloads** via isolated multiprocessing and Ray-based distributed execution |
| **PII scanner** | ❌ | ✅ probability-scored field detection, configurable threshold, DataWorkbench integration |
| **Runtime configuration profiles** | ❌ | ✅ Performance · Balanced · Flexibility |
| **Memory management** | standard | optimised for high-volume batch and streaming |
| **Logging granularity** | flat execution log | configurable: minimal · standard · deep nested tracing |
| **Nested structure evaluation** | basic | deep nested generation with extended condition + ruleset evaluation |
| **Importer / exporter logging** | ❌ | per-stage logging for importers and exporters |
| **Error handling** | standard exceptions | structured error catalog with recovery strategies |
| **ML engine integration** | ❌ | combine statistical models with conditions, rulesets, validators |

### Platform capabilities (EE only)

| Capability | EE |
|---|---|
| Multi-user collaboration | ✅ |
| Role-based access control (RBAC) | ✅ |
| Audit logs + provenance dashboards | ✅ |
| **PII scanner — probability scoring, threshold-based field flagging** | ✅ |
| **DataWorkbench — visual field mapping and pseudonymization model builder** | ✅ |
| Reusable enterprise template library | ✅ |
| Scheduled execution + task runner | ✅ |
| CI/CD pipeline integration (Tosca, Jenkins, GitLab) | ✅ |
| Multi-system execution: Oracle, MongoDB, Kafka | ✅ |
| **Template engine: EDIFACT, SWIFT MT, HL7 + spec-specific editors** | ✅ |
| Audit evidence support for GDPR / HIPAA / PCI assessments | ✅ |
| On-premise deployment + air-gapped environments | ✅ |
| LSP-powered IDE tooling for DSL authoring | ✅ |

👉 [Compare editions in detail](https://datamimic.io) &nbsp;|&nbsp; [Book a platform demo](https://datamimic.io/contact)

---

## EE runtime profiles

The EE core supports three runtime configuration profiles, selectable per execution context:

| Profile | Optimises for | Typical use case |
|---|---|---|
| **Performance** | Maximum throughput via isolated multiprocessing + Ray-based distributed execution | Bulk generation at nine-figure record volumes to PostgreSQL, Oracle, Kafka |
| **Balanced** | Throughput + full audit logging | Standard enterprise pipeline runs with compliance requirements |
| **Flexibility** | Deep nested evaluation, extended condition and ruleset processing | Complex domain models with ML engine combinations, multi-level referential structures |

Logging depth is independently configurable per profile — from minimal (throughput-optimised) to full nested tracing across importers, exporters, and generation stages.

---

## EE template engine

The EE template engine generates industry-standard financial and healthcare message formats from DATAMIMIC models, with spec-specific editors for each format:

| Format | Standard | Spec-specific editor |
|---|---|---|
| EDIFACT | UN/EDIFACT | ✅ |
| SWIFT MT | SWIFT MT | ✅ |
| HL7 | HL7 v2.x | ✅ |

Templates are versioned, reusable across scenarios, and fully integrated with the DATAMIMIC DSL and audit layer. Generated messages are deterministic and traceable to their source model.

---

## Who is DATAMIMIC for?

### Enterprise Platform (EE)
| Role | What DATAMIMIC solves |
|---|---|
| **QA / Test Manager** | Eliminate manual test data requests. Self-service, governed, always ready. |
| **Business Analyst** | Define data requirements in business-readable models — no scripting needed. |
| **Platform / DevOps Engineer** | Integrate deterministic test data generation into CI/CD and scheduled pipelines. |
| **Compliance / Audit** | Full audit trail for every generation run. Regulator-ready logs, no production data exposure. |
| **Enterprise Architect** | One governed standard across Oracle, MongoDB, Kafka, flat files, and custom systems. |

### Community Edition (CE)
Developers and data engineers who need deterministic synthetic data generation or PII-aware pseudonymization in local environments, CI pipelines, or agent-driven workflows. PII field identification is manual — the EE DataWorkbench automates this step.

---

## Why deterministic generation matters

Most test data tools produce random output. That breaks regression tests, audit trails, and cross-team reproducibility.

**DATAMIMIC's determinism contract:**

- Same seed + same model = byte-identical output, every run, every machine
- Frozen clocks + canonical hashing = stable temporal context
- UUIDv5 namespaces = reproducible entity identifiers
- Provenance hash on every output = audit-ready lineage

```python
from datamimic_ce.domains.facade import generate_domain

request = {
    "domain": "person",
    "version": "v1",
    "count": 1,
    "seed": "regression-suite-42",       # identical seed → identical output
    "locale": "en_US",
    "clock": "2025-01-01T00:00:00Z"      # fixed clock = stable time context
}

response = generate_domain(request)
# Same input → same output, always, everywhere
```

---

## Why DATAMIMIC beats Faker and generic generators

| | Faker / Random generators | DATAMIMIC CE | DATAMIMIC EE |
|---|---|---|---|
| Reproducible output | ❌ | ✅ | ✅ |
| Domain-aware relationships | ❌ | ✅ | ✅ |
| Business logic constraints | ❌ | ✅ | ✅ |
| Audit-ready provenance | ❌ | ✅ | ✅ |
| Source data pseudonymization | ❌ | ✅ manual | ✅ automated |
| PII field detection | ❌ | ❌ | ✅ probability-scored |
| Enterprise governance layer | ❌ | ❌ | ✅ |
| Multi-system execution | ❌ | ❌ | ✅ |
| Role-based workflows | ❌ | ❌ | ✅ |
| Regulated industry compliance | ❌ | ❌ | ✅ |

```python
# Faker — broken relationships
from faker import Faker
fake = Faker()
patient_age = fake.random_int(1, 99)
conditions  = [fake.word()]
# "25-year-old with Alzheimer's" — meaningless for any real test

# DATAMIMIC — domain-aware, deterministic
from datamimic_ce.domains.healthcare.services import PatientService
patient = PatientService().generate()
print(f"{patient.full_name}, {patient.age}, {patient.conditions}")
# "Shirley Thompson, 72, ['Diabetes', 'Hypertension']" — every time
```

---

## Quickstart — Community Edition

```bash
pip install datamimic-ce
```

### Healthcare domain

```python
from datamimic_ce.domains.healthcare.services import PatientService

patient = PatientService().generate()
print(patient.full_name, patient.age, patient.conditions)
# Age-appropriate conditions, demographically realistic, deterministic
```

### Finance domain

```python
from datamimic_ce.domains.finance.services import BankAccountService

account = BankAccountService().generate()
print(account.account_number, account.balance)
# Balance-consistent, locale-correct, reproducible
```

### Pseudonymization — CE (manual model)

DATAMIMIC supports two pseudonymization modes with different privacy postures:

| Mode | How | Legal classification | Use case |
|---|---|---|---|
| **Seeded** (`rngSeed` set) | Deterministic, reproducible | Pseudonymization — GDPR Art. 25 | Regression testing, stable CI/CD pipelines |
| **Non-seeded** (no `rngSeed`) | Non-deterministic, no reversible mapping at field level | Privacy-maximized transformation | One-time data delivery, higher privacy posture |

> **Note on GDPR anonymization:** Full anonymization status under GDPR depends on complete field coverage across all quasi-identifiers and a re-identification risk assessment on the complete record — not on individual field transformation alone. DATAMIMIC does not make anonymization claims on behalf of the customer. Non-seeded mode maximizes privacy at the transformation level; the customer is responsible for assessing re-identification risk across the full dataset.

In CE, PII fields are identified and modeled manually in the XML pipeline:

```xml
<setup>
  <generate name="customers" source="customer_export" target="customer_test">
    <key name="first_name"  converter="Mask" />
    <key name="email"       converter="anonymize_email" />
    <key name="iban"        converter="generate_iban" dataset="DE" rngSeed="42" />
    <key name="birth_date"  converter="shift_date" shiftDays="90" />
  </generate>
</setup>
```

```bash
datamimic run ./pseudonymize-customers/datamimic.xml
```

`source` is a controlled export or staging input — never a live production connection.

With `rngSeed` set: same source record → same pseudonymized output on every run. Stable for regression testing.

Without `rngSeed`: non-deterministic output — no reversible mapping exists at the field level. Stronger privacy posture for one-time delivery scenarios.

> **In the Enterprise Platform (EE):** the DataWorkbench PII scanner automatically scans source schemas, assigns probability scores to each field, and flags candidates above a configurable threshold. Flagged fields are wired into the pseudonymization model automatically — no manual field mapping required.



```xml
<setup>
  <generate name="patients" count="1000" target="CSV">
    <variable name="patient" entity="Patient" dataset="US" ageMin="60" ageMax="80" rngSeed="42" />
    <key name="full_name"   script="patient.full_name" />
    <key name="age"         script="patient.age" />
    <array name="conditions" script="patient.conditions" />
  </generate>
</setup>
```

```bash
datamimic run ./patient-scenario/datamimic.xml
```

---

## MCP Server — AI Agent Integration

DATAMIMIC CE ships with a Model Context Protocol (MCP) server, making it directly callable from AI agents, Claude, Cursor, and any MCP-compatible runtime.

```bash
pip install datamimic-ce[mcp]

export DATAMIMIC_MCP_HOST=127.0.0.1
export DATAMIMIC_MCP_PORT=8765
export DATAMIMIC_MCP_API_KEY=your-key
datamimic-mcp
```

Agents can call `generate` with a domain, seed, count, and locale and receive deterministic, provenance-hashed output — making DATAMIMIC the natural test data runtime for agent-driven workflows.

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
        # Determinism proof: identical hashes across calls
        assert (json.loads(a[0].text)["determinism_proof"]["content_hash"]
             == json.loads(b[0].text)["determinism_proof"]["content_hash"])

anyio.run(main)
```

📘 Full guide: [`docs/mcp_quickstart.md`](docs/mcp_quickstart.md)

---

## Where CE fits on its own

Most teams adopt CE for one of three reasons. EE is not required for any of them.

**1. Reproducible test data for CI/CD pipelines.** Same seed → byte-identical output across machines. Regression tests stop being flaky because the input data is stable across runs.

```python
from datamimic_ce.domains.healthcare.services import PatientService

# This call returns the exact same patient on every machine, every run.
patient = PatientService().generate(seed="ci-pipeline-42", locale="en_US")
```

**2. Deterministic data backend for AI agents and LLM tooling.** The bundled MCP server (`pip install datamimic-ce[mcp]`) exposes `generate` as an MCP tool. Agents call it with seed, locale, count; outputs ship with a `determinism_proof.content_hash` for verification — exactly the kind of evidence EU AI Act Art. 10 (data governance) and Art. 50 (transparency) audits want to see.

**3. Pseudonymization of staging and QA exports.** Manual model in CE (XML pipeline), no scanner license required. Seeded mode for stable regression test data; non-seeded mode for one-time deliveries with maximized privacy posture. See the [Pseudonymization section above](#pseudonymization--ce-manual-model).

---

## Where DATAMIMIC fits in your compliance program

DATAMIMIC produces evidence and reproducible artifacts that support compliance work. It does not replace your DPO, your CISO, or your auditor. The following are pointers for where DATAMIMIC outputs commonly slot into established programs:

| Regulation / standard | Where DATAMIMIC contributes |
|---|---|
| **EU AI Act (Reg. 2024/1689)** — Art. 10 (data governance), Art. 50 (transparency) | Provenance-hashed synthetic datasets for training/test data with reproducible lineage; deterministic outputs that audit reviewers can re-execute |
| **DORA (Reg. 2022/2554)** — Art. 24–27 (resilience testing), Art. 8 (asset register) | Reproducible test datasets for resilience testing programs; deterministic data fixtures for ICT system inventories |
| **ISO/IEC 27701:2025** — A.1.4 (privacy by design), A.1.2.9 (RoPA) | Synthetic data in lieu of PII in non-production environments; documented model definitions as privacy-by-design evidence |
| **HIPAA Security Rule** — §164.312 technical safeguards | Synthetic Patient/MedicalDevice/MedicalProcedure data for dev and test environments without ePHI exposure |
| **GDPR Art. 25** (data protection by design) | Seeded pseudonymization with deterministic mapping; non-seeded mode for stronger privacy posture |

> These pointers do not constitute legal advice or a compliance attestation. Consult your DPO, CISO, or qualified counsel for formal compliance determinations. Full anonymization status under GDPR depends on re-identification risk across the complete dataset — see the [pseudonymization disclaimer above](#pseudonymization--ce-manual-model).

---

## Architecture

CE and EE have **separate, independently maintained cores**. CE is not a stripped-down EE. EE is not CE with features unlocked. They share the same DSL and determinism contract but diverge completely at the execution layer.

```
╔══════════════════════════════════════════════════════════════════╗
║              DATAMIMIC ENTERPRISE PLATFORM (EE)                  ║
║                                                                  ║
║  ┌──────────────────────────────────────────────────────────┐    ║
║  │  PLATFORM LAYER                                          │    ║
║  │  UI · RBAC · Governance · Audit Dashboards               │    ║
║  │  DataWorkbench · PII Scanner · Pseudonymization Builder  │    ║
║  │  Scheduler · Task Runner · CI/CD · Template Engine       │    ║
║  └──────────────────────────────────────────────────────────┘    ║
║                                                                  ║
║  ┌──────────────────────────────────────────────────────────┐    ║
║  │  EE CORE  (optimised, separate from CE)                  │    ║
║  │                                                          │    ║
║  │  Ray-based distributed execution                         │    ║
║  │  Isolated multiprocessing · Linear scalability           │    ║
║  │  Runtime profiles: Performance · Balanced · Flexibility  │    ║
║  │  Deep nested evaluation · Conditions · Rulesets          │    ║
║  │  ML engine integration · Structured error catalog        │    ║
║  │  Per-stage importer/exporter logging                     │    ║
║  └──────────────────────────────────────────────────────────┘    ║
╚══════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════╗
║              DATAMIMIC COMMUNITY EDITION (CE)  — this repo       ║
║                                                                  ║
║  Determinism Kit · Domain Services · Schema Validators           ║
║  Synthetic Generation · Pseudonymization (manual model)          ║
║  Python API · XML Pipelines · CLI · MCP Server                   ║
╚══════════════════════════════════════════════════════════════════╝

         ↓              ↓              ↓              ↓
    PostgreSQL       Oracle         MongoDB      Kafka / Files
```

Both editions share the same DATAMIMIC DSL and determinism contract. Scale, throughput, governance, and operational control are EE-only.

---

## Supported systems

| System | CE | EE | Notes |
|---|---|---|---|
| PostgreSQL | ✅ | ✅ | EE adds schema introspection and referential integrity |
| MySQL | ✅ | ✅ | |
| Oracle | ✅ | ✅ | EE production-validated in regulated banking environments |
| MS SQL Server | ✅ | ✅ | |
| SQLite | ✅ | ✅ | Lightweight CI/CD fixtures |
| MongoDB | ✅ | ✅ | EE adds nested document generation |
| CSV / JSON / XML | ✅ | ✅ | Flat file pipelines |
| Apache Kafka | — | ✅ | Real-time streaming, payment scenarios |
| EDIFACT / SWIFT MT | — | ✅ | Test/training output only; does not satisfy SWIFT CSP production-environment controls (1.1, 1.4) |

---

## CE domains

| Domain | Services available |
|---|---|
| **Healthcare** | Patient, Doctor, Hospital, MedicalDevice, MedicalProcedure |
| **Finance** | Bank, BankAccount, CreditCard, Transaction |
| **Insurance** | InsuranceCompany, InsuranceProduct, InsurancePolicy, InsuranceCoverage |
| **E-commerce** | Order, Product |
| **Public sector** | AdministrationOffice, EducationalInstitution, PoliceOfficer |
| **Demographics** | Person (DE / US / VN locale packs), Address, Company |

All services are versioned, seeded, and audit-ready. Each service exposes the same deterministic API: `Service().generate(seed=…, locale=…, count=…)`.

---

## CLI reference

```bash
# Initialize a new project
datamimic init ./my-scenario

# Validate an XML descriptor without executing it
datamimic validate ./my-scenario/datamimic.xml

# Run a scenario
datamimic run ./my-scenario/datamimic.xml

# Demos
datamimic demo list
datamimic demo create healthcare-example
datamimic demo create --all --target ./my_demos

# System and version info
datamimic info
datamimic version
```

---

## Documentation

| Resource | Link |
|---|---|
| Full documentation | [docs.datamimic.io](https://docs.datamimic.io) |
| MCP quickstart | [docs/mcp_quickstart.md](docs/mcp_quickstart.md) |
| Developer guide | [docs/developer_guide.md](docs/developer_guide.md) |
| Enterprise platform | [datamimic.io](https://datamimic.io) |
| GitHub Discussions | [Discussions](https://github.com/rapiddweller/datamimic/discussions) |
| Issue tracker | [Issues](https://github.com/rapiddweller/datamimic/issues) |
| Email support | support@rapiddweller.com |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). CE is MIT licensed and community contributions are welcome.

The CE engine is the foundation. If you are building integrations, domain extensions, or MCP tooling on top of DATAMIMIC, we want to hear from you.

---

## License

MIT — see [LICENSE](LICENSE).

The DATAMIMIC Enterprise Platform (EE) is a commercial product. [Contact us](https://datamimic.io/contact) for licensing.

---

**DATAMIMIC — Make test data a standard, not a manual process.**

[datamimic.io](https://datamimic.io) &nbsp;|&nbsp; [Book a demo](https://datamimic.io/contact) &nbsp;|&nbsp; [LinkedIn](https://linkedin.com/company/rapiddweller)
