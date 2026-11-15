# DATAMIMIC Community Edition

[![CI](https://github.com/rapiddweller/datamimic/actions/workflows/main.yml/badge.svg?branch=development)](https://github.com/rapiddweller/datamimic/actions)
[![Python](https://img.shields.io/badge/Python-3.11%20to%203.13-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/rapiddweller/datamimic/blob/development/LICENSE)

**DATAMIMIC Community Edition (CE) is an open-source Python library and command line tool for test data, made by rapiddweller and released under the MIT license.**
You describe the data in an XML model. CE generates synthetic data from the model, or replaces personal data in an existing export. With a seed, the same model gives the same data again.

- **Model-driven.** One XML project describes tables, nested records, references between records, and conditions. CE writes CSV, JSON, XML, XLSX, DbUnit and fixed-width files, and writes to PostgreSQL, MySQL, Oracle, MS SQL Server, SQLite and MongoDB.
- **Repeatable.** Set `<setup rngSeed="7">`. The same CE version, project files and seed give the same rows on the tested platforms. CI compares seeded output on Linux with Python 3.11 to 3.13 and on Windows with Python 3.11, on each run.
- **Checked before you use it.** `datamimic authoring build` runs the project with a row limit and checks it against the expectations in `acceptance/build.json`. The result is `ready` or `rejected`. A ready Build lists every project file it read with its SHA-256. Build is the only proof; a successful run without Build proves nothing about the data.
- **Made for coding agents.** One plugin for Claude Code and Codex installs the skills and a local MCP server. The MCP tools mirror the CLI commands.
- **Pseudonymization.** Replace names, addresses and account numbers in a staging export with generated values or keyed hashes. You name the fields; CE does not scan for personal data.

> **Pre-release.** CE 5.0 is not on PyPI yet. PyPI has 4.3.0, which does not have the commands on this page. Until 5.0.0 is released, install from the GitHub branch `development` as shown below.

## Quick start: command line

You need Python 3.11 to 3.13.

```bash
python3.11 -m venv .venv && source .venv/bin/activate
python -m pip install "datamimic-ce @ git+https://github.com/rapiddweller/datamimic@development"
```

Make a project directory `shop` with two files.

`shop/datamimic.xml`:

```xml
<setup rngSeed="7">
    <generate name="customers" count="25" target="CSV">
        <variable name="person" entity="Person" dataset="DE"/>
        <key name="id" type="int" generator="IncrementGenerator"/>
        <key name="name" script="person.name"/>
        <key name="email" script="person.email"/>
    </generate>
</setup>
```

`shop/acceptance/build.json`:

```json
{
  "version": "5.0",
  "expectations": [
    {"kind": "exact_count", "subject": {"kind": "product", "product": "customers"}, "count": 25}
  ]
}
```

Check the project, then run it:

```bash
datamimic authoring build shop     # prints JSON; "outcome": "ready" and exit code 0
datamimic run shop/datamimic.xml   # writes shop/output/<task id>/customers.csv
```

| Build outcome | Exit code | Meaning |
|---|---|---|
| `ready` | 0 | All declared expectations passed on a complete, bounded capture. |
| `rejected` | 1 | Read the first entry in `diagnostics`, correct the project, build again. |

## Quick start: coding agents

The plugin gives the agent two skills and a local MCP server. You need [`uv`](https://docs.astral.sh/uv/) for the MCP server.

Claude Code:

```bash
claude plugin marketplace add https://github.com/rapiddweller/datamimic.git
claude plugin install datamimic@datamimic
```

Codex:

```bash
codex plugin marketplace add https://github.com/rapiddweller/datamimic.git
codex plugin add datamimic@datamimic
```

Start a new session in your project and ask:

```text
Use DATAMIMIC. In ./shop make a project that generates 25 customers
(id, name, email) as CSV with seed 7. Build until the outcome is ready,
then run it. Show me the model and the Build evidence.
```

The first start of the MCP server downloads CE from GitHub and takes about 7 s. Later starts take about 1 s. We measured both on one machine.
If the server does not connect, the skills still work with the command line.
To use the MCP server without the plugin, install `python -m pip install "datamimic-ce[mcp] @ git+https://github.com/rapiddweller/datamimic@development"`.

What the agent can and cannot do:

- The MCP tools mirror the CLI: `datamimic_build` is `datamimic authoring build`, and so on.
- `datamimic_run_project` builds the project first, then runs it. It does not write to a database or another external target unless the call sets `allow_side_effects`. Give that permission only after you checked the named targets.
- A `ready` Build does not prove delivery to an external system.

More: [agent plugin guide](https://github.com/rapiddweller/datamimic/blob/development/docs/agent_plugin.md), [MCP guide](https://github.com/rapiddweller/datamimic/blob/development/docs/mcp_quickstart.md).

## What can CE do?

- **Generate.** `<generate>`, nested keys, lists, references between records, `<if>` and `<while>`, `<state-machine>`, `<assert>` and a memstore. [Worked projects](https://github.com/rapiddweller/datamimic/blob/development/docs/examples/authoring.md) show nested foreign keys, memstore readback and time series.
- **Read sources.** CSV, JSON, XML, XLSX, DbUnit, fixed-width files, SQL databases and MongoDB. For database connections use [connection profiles](https://github.com/rapiddweller/datamimic/blob/development/docs/developer_guide.md#database-and-mongodb-connection-profiles).
- **Time series.** Give `<generate>` the attributes `start`, `end` and `interval`. See the [time-series guide](https://github.com/rapiddweller/datamimic/blob/development/docs/guides/time-series.md).

```xml
<generate name="readings" start="2026-01-01T00:00:00+00:00"
          end="2026-01-02T00:00:00+00:00" interval="PT1H" target="CSV">
    <key name="timestamp" script="ts.now.isoformat()"/>
    <key name="value" script="20 - 10 * math.cos(ts.now.hour * math.pi / 12)"/>
</generate>
```

- **Domain data.** Ready-made services for these domains ([examples](https://github.com/rapiddweller/datamimic/blob/development/docs/guides/domain-examples.md)):

| Domain | Services |
|---|---|
| Healthcare | Patient, Doctor, Hospital, MedicalDevice, MedicalProcedure |
| Finance | Bank, BankAccount, CreditCard, Transaction |
| Insurance | InsuranceCompany, InsuranceProduct, InsurancePolicy, InsuranceCoverage |
| E-commerce | Order, Product |
| Public sector | AdministrationOffice, EducationalInstitution, PoliceOfficer |
| Demographics | Person (locale packs; see the [domain docs](https://github.com/rapiddweller/datamimic/blob/development/docs/data-domains/README.md)), Address, City, Country |
| Common | Company |

## Is the output reproducible?

Yes, under these conditions: the same CE version, the same project files and the same seed, on the tested platforms. Without a seed the output is not repeatable.

- `datamimic authoring build` replays a seeded project and reports `deterministic_replay`.
- CI replays a committed model in two separate processes on each run. It covers 4 of 4 facade domains, 23 of 23 entities and 34 of 35 literal generators.
- The evidence is for CE only. See the [determinism evidence](https://github.com/rapiddweller/datamimic/blob/development/docs/determinism.md) for the test matrix and its limits.

## How do I pseudonymize an export?

Name the fields and give each one a generated replacement. This model is the tested scenario [`s28_pseudonymize_source`](https://github.com/rapiddweller/datamimic/tree/development/tests_ce/scenarios/s28_pseudonymize_source). It replaces the personal data in a pipe-separated export (`customer_id|first_name|last_name|email|iban|birth_date`):

```xml
<setup rngSeed="42">
  <generate name="customers" source="data/entity/customers.ent.csv" target="CSV" distribution="ordered">
    <!-- rngSeed makes seeded runs produce the same pseudonyms; remove it for a new
         mapping per run. distribution="ordered" keeps source row N mapped to the
         same pseudonym. -->
    <variable name="p"   entity="Person"      dataset="DE" />
    <variable name="acc" entity="BankAccount" dataset="DE" />

    <key name="customer_id" script="customer_id" />
    <key name="first_name" script="p.given_name" />
    <key name="last_name"  script="p.family_name" />
    <key name="email"      script="p.email" />
    <key name="iban"       script="acc.iban" />
    <key name="birth_date" script="p.birthdate" />
  </generate>
</setup>
```

- You name the fields. CE does not scan for personal data.
- With a seed and the same row order, the replacements repeat.
- For tokens that stay stable across runs, use the `Hash` converter with an external key. Pass the key with `--param-env`.
- Pseudonymized data is still personal data ([GDPR Art. 4(5)](https://eur-lex.europa.eu/eli/reg/2016/679/oj#d1e1888-1-1), [Recital 26](https://eur-lex.europa.eu/eli/reg/2016/679/oj#rct_26)).

Use a controlled export or staging input, not a live production source. Key management and the converter list are in the [pseudonymization guide](https://github.com/rapiddweller/datamimic/blob/development/docs/guides/pseudonymization.md).

## How is DATAMIMIC CE different from Faker?

| | Faker | DATAMIMIC CE |
|---|---|---|
| Related fields | `profile()` and `simple_profile()` return related personal fields | Patient conditions are weighted by age (`PatientService`); `ageMin` and `ageMax` limit the age range |
| References between records | You write the code | Nested `<generate>` and the `<reference>` element in the model |
| Seed | `Faker.seed()` seeds the shared generator for all instances in the process | `rngSeed` in `<setup>` seeds a full project, including references between tables; CI replays seeded projects |
| Check against expectations | No | `datamimic authoring build` |

CE uses Faker as a dependency for some generators.

## Command reference

Authoring commands print JSON and accept a file or `-` for standard input.

| Command | MCP tool | Use |
|---|---|---|
| `datamimic authoring build <project>` | `datamimic_build` | Check a project against `acceptance/build.json` |
| `datamimic authoring run-project <project>` | `datamimic_run_project` | Build, then run for real data |
| `datamimic run <datamimic.xml>` | none | Run a model |
| `datamimic authoring lint <file>` | `datamimic_lint` | Check one XML file |
| `datamimic authoring dry-run <file>` | `datamimic_dry_run` | Run one XML file with a bounded capture |
| `datamimic authoring run <file>` | `datamimic_run` | Run one XML file with limits |
| `datamimic authoring version` | `datamimic_version` | Show the CE version and contracts |
| `datamimic authoring schema [--name <name>]` | `datamimic_schema` | Show a contract schema |
| `datamimic authoring capabilities` | `datamimic_capabilities` | List the DSL vocabulary |
| `datamimic authoring capability --domain element --name generate` | `datamimic_capability` | Show one element |
| `datamimic authoring reference --topic assembly --name model` | `datamimic_reference` | Read focused guidance |
| `datamimic authoring compile -` / `decompile <file>` | `datamimic_compile` / `datamimic_decompile` | Convert between DM JSON and XML |
| `datamimic init`, `demo list`, `demo create`, `info`, `version` | none | Project and demo helpers |

Exit codes: 0 for success, 1 for a rejected result, 2 for a usage error.

## Python API

```python
import random
from datamimic_ce.domains.healthcare.services import PatientService

patient = PatientService(rng=random.Random(42)).generate()
print(patient.full_name, patient.age, patient.conditions)  # the same values for seed 42
```

```python
from datamimic_ce.domains.facade import generate_domain

response = generate_domain({
    "domain": "person", "version": "v1", "count": 1,
    "seed": "ci-42", "locale": "en_US", "clock": "2026-01-01T00:00:00Z",
})
print(response["determinism_proof"]["content_hash"])
```

The content hash is on the results of `generate_domain` (person, address, patient, doctor). Files from `datamimic run` have no such hash.

## Where can CE support a compliance program?

DATAMIMIC provides test data and run evidence that can support compliance work. It does not replace your data protection officer, your security officer or your auditor. The [compliance pointers](https://github.com/rapiddweller/datamimic/blob/development/docs/guides/compliance-pointers.md) show where CE output fits for DORA, ISO/IEC 27701, HIPAA, GDPR and PCI DSS 4.0.1. They are not attestations.

## What is the difference between DATAMIMIC CE and the Enterprise Platform?

DATAMIMIC has two editions. Both use the same XML model language.

**Community Edition (this repository)** is a Python library and a command line tool. Your team installs it, keeps the project files, and runs it on a workstation or in CI. It has no web UI, no source scanner, no scheduler, no access control, no Kafka or RabbitMQ target and no message template engine.

**The DATAMIMIC Enterprise Platform** is a commercial, self-managed product for teams. It runs on a separate engine, the Enterprise Core. It adds a web UI, shared projects with access control, a Workbench that scans data sources, tasks with a scheduler, and IDE extensions for [VS Code](https://docs.datamimic.io/tutorial/install-ide-extension/) and [JetBrains IDEs](https://plugins.jetbrains.com/plugin/34581-datamimic). ([Release notes](https://docs.datamimic.io/release-notes/))

What a team gets from the Platform, and where the proof is:

- **Scale.** The Enterprise Core is designed for billion-record workloads: it works in pages, and memory does not grow with the record count. The largest published measurement is 100 million records for each connected system, with 4 workers and a peak process memory of 1.45 GiB or less. ([Release notes 4.0.0](https://docs.datamimic.io/release-notes/))
- **Runtime profiles (Performance, Balanced, Flexibility).** Today you set logging, paging and connector tuning for each project in Runtime Configuration. The three profiles are presets of these values and are planned. ([Runtime configuration per project](https://docs.datamimic.io/reference/ui/settings/runtime-config/))
- **CI/CD and Tosca.** A pipeline uses the REST API with a project access token to change project files, start runs and get artifacts. The documentation names GitHub Actions, GitLab CI, Jenkins and Azure Pipelines. ([API](https://docs.datamimic.io/reference/api/), [Workspace API](https://docs.datamimic.io/reference/api/workspace-api/)) One bank connected DATAMIMIC to Tosca DI in a project. ([Case study](https://datamimic.io/case-study/tier-1-european-bank-deterministic-test-data-across-oracle-mongodb-kafka/))
- **Message formats and HL7 FHIR.** The Platform has templates for EDIFACT, SWIFT MT and HL7 messages, for test and training systems only. ([Release notes 2.3.0 and 2.6.0](https://docs.datamimic.io/release-notes/)) The [Demo Store](https://docs.datamimic.io/reference/ui/demostore/) has built-in demos that you clone into a project. One of them is a FHIR R4 project, "Payer Claims in FHIR R4".
- **Approval flows (review and consent steps).** Today these are review and consent steps, not an approval by a second person. A person reviews the PII preselection before a model is created, sets a reviewed ML generator version as default, and gives consent before an agent starts a run that can write to external systems. ([PII review in the Database Workbench](https://docs.datamimic.io/reference/ui/database/), [ML generator versions](https://docs.datamimic.io/reference/ui/ml-generator-view/), [consent for agent runs](https://docs.datamimic.io/advanced/connect-mcp-client/))
- **Audit-evidence artifacts for GDPR Art. 30, PCI DSS 4.0.1 Req. 6.5.5, HIPAA Security Rule reviews.** For each run the Platform keeps the actor, the time, the status, the log, a snapshot of the project and the artifacts. ([Task records](https://docs.datamimic.io/reference/ui/tasks/)) A team can attach these records to its GDPR Art. 30 documentation, to a PCI DSS 4.0.1 Req. 6.5.5 review, or to a HIPAA Security Rule review. DATAMIMIC does not certify compliance.

The two editions use different engines. Do not expect the same output bytes from CE and from the Platform for the same model and seed. The determinism evidence in this repository is for CE only.

The agent plugin works with both: with a local CE project, or with a project on a connected Platform.

Comparison: https://datamimic.io

## Documentation and help

- [Documentation](https://docs.datamimic.io)
- [Agent plugin guide](https://github.com/rapiddweller/datamimic/blob/development/docs/agent_plugin.md) and [MCP guide](https://github.com/rapiddweller/datamimic/blob/development/docs/mcp_quickstart.md)
- [Developer guide](https://github.com/rapiddweller/datamimic/blob/development/docs/developer_guide.md) and [worked examples](https://github.com/rapiddweller/datamimic/blob/development/docs/examples/authoring.md)
- [GitHub Discussions](https://github.com/rapiddweller/datamimic/discussions) and [Issues](https://github.com/rapiddweller/datamimic/issues)
- Email: support@rapiddweller.com

## Contributing

See [CONTRIBUTING.md](https://github.com/rapiddweller/datamimic/blob/development/CONTRIBUTING.md). The [current architecture report](https://rapiddweller.github.io/datamimic/) shows the observed structure and the target. Agents that work on this repository read [AGENTS.md](https://github.com/rapiddweller/datamimic/blob/development/AGENTS.md).

## License

MIT. See [LICENSE](https://github.com/rapiddweller/datamimic/blob/development/LICENSE). The DATAMIMIC Enterprise Platform is a separate commercial product of rapiddweller. [Contact rapiddweller](https://datamimic.io/contact).
