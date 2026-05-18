# DATAMIMIC — Governed Test Data for Regulated Enterprises

> **This repository contains the DATAMIMIC Community Edition (CE).** MIT-licensed, Python-native, MCP-ready.
>
> CE is fully usable standalone for deterministic synthetic data generation and PII-aware pseudonymization. The Enterprise Platform adds governed workflows, PII scanning, role-based access, audit logging, scheduling, multi-system execution, and the full operational layer that regulated enterprises require.
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

**DATAMIMIC CE is the open-source deterministic data engine at the core of the DATAMIMIC Enterprise Platform.** It is usable standalone for synthetic data generation and PII-aware pseudonymization in any local, CI, or agent-driven workflow.

The Enterprise Platform adds the governed workflows, scanners, dashboards, and execution layer that regulated enterprises require for production-scale test-data operations.

**Available in CE (this repo):**

- **Generate** fully synthetic, deterministic datasets — model-driven, no source data required
- **Pseudonymize** staging/QA exports — deterministic (seeded) or privacy-maximized (non-seeded) field transformation; PII fields identified and modeled manually in the XML pipeline
- **Execute** single-system pipelines against PostgreSQL · MySQL · Oracle · MS SQL · SQLite · MongoDB · CSV · JSON · XML
- **Emit provenance** — append-only execution logs and per-output content hash for audit re-execution
- **Serve agents** — bundled MCP server exposing `generate` as a deterministic tool for AI/LLM tooling

**The Enterprise Platform adds:**

- **PII scanner** — probability-scored field detection with configurable thresholds via DataWorkbench
- **Multi-system execution** — Oracle / MongoDB / Kafka / EDIFACT / SWIFT MT / HL7 v2.x / HL7 FHIR in coordinated workflows with referential integrity
- **Governance layer** — role-based dashboards, audit trails, approval flows, reusable enterprise templates, scheduler
- **Performance core** — Rust fastpath, ML/auto-regressive engine for complex distributions, keyset and manifest building, optimised distributed execution
- **On-premise / air-gapped deployment** — podman-compose or Helm, with consulting-led rollout

> Deployed in a regulated EU banking engagement for deterministic test data across Oracle, MongoDB, and Kafka pipelines (see [datamimic.io case studies](https://datamimic.io)).

---

## CE vs Enterprise Platform

CE and EE are **not the same engine with a feature flag**. They share the DSL and determinism contract, but EE is an independently optimised execution engine built for enterprise-scale throughput and operational control.

### Engine comparison

| Capability | Community Edition (CE) | Enterprise Platform (EE) |
|---|---|---|
| Deterministic data generation | ✅ | ✅ |
| **Pseudonymization — seeded** *(GDPR Art. 4(5); supports Art. 25 / Art. 32)* | ✅ manual model | ✅ automated via DataWorkbench |
| **Pseudonymization — non-seeded (privacy-maximized)** | ✅ manual model | ✅ automated via DataWorkbench |
| Python API + XML pipelines | ✅ | ✅ |
| Domain models: Finance, Healthcare, Demographics | ✅ | ✅ |
| MCP server for AI agent integration | ✅ | ✅ |
| CLI + local execution | ✅ | ✅ |
| **Scale** | millions of records via Python multiprocessing (and optional Ray) | **designed for billion-record workloads** — Rust fastpath, optimised multi-process execution, and keyset/manifest building on top of the shared Ray distribution layer |
| **PII scanner** | ❌ | ✅ probability-scored field detection, configurable threshold, DataWorkbench integration |
| **Runtime configuration profiles** | ❌ | ✅ Performance · Balanced · Flexibility |
| **Memory management** | standard | optimised for high-volume batch and streaming |
| **Logging granularity** | flat execution log | configurable: minimal · standard · deep nested tracing |
| **Nested structure evaluation** | basic | deep nested generation with extended condition + ruleset evaluation |
| **Importer / exporter logging** | ❌ | per-stage logging for importers and exporters |
| **Error handling** | standard exceptions | structured error catalog with recovery strategies |
| **Rust fastpath** | ❌ | performance-critical paths in Rust |
| **Keyset and manifest building** | ❌ | reads live DB schemas to build coordinated multi-table generation plans |
| **ML / auto-regressive engine** | ❌ | combine statistical models with conditions, rulesets, validators for complex distributions |

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
| **Template engine: schema-aware editors for EDIFACT, SWIFT MT, HL7 v2.x, and HL7 FHIR — customer-uploadable specs, further industry formats deliverable in days on the same framework** | ✅ |
| Audit-evidence artefacts for GDPR Art. 30 records, PCI DSS 4.0 Req. 6.5.5 (test data) reviews, and — for US Covered Entities / Business Associates — HIPAA §164.312 evidence packs | ✅ |
| On-premise deployment + air-gapped environments | ✅ |
| LSP-powered IDE tooling for DSL authoring | ✅ |

👉 [Explore the Enterprise Platform](https://datamimic.io) &nbsp;|&nbsp; [Book a platform demo](https://datamimic.io/contact)

---

## EE runtime profiles

The EE core supports three runtime configuration profiles, selectable per execution context:

| Profile | Optimises for | Typical use case |
|---|---|---|
| **Performance** | Maximum throughput via Rust fastpath, optimised multi-process execution, and Ray-based distribution | Bulk generation at billion-record volumes to PostgreSQL, Oracle, Kafka |
| **Balanced** | Throughput + full audit logging | Standard enterprise pipeline runs with compliance requirements |
| **Flexibility** | Deep nested evaluation, extended condition and ruleset processing | Complex domain models with ML engine combinations, multi-level referential structures |

Logging depth is independently configurable per profile — from minimal (throughput-optimised) to full nested tracing across importers, exporters, and generation stages.

---

## EE template engine

The EE template engine generates industry-standard financial messages from DATAMIMIC models. The workbench parses uploaded message samples, auto-detects the message type, and validates edits against the registered spec version in real time.

### Capabilities

- **Spec-aware form editing** — segments and elements rendered as structured forms with mandatory/optional indicators, per-field value suggestions, and inline custom-extension support
- **Strict validation** against baked spec versions, with segment- and element-level error reporting
- **Advisory mode** when a spec is unregistered or in draft — editing stays enabled, validation continues as guidance
- **Round-trip** between the structured form view and the authoritative template text — no fidelity loss
- **Download / adjust / upload your own spec** — customers can extend or override the baked spec catalogue without waiting for a release
- **Live structure tree + preview** for every edit
- **File auto-detection** — upload an existing message, the editor identifies the type and loads the matching spec

### Format coverage

| Format | Coverage |
|---|---|
| **UN/EDIFACT** | Schema-aware form editor; spec versions and subsets per engagement |
| **SWIFT MT** | Schema-aware form editor; categories and SR versions per engagement |
| **HL7 v2.x** | Schema-aware form editor; versions per engagement |
| **HL7 FHIR** | Schema-aware form editor for FHIR resources (Patient, Observation, Encounter, …); profiles per engagement |
| **Further industry formats** (ISO 20022 / MX, vertical dialects) | Built into the editor catalogue as part of POC and 1-year engagement scopes — typically delivered in days on the same framework |

Customers can also download, adjust, and upload their own specs directly — DATAMIMIC's spec library expands with customer needs, not with quarterly vendor release notes.

Generated messages are deterministic and traceable to their source model, and syntactically valid against the registered spec. They are intended for **test and training environments only** — they are not network-validated and must not be transmitted on production SWIFTNet or EDI networks. See the [SWIFT CSP note](#supported-systems) below.

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
- Provenance hash on every output = re-executable lineage

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

## How DATAMIMIC differs from Faker and generic generators

| | Faker / Random generators | DATAMIMIC CE | DATAMIMIC EE |
|---|---|---|---|
| Reproducible output | ❌ | ✅ | ✅ |
| Domain-aware relationships | ❌ | ✅ | ✅ |
| Business logic constraints | ❌ | ✅ | ✅ |
| Per-output provenance hash | ❌ | ✅ | ✅ |
| Source data pseudonymization | ❌ | ✅ manual | ✅ automated |
| PII field detection | ❌ | ❌ | ✅ probability-scored |
| Enterprise governance layer | ❌ | ❌ | ✅ |
| Multi-system execution | ❌ | ❌ | ✅ |
| Role-based workflows | ❌ | ❌ | ✅ |
| Designed for regulated-industry deployment (governance, audit, RBAC) | ❌ | ❌ | ✅ |

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
| **Seeded** (`rngSeed` set) | Deterministic, reproducible | Pseudonymization (GDPR Art. 4(5)) | Regression testing, stable CI/CD pipelines |
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

**2. Deterministic data backend for AI agents and LLM tooling.** The bundled MCP server (`pip install datamimic-ce[mcp]`) exposes `generate` as an MCP tool. Agents call it with seed, locale, count; outputs ship with a `determinism_proof.content_hash` so the same call can be re-executed and verified later — useful for agent regression tests and for any workflow where the data the agent saw needs to be reconstructable.

**3. Pseudonymization of staging and QA exports.** Manual model in CE (XML pipeline), no scanner license required. Seeded mode for stable regression test data; non-seeded mode for one-time deliveries with maximized privacy posture. See the [Pseudonymization section above](#pseudonymization--ce-manual-model).

---

## Where DATAMIMIC fits in your compliance program

DATAMIMIC produces evidence and reproducible artifacts that support compliance work. It does not replace your DPO, your CISO, or your auditor. The following are pointers for where DATAMIMIC outputs commonly slot into established programs:

> Both editions produce reproducible artefacts. CE covers single-system fixtures and provenance evidence; multi-system audit evidence with role-based dashboards is EE.

| Regulation / standard | Where DATAMIMIC contributes |
|---|---|
| **DORA (Reg. 2022/2554)** — Art. 25 (testing of ICT tools and systems) | Reproducible test datasets for non-TLPT resilience tests; deterministic data fixtures for ICT testing programmes |
| **ISO/IEC 27701:2019** — A.7.2.1, 7.2.8 (privacy by design and RoPA-supporting evidence) | Synthetic data in lieu of PII in non-production environments; documented model definitions as privacy-by-design evidence |
| **HIPAA Security Rule** — §164.312 technical safeguards *(US Covered Entities / Business Associates only)* | Synthetic Patient/MedicalDevice/MedicalProcedure data for dev and test environments without ePHI exposure |
| **GDPR** — Art. 4(5) pseudonymization definition; Art. 25 privacy by design; Art. 32 security of processing | Seeded pseudonymization with deterministic mapping; non-seeded mode for stronger privacy posture |
| **PCI DSS 4.0** — Req. 6.5.5 (live PANs prohibited in test/development) | Synthetic PAN generation for test environments; deterministic tokenisation reproducible across runs |

> These pointers do not constitute legal advice or a compliance attestation. Consult your DPO, CISO, or qualified counsel for formal compliance determinations. Full anonymization status under GDPR depends on re-identification risk across the complete dataset — see the [pseudonymization disclaimer above](#pseudonymization--ce-manual-model).

---

## Architecture

CE and EE share the DATAMIMIC DSL and the determinism contract. The execution layer is separate: CE is a Python execution engine using multiprocessing (with optional Ray for distribution); EE is an independently-optimised execution engine with a Rust fastpath, ML/auto-regressive generation, keyset and manifest building from live schemas, and optimised distributed execution at billion-record scale.

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
║  │  EE CORE  (separately maintained, more advanced than CE) │    ║
║  │                                                          │    ║
║  │  Rust fastpath for performance-critical paths            │    ║
║  │  ML / auto-regressive engine for complex distributions   │    ║
║  │  Keyset and manifest building from live DB schemas       │    ║
║  │  Optimised distributed execution at billion-record scale │    ║
║  │  Runtime profiles: Performance · Balanced · Flexibility  │    ║
║  │  Deep nested evaluation · Conditions · Rulesets          │    ║
║  │  Structured error catalog · Per-stage execution logging  │    ║
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
| EDIFACT / SWIFT MT | — | ✅ | Test/training output only; does not satisfy SWIFT CSCF v2025 secure-zone controls (1.1 environment protection, 1.4 internet restriction). Generated messages must not be transmitted from a CSP-attested secure zone. |

---

## CE domains

| Domain | Services available |
|---|---|
| **Healthcare** | Patient, Doctor, Hospital, MedicalDevice, MedicalProcedure |
| **Finance** | Bank, BankAccount, CreditCard, Transaction |
| **Insurance** | InsuranceCompany, InsuranceProduct, InsurancePolicy, InsuranceCoverage |
| **E-commerce** | Order, Product |
| **Public sector** | AdministrationOffice, EducationalInstitution, PoliceOfficer |
| **Demographics** | Person (DE / US / VN locale packs), Address |

All services are versioned and seeded; each generation emits a provenance hash suitable as evidence in audit reviews. Same deterministic API across domains: `Service().generate(seed=…, locale=…, count=…)`.

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

**DATAMIMIC — Deterministic, governed test data for regulated enterprises.**

[datamimic.io](https://datamimic.io) &nbsp;|&nbsp; [Book a demo](https://datamimic.io/contact) &nbsp;|&nbsp; [LinkedIn](https://linkedin.com/company/rapiddweller)
