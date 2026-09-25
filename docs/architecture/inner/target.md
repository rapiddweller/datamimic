# CE/EE inner architecture target — draft

Status: agent proposal. Alex approved a target-first contract and the same physical
core structure in CE and EE. This is a path invariant, not merely matching boxes in
a report. EE runtime semantics lead; its current root-level engine owners are not
the target. This document does not authorize an EE file move or change descriptor behavior.

## Physical target in both editions

Replace `<edition>` with `datamimic_ce` or `datamimic_ee`. These directories and
their ownership must exist in both editions where the shared feature exists:

```text
<edition>/
  authoring/
    api.py  contracts.py  spec.py
    domain/  application/  adapters/  projection/
  errors/
    base.py  catalog/  context/  factory.py  formatters.py
  domains/
    domain_core/       # domain contracts and primitives
    shared/            # reusable generators and shared data
      models/  services/  generators/  literal_generators/  converters/
    {finance,healthcare,insurance,ecommerce,public_sector}/  # vertical owners
  engine/
    dsl/
      api.py  contracts.py
      constants/  enums/  model/  parsers/  statements/
    io/
      api.py  contracts.py
      clients/  connection_config/  data_sources/  exporters/
    runtime/
      api.py  contracts.py  logging.py
      contexts/  tasks/  workers/  storage/  lifecycle/  scripting/
  interfaces/
```

This is the common core skeleton, not a demand for identical files or features.
Edition-only connectors belong under `engine/io/`; EE-only task and worker policies
belong under `engine/runtime/`. A shared capability must keep the same owning path
and public boundary in both editions. CE's current `domains/common` and EE's root
`model/`, `parsers/`, `tasks/`, `clients/`, `data_sources/`, and `exporters/` are
transitional, not additional target owners. Do not create empty placeholder packages.
The package name differs only at `<edition>`.

The CE `ENGINE-LAYOUT` rule forbids a fourth direct `engine/` child. ArchKeel's
current `root_layout` rule checks allowed children but does not require missing
children or compare two repositories. Full physical parity therefore needs an
explicit CE/EE path comparison at acceptance; a green contract alone cannot prove it.

## Why another level

The CE component contract passes, but the 0.7.0 observation still contains six module
SCCs and 171 cycle edges. The largest SCCs contain 28 DSL and 23 Runtime modules.
ArchKeel's automatic Runtime draft made 15 components and 210 pair decisions; one
component per directory or file would codify noise, not ownership.

All five CE component interiors now have active drafts. ArchKeel 0.7.0 parses all
476 CE files and reports 97 target violations: Domains 58, DSL 26, IO 6,
Runtime 5, Authoring 2. The parent `requires` edges and numeric baseline were
not widened. These are migration work, not permissions to add to `requires`.

| Interior | Target violations | Main cause, not 97 independent design decisions |
| --- | ---: | --- |
| Domains | 58 | `domain_core` registries import shared generators and all vertical services; `base_domain_service` imports a shared utility. Move registration to `shared` instead of permitting reverse dependencies. |
| DSL | 26 | The model-side element registry imports concrete parsers. Bind them from the parser side. |
| IO | 6 | Three clients import source policy; `exporters.memstore` is imported by source modules. Move shared types and ownership to the correct side. |
| Runtime | 5 | A task imports the public facade, another reads global config, and `generate_task` schedules three worker implementations. Scheduling belongs to lifecycle. |
| Authoring | 2 | `rules.base` imports schema projection and XML loading. Pass pure facts into rules instead. |

Current-file assignments cover every non-root module within the five interiors.
Their root `__init__.py` modules remain unassigned in the report; notably,
`authoring/__init__.py` re-exports use cases and is not an inert package marker.
ArchKeel 0.7.0 does not enforce that gap. Do not place the package root in the
`api` sub-component: it would overlap every child and leave them all ownerless.
The target owner labels describe where code should end up, not a claim that CE
already has the EE-like directories. `domains/shared` still groups 98 current
modules; its EE-like child directories are physical acceptance criteria, not
an extra level ArchKeel 0.7.0 can enforce in an `inside` contract.

## Agent decisions

| Area | Target boundary | Basis | Consequence |
| --- | --- | --- | --- |
| IO | Separate API, contracts, clients, sources, exporters, and files. Sources read through clients; exporters own writes; clients do not import source policy. | EE read/write ownership and CE's three-module client/source SCC. | Move pagination types and cyclic selection out of clients; retain descriptor behavior. |
| Runtime | Lifecycle schedules; workers execute tasks; contexts own state; logging and scripting are separate runtime owners. IO constructs clients and owns reads/writes. | EE's accepted no-tasks-to-clients rule. CE `generate_task` schedules workers, while workers import tasks. | Move scheduling out of tasks, replace task-side client construction behind a typed IO seam, and verify setup, seeded replay, and external-service descriptors. |
| DSL | Typed models own grammar facts; parsing binds parser implementations; statements carry executable meaning. No second element catalog. | Both editions derive Authoring/DSL capabilities from typed owners. CE's registry↔parser SCC is 28 modules. | Separate registry facts from parser construction without duplicating the vocabulary; compare Authoring projections and XML behavior. |
| Domains | `domain_core` owns primitives, `shared` owns common generators and registrations, and finance/healthcare/insurance/ecommerce/public-sector own their vertical behavior. | EE already uses this split; CE `common` and `domain_core` import each other. | Move CE `common` to `shared` and both built-in registries out of the core; fold `doctor`/`patient` into healthcare and `address`/`person` into shared. No compatibility shim. |
| Errors | One root `errors/` owns stable user-facing codes, exception types, descriptor context, factories, and formatting. Local validation rules remain with their component; logging configuration remains in Runtime. | EE already owns this under `errors/`; CE has scattered exceptions and separate Authoring validation codes. | Migrate shared error semantics from EE into CE without copying EE-only codes or changing unrelated Authoring validation contracts. |
| Authoring | Intent and rules are pure; projection derives DSL facts; adapters handle XML and bounded execution; application sequences use cases. | EE's `domain/application/adapters/projection` split and CE's transport separation. | Remove two rule imports of file/schema adapters; keep Runtime access inside the bounded execution adapter, without inventing a second DSL vocabulary. |

These are agent decisions, not a claim that current code satisfies them. No target
edge is permitted solely because the current implementation imports it.

## EE migration impact

| Shared target | CE today | EE today | Migration consequence |
| --- | --- | --- | --- |
| `engine/dsl/{model,parsers,statements,constants,enums}` | Already under `engine/dsl/`. | `model/`, `parsers/`, `statements/`, `constants/`, `dsl_contract/` are root siblings. | EE moves these owners into the matching paths without copying DSL facts into Authoring. |
| `engine/runtime/{contexts,tasks,workers,storage,lifecycle,scripting}` | CE has contexts/tasks/workers/storage; lifecycle and scripting logic is still flat. | `tasks/`, `contexts/`, `lifecycle/`, and scripting are root siblings; worker code is below tasks. | Both editions use the same owner paths; Rust and advanced policies remain inside Runtime, not new root peers. |
| `authoring/{domain,application,adapters,projection}` | CE logic is mostly flat. | EE already uses the four groups. | CE adopts the EE owner paths; public root `api.py`, `contracts.py`, and `spec.py` stay explicit. |
| `engine/io/{clients,connection_config,data_sources,exporters}` | Already under `engine/io/`. | `clients/`, `data_sources/`, and `exporters/` are root siblings. | EE moves those owners into the matching paths; Kafka/RabbitMQ and other EE connectors stay under IO. |
| `domains/{domain_core,shared,...}` | CE still uses `common` beside `domain_core`. | EE uses `shared` and `domain_core` plus vertical domains. | CE adopts the EE ownership split; `domains.common` is removed, not retained as an alias. |
| `errors/{base.py,catalog,context,factory.py,formatters.py}` | No root `errors/`; exceptions are scattered. | EE already has the target owner. | CE adopts EE's shared stable codes and types; EE-only codes stay in EE under the same owner. |

Same physical structure means comparable ownership and navigation, not identical
edition behavior, runtime settings, Rust support, or seeded output. EE's source
checkout is clean under `datamimic_ee/`; its current ArchKeel-migration worktree
contains unrelated uncommitted governance changes and is not an accepted target.

## Accepted 5.0 compatibility decision

Alex decided against a `domains.common` compatibility path. Move repository-owned
imports in code, tests, docs, and bundled descriptor scripts to `domains.shared`
when the implementation moves, then delete `domains.common`. For example,
`tests_ce/integration_tests/test_entity/customer.xml` loads `script/customer.scr.py`,
which imports `Person` from `domains.common.models.person`; that script must move
to the new import while the XML and its generated result remain unchanged.
External Python scripts importing `domains.common` will need the same migration.
This is an explicit Python import break for CE 5.0, not a promise of unchanged
external script execution.

## Accepted error ownership decision

Alex chose a root `errors/` in both editions for stable codes and types. EE's
existing package is the reference for shared user-facing error behavior. CE's
current Authoring-only validation codes are not moved just to make the tree
look symmetric; move a code only when it is genuinely shared. Error factories
own user-facing formatting, while components still decide when to raise and
Runtime retains logging configuration. No empty CE package is created for the
draft; ArchKeel 0.7.0 rejects an `errors` component before any Python module
exists (`reference.package_unscanned`). The first implementation slice adds
real code, declares the component, and activates its public boundary. For a
failure supported in both editions, verify the same stable code and public
error type; EE-only codes remain EE-only.

## Tool and delivery limits

ArchKeel 0.7.0 can load an `inside` JSON contract, check its public surface against
the parent, and enforce its `complete_requires` edges. It does not currently
enforce the inside's module assignment, cycle, interface, or external-scope rules,
and its report reads only one inside level. A green inner edge check is therefore
not proof of a fully enforced lower-level architecture.
For example, the outer Runtime rule permits `runtime -> io.api`; it cannot tell
that the exported class is a concrete database client instantiated by a task.
The no-tasks-to-clients obligation needs a separate symbol/construct check or
review until ArchKeel can express it. Do not waive it because the inner count is low.

Keep the existing CE branch and baseline unchanged while target contracts are
drafted in an isolated worktree. All five inside contracts are active there and
intentionally red. Preserve those findings as work to resolve in small slices.
Every production slice needs positive and negative tests, the
descriptor oracle, full static gates, and exact EE/CE ownership review. EE gets
its own migration and edition-local seeded replay; CE and EE need not generate
the same values.

Suggested order: finish CE target contracts and architect decisions; close the
ArchKeel inside-enforcement gap; remove CE target violations in narrow slices;
run the full CE descriptor and test gates; then migrate EE to the same physical
core layout with EE-local architecture and behavior gates. Do not combine the
CE and EE file moves into one review.
