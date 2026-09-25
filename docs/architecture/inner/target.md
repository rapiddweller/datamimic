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
      contexts/  storage/  lifecycle/  scripting/
      tasks/
        generate/
          workers/  services/policies/
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

The CE component contract passes, but the 0.7.0 observation still contains
168 module cycle edges. The largest SCCs contain 28 DSL and 23 Runtime modules.
ArchKeel's automatic Runtime draft made 15 components and 210 pair decisions; one
component per directory or file would codify noise, not ownership.

All five CE component interiors have active drafts. ArchKeel 0.7.0 parses all
475 CE files and reports 89 target violations after correcting three wrongly
forbidden Generate-to-worker edges and moving IO pagination/selection ownership
(the first draft reported 97). The parent `requires` edges and numeric baseline
were not widened. These are rule findings, not 89 independent design decisions.

| Interior | Violations | Main cause to inspect |
| --- | ---: | --- |
| Domains | 58 | `domain_core` registries import shared generators and vertical services; place registration with its owner instead of permitting reverse dependencies. |
| DSL | 26 | The model-side element registry imports concrete parsers; bind implementations from the parser side. |
| IO | 1 | Pagination now lives in IO contracts and selector cycling in Runtime sources. The remaining `data_sources`↔`exporters.memstore` dependency still needs an ownership decision. |
| Runtime | 2 | Generate-to-worker imports are legitimate inside Generate orchestration. Investigate remaining facade and global-config dependencies separately. |
| Authoring | 2 | `rules.base` imports a schema fact lookup and a pure element-path helper; move those small facts/functions to the rule/domain owner, not a new framework. |

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
| IO | Separate API, contracts, clients, sources, exporters, and files. Sources read through clients; exporters own writes; clients do not import source policy. | EE read/write ownership and CE's three-module client/source SCC. | Pagination and cyclic selection have moved; resolve the source/exporter dependency without changing descriptor behavior. |
| Runtime | Lifecycle starts Setup; Generate owns per-statement worker policy and execution. Contexts own state; IO owns reads/writes. | EE keeps policies and workers under `tasks/generate/`, while Lifecycle only starts Setup. | Move CE workers below Generate, remove task-side client construction, and verify setup, seeded replay, and external-service descriptors. |
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
| `engine/runtime/{contexts,tasks,storage,lifecycle,scripting}` with `tasks/generate/workers` | CE workers still sit beside tasks; lifecycle and scripting logic is partly flat. | `tasks/`, `contexts/`, and `lifecycle/` are root siblings; workers and policy live under `tasks/generate/`. | Both editions use the same owner paths; Rust and advanced policies remain inside Runtime, not new root peers. |
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

## Entry points and acceptance

```text
CLI run / Python DataMimic or factory
  -> Runtime API -> DSL parse -> Setup -> Generate/other tasks
  -> IO data sources and exporters -> result or stable error

CLI lint/dry-run/scaffold / MCP tools
  -> Authoring API -> intent projection or XML lint
  -> optional bounded Runtime execution -> diagnostics and verification
```

CLI and MCP adapt requests and present results; they do not own execution or
authoring policy. MCP `datamimic_run` is a bounded dry-run, not the unrestricted
CLI `run`. Public boundaries must expose typed operations and results, not
concrete client or exporter classes merely re-exported through `io.api`.
Runtime Lifecycle prepares and starts Setup; Generate owns worker selection for
each statement. IO owns source routing and write policy. The same concern has
one owner in both editions.

Acceptance requires no production module dependency cycles, not just no cycles
between top-level components. Function-local imports do not erase a dependency
cycle. The current Pylint 3.3.7 diagnostic reports 53 overlapping cycle paths;
triage shared causes before treating that as 56 separate fixes. ArchKeel 0.7.0
observes module cycles but does not enforce them in `inside` contracts. Until
it does, use one targeted Pylint cycle check alongside ArchKeel and the DSL
behavior suite; do not add a parallel collection of custom gates.

Bounded Authoring must apply its count, target, and side-effect policy to every
descriptor expansion. CE currently rejects XML `<include>` during dry-run
because included statements are parsed later; `.properties` includes remain
allowed. Safe support for XML includes requires a separately verified expansion
path. Full `run` retains XML include behavior.

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
