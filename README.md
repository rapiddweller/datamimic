<p align="center">
  <a href="https://datamimic.io">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/rapiddweller/datamimic/development/docs/assets/datamimic-logo-dark.svg">
      <img alt="DATAMIMIC" width="370" src="https://raw.githubusercontent.com/rapiddweller/datamimic/development/docs/assets/datamimic-logo-light.svg">
    </picture>
  </a>
</p>

<h1 align="center">Community Edition</h1>

<p align="center"><b>Test data must agree with itself.</b></p>

<p align="center">
  <a href="https://docs.datamimic.io">Docs</a> |
  <a href="https://github.com/rapiddweller/datamimic/blob/development/docs/agent_plugin.md">Agent plugin</a> |
  <a href="https://datamimic.io/case-study/">Case studies</a> |
  <a href="https://github.com/rapiddweller/datamimic/discussions">Discussions</a> |
  <a href="https://datamimic.io">Enterprise Platform</a>
</p>

<p align="center">
  <a href="https://github.com/rapiddweller/datamimic/actions"><img alt="CI" src="https://github.com/rapiddweller/datamimic/actions/workflows/main.yml/badge.svg?branch=development"></a>
  <a href="https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic"><img alt="Coverage" src="https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=coverage"></a>
  <a href="https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic"><img alt="Maintainability" src="https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=sqale_rating"></a>
  <a href="https://www.python.org/downloads/"><img alt="Python 3.11 to 3.14" src="https://img.shields.io/badge/Python-3.11%20to%203.14-blue.svg"></a>
  <a href="https://github.com/rapiddweller/datamimic/blob/development/LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-green.svg"></a>
  <a href="https://github.com/rapiddweller/datamimic/blob/development/docs/agent_plugin.md"><img alt="MCP Ready" src="https://img.shields.io/badge/MCP-ready-8A2BE2.svg"></a>
</p>

Independent random values do not agree with each other: an order points to a customer that does not exist, a postal code does not belong to its city, and the next run gives different rows.

**DATAMIMIC Community Edition (CE) is an open-source Python library and command line tool, made by rapiddweller and released under the MIT license, that generates connected test data from one XML model.** Records reference each other, domain values come from data files, and the same seed gives the same rows again. CE can also replace personal data in an existing export.

<!-- Recording placeholder: docs/assets/build-ready.gif, made from docs/assets/build-ready.tape after #514 merges. Caption: what the GIF shows, the CE commit, a link to the tape and to the scenario s53_readme_shop. -->

- **Connected.** One XML project describes tables, nested records, references between records and conditions. CE writes CSV, JSON, XML, XLSX, DbUnit and fixed-width files, and writes to PostgreSQL, MySQL, Oracle, MS SQL Server, SQLite and MongoDB.
- **Repeatable.** Set `<setup rngSeed="7">`. The same CE version, project files and seed give the same rows on the tested platforms. CI compares seeded output on Linux with Python 3.11 to 3.14 and on Windows with Python 3.11, on each run.
- **Proven, not only generated.** `datamimic authoring build` runs the project with a row limit, checks each rule in `acceptance/build.json`, and replays the seeded run. The result is `ready` or `rejected`. `ready` is your proof that the data follows your rules. A ready Build lists every project file it read with its SHA-256. For a coding agent, `ready` is the signal that the work is done.
- **Made for coding agents.** One plugin for Claude Code and Codex installs the skills and a local MCP server. The MCP tools mirror the CLI commands.

> **Pre-release.** CE 5.0 is not on PyPI yet. PyPI has 4.3.0, which does not have the commands on this page. Until 5.0.0 is released, install from the GitHub branch `development` as shown below.

## Quick start: command line

You need Python 3.11 to 3.14.

```bash
python3.11 -m venv .venv && source .venv/bin/activate
python -m pip install "datamimic-ce @ git+https://github.com/rapiddweller/datamimic@development"
```

Make a project directory `shop` with these two files.

`shop/datamimic.xml`:

```xml
<setup rngSeed="7">
    <generate name="customers" count="25" target="CSV">
        <variable name="person" entity="Person" dataset="DE"/>
        <variable name="address" entity="Address" dataset="DE"/>
        <key name="id" generator="IncrementGenerator"/>
        <key name="name" script="person.name"/>
        <key name="postal_code" script="address.postal_code"/>
        <key name="city" script="address.city"/>
        <generate name="orders" count="2" target="CSV">
            <key name="customer_id" script="parent.id"/>
            <key name="line_no" generator="IncrementGenerator"/>
            <key name="amount" type="int" min="5" max="500"/>
        </generate>
    </generate>
</setup>
```

<details><summary><code>shop/acceptance/build.json</code> (the rules that Build checks)</summary>

```json
{
  "version": "5.0",
  "expectations": [
    {"kind": "exact_count", "subject": {"kind": "product", "product": "customers"}, "count": 25},
    {"kind": "exact_count", "subject": {"kind": "product", "product": "orders"}, "count": 50},
    {"kind": "unique", "subject": {"kind": "product", "product": "customers"}, "field": "id"},
    {"kind": "foreign_key",
     "child": {"subject": {"kind": "product", "product": "orders"}, "field": "customer_id"},
     "parent": {"subject": {"kind": "product", "product": "customers"}, "field": "id"}}
  ]
}
```

</details>

Check the project, then run it:

```bash
datamimic authoring build shop     # prints JSON; "outcome": "ready" and exit code 0
datamimic run shop/datamimic.xml   # writes shop/output/<task id>/customers.csv and orders.csv
```

A run generates the data. Build is the step that checks it. Thus use Build as the gate, and use a run for the full output.

### What you get

`customers.csv`:

```text
id|name|postal_code|city
1|Marion Abraham|36419|Schleid
2|Peter Bayer|24161|Levensau
3|Ludmila Jehle|56368|Katzenelnbogen
```

`orders.csv`:

```text
customer_id|line_no|amount
1|1|237
1|2|207
2|1|373
```

- Each order has the `id` of a customer in `customers.csv`. Build checks this with the `foreign_key` expectation. If you change `customer_id` to a random number, Build gives `rejected`.
- Each postal code belongs to its city: 36419 is Schleid. CE reads both values from one row of its German city data.
- Run it again, on your machine or in CI: seed 7 gives these rows again with this CE version.

| Build outcome | Exit code | Meaning |
|---|---|---|
| `ready` | 0 | All declared expectations passed on a complete, bounded capture. |
| `rejected` | 1 | Read the first entry in `diagnostics`, correct the project, build again. |

## Why not only Faker?

Faker gives single values, and CE uses Faker as a dependency. CE adds the model around the values.

| You need | With Faker | With CE |
|---|---|---|
| Records that reference each other | You write the code that keeps the keys correct. | A nested `<generate>` copies the key of its parent. Build checks the reference with a `foreign_key` expectation. |
| The same data again | You call `Faker.seed()` or `seed_instance()` in your code. | The seed is in the model: `<setup rngSeed="7">`. Build replays the seeded run, and CI compares seeded output on Linux and Windows. |
| A check that the data follows your rules | Faker has no check. You write tests. | `acceptance/build.json` holds the rules. Build gives `ready` or `rejected`. |

Use Faker for a few values in a unit test. Use CE when the data has a structure that must be correct each time.

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

What the agent does (from a recorded session with Claude Code, 2026-11-15; shortened, file reads left out):

```text
datamimic_reference      topic=assembly name=starter   -> project layout
datamimic_capabilities                                 -> entities, generators, exporters
datamimic_capability     domain=entity name=Person     -> fields of Person
Write                    datamimic.xml, acceptance/build.json
datamimic_build          project=./shop                -> outcome: ready
datamimic_run_project    project=./shop                -> completed, exit 0, 1.4 s
                                                          output/<id>/customers_csv.csv, 25 rows
```

<!-- Recording placeholder: docs/assets/agent-quick-start.gif, at most 30 seconds, recorded after P4a. Keep the text block above. -->

The first start of the MCP server downloads CE from GitHub and takes about 7 s. Later starts take about 1 s. We measured both on one machine.
If the server does not connect, the skills still work with the command line.
To use the MCP server without the plugin, install `python -m pip install "datamimic-ce[mcp] @ git+https://github.com/rapiddweller/datamimic@development"`.

What the agent can and cannot do:

- The MCP tools mirror the CLI: `datamimic_build` is `datamimic authoring build`, and so on.
- `datamimic_run_project` builds the project first, then runs it. It does not write to a database or another external target unless the call sets `allow_side_effects`. Give that permission only after you checked the named targets.
- A `ready` Build does not prove delivery to an external system.

More: [agent plugin guide](https://github.com/rapiddweller/datamimic/blob/development/docs/agent_plugin.md), [MCP guide](https://github.com/rapiddweller/datamimic/blob/development/docs/mcp_quickstart.md), the [consumer skill](https://github.com/rapiddweller/datamimic/blob/development/plugins/datamimic/skills/generate-test-data/SKILL.md) and the [model review format](https://github.com/rapiddweller/datamimic/blob/development/plugins/datamimic/skills/generate-test-data/references/review.md).

## Engineering you can check

- **The architecture contract is checked in public.** In each CI run, ArchKeel compares the observed structure of the code with the declared target contracts. The job `archkeel_check` must pass before a release. The [report](https://rapiddweller.github.io/datamimic/) is public. The budgets for accepted violations are ratchets: a raise needs an argued and verified amendment. A change to a contract needs an independent architecture review, recorded in a review note or in an approving review on the pull request ([how](https://github.com/rapiddweller/datamimic/blob/development/CONTRIBUTING.md)). There are 25 contract files, for example [`architecture-contract.json`](https://github.com/rapiddweller/datamimic/blob/development/architecture-contract.json), and the list of accepted violations in [`known-violations.json`](https://github.com/rapiddweller/datamimic/blob/development/known-violations.json) is empty.
- **The DSL is specified by checked-in projects.** Each of the 43 [scenarios](https://github.com/rapiddweller/datamimic/tree/development/tests_ce/scenarios) is a real `datamimic.xml` with an `acceptance/build.json`, a list of what it proves, and negatives that must fail. CI builds every scenario with `datamimic authoring build`.
- **CE and Enterprise compatibility is recorded.** The [parity matrix](https://github.com/rapiddweller/datamimic/blob/development/docs/architecture/inner/ce-ee-parity.md) lists each difference between the two editions with its status. CE runs the 8 shared [conformance cases](https://github.com/rapiddweller/datamimic/tree/development/tests_ce/conformance/cases) in CI; the Enterprise Core runner follows.
- **Seeded output is measured.** CI compares seeded output on 8 configurations: Linux with Python 3.11 (UTC, Los Angeles, lowest permitted dependency versions), 3.12, 3.13 and 3.14 (UTC), and Windows with Python 3.11 (UTC, Pacific). See the job [`runtime_determinism_matrix`](https://github.com/rapiddweller/datamimic/blob/development/.github/workflows/main.yml).

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

## Where DATAMIMIC is used

These projects used DATAMIMIC with the Enterprise Platform and services from rapiddweller, and the case studies describe the Enterprise Platform. The model language of these projects is the XML DSL that you use in CE.

| Sector | What was done, in the words of the case study |
|---|---|
| Payments | "Records anonymised inline at millions per hour" in Kafka streams, for records with "140-180 columns". [ACI Worldwide](https://datamimic.io/case-study/aci-worldwide-real-time-anonymisation-of-streaming-payment-data/) |
| Banking | Test data across Oracle, MongoDB and Kafka. Lead time: "Before 20-28 days After 6-12 hours". [Tier-1 European bank](https://datamimic.io/case-study/tier-1-european-bank-deterministic-test-data-across-oracle-mongodb-kafka/) |
| Public sector, statutory insurance | After a public tender, "DATAMIMIC replaced these legacy tools with model-driven test-data generation integrated into the client's CI/CD pipeline". [Public-sector body in German statutory accident insurance](https://datamimic.io/case-study/case-study-german-statutory-accident-insurance/) |
| Education | "Replaced the ~10,000-line custom generator with about 1,200 lines of DATAMIMIC models" for about 30 PostgreSQL schemas with more than 200 tables. [School management system](https://datamimic.io/case-study/school-management-system-consultancy-for-synthetic-data-in-hyper-sensitive-environments/) |

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

## Get help and contribute

- [Documentation](https://docs.datamimic.io), [agent plugin guide](https://github.com/rapiddweller/datamimic/blob/development/docs/agent_plugin.md), [MCP guide](https://github.com/rapiddweller/datamimic/blob/development/docs/mcp_quickstart.md), [developer guide](https://github.com/rapiddweller/datamimic/blob/development/docs/developer_guide.md)
- [GitHub Discussions](https://github.com/rapiddweller/datamimic/discussions) and [Issues](https://github.com/rapiddweller/datamimic/issues)
- Release notes: [GitHub releases](https://github.com/rapiddweller/datamimic/releases) and [CE 5.0](https://github.com/rapiddweller/datamimic/blob/development/docs/releases/5.0.md)
- Security: [SECURITY.md](https://github.com/rapiddweller/datamimic/blob/development/SECURITY.md). Do not report a vulnerability in a public issue.
- Contributing: [CONTRIBUTING.md](https://github.com/rapiddweller/datamimic/blob/development/CONTRIBUTING.md). The [current architecture report](https://rapiddweller.github.io/datamimic/) shows the observed structure and the target. Agents that work on this repository read [AGENTS.md](https://github.com/rapiddweller/datamimic/blob/development/AGENTS.md).
- Email: support@rapiddweller.com

## License

MIT. See [LICENSE](https://github.com/rapiddweller/datamimic/blob/development/LICENSE). The DATAMIMIC Enterprise Platform is a separate commercial product of rapiddweller. [Contact rapiddweller](https://datamimic.io/contact).

The DATAMIMIC name and logo are trademarks of rapiddweller and are not covered by the MIT license.
