# CE / EE target architecture — recursive definition

Date: 2026-09-27. Status: **Astra-decided target; implementation not complete**.
See [Astra's semantic decisions](semantic-review/astra-target-decision.md) and
[Amendment 20](../refactoring-study/experiment-2/amendment-20.md).
Published ArchKeel 0.8.0 timed out on the earlier draft. The local candidate
completes but reports failures; neither result certifies this target.
This replaces the earlier 0.7 design notes in this file, not the experiment history.
Alex's decisions: equal physical core paths, EE leads shared semantics, stable root
`errors/`, no legacy import shims, no Rust or EE runtime configuration in CE.
Delegated grouping and interface decisions remain marked `decided_by: agent` in JSON.

The source-to-target map and recursive review are in
[structure-review.json](structure-review.json). The shared root below applies to
both `datamimic_ce` and `datamimic_ee`. See [EE migration](edition-alignment.md)
for edition-only additions and the superseded Experiment 3 proposal.
Each current CE Python file has one target sentence in the deepest mounted
contract's `declarations.modules`; those declarations are the report's target
inventory. The source review is historical evidence; its explicit target
overrides must match the contract declarations.

Every current CE Python module has a target path and a candidate responsibility
sentence: one-to-one moves inherit the historical source concern from
`semantic-review/review-*.json`; revised modules have explicit
`target_module_concerns` in the structure review. Ownership and migration intent
are decided by the semantic target decision
and subsequent named amendments. Module declarations encode that intent;
coverage checks do not establish semantic correctness or completed migration.
Member and relationship assertions cover only explicitly authored slices. The root
`__init__.py` is an inert package initializer, not an environment owner.
CLI and MCP executable startup load only the startup cwd `.env` with
`override=False` before reading settings or transport defaults. Library callers
prepare their own environment. Runtime settings resolve on use. Descriptor
`.env.properties` lookup remains separate. This deliberately changes the old
import-time bootstrap behavior ([Amendment 68](../refactoring-study/experiment-2/amendment-68.md)).
The regular root package remains the installed-distribution origin anchor, owned only
as exact module `datamimic_ce` by `distribution`, without descendant scope or grants
([Amendment 173](../refactoring-study/experiment-2/amendment-173-root-distribution-owner.md)). Engine
is an implicit grouping namespace; DSL, IO and Runtime retain their own modules.
Neither grouping introduces a catch-all component. External Engine introspection/discovery compatibility,
other Python versions and EE packaging remain UNKNOWN
([Amendment 171](https://github.com/rapiddweller/datamimic/blob/384b7723d950d8b312b1080d23ffd89a5343c9b0/docs/architecture/refactoring-study/experiment-2/amendment-171-engine-namespace.md)).
Interfaces is an implicit grouping namespace; CLI, MCP, demo, project and Python
retain their existing owners. Active CLI/MCP initializers and descendant entrypoints
remain. Parent package introspection changes; external discovery compatibility and
EE wheel discovery remain UNKNOWN ([Amendment 169](https://github.com/rapiddweller/datamimic/blob/384b7723d950d8b312b1080d23ffd89a5343c9b0/docs/architecture/refactoring-study/experiment-2/amendment-169-interfaces-namespace.md)).

## Authoring and Errors adoption — 2026-10-18

The active Authoring/Errors target is amended by [the migration contract](../../migrations/authoring-errors.md). It replaces the persisted CE Intent/Scaffold contract with DM JSON, transaction-scoped Build expectations and persisted XML. Python becomes >=3.11. Existing CE parser, Runtime and IO owners stay in place. Application consumes typed ports; bootstrap alone selects CE adapters. Complete capture, acceptance, optional export smoke and requested full replay remain separate required proofs. The current tree below and the exact mounted declarations encode this target; historical baseline reviews remain unchanged.

The implemented promotion retains six Authoring owners: API/bootstrap, Domain, Application,
Ports, Projection and Adapters. Schema assembly belongs to Application because it coordinates
the descriptor port; Projection receives facts and gains no Ports dependency. IO client
ownership includes `io/failures.py`; only `io.api` exposes its transport normalization.
The pure DSL metadata contract is public without loading execution implementations.
Errors publishes exact `descriptor_scope`, `get_descriptor_name` and `get_issue_definition`
operations for logical error identity and catalog lookup; their existing owners remain unchanged.
Python 3.11 replaces `_compat`; old Intent/Scaffold owners and their public grants retire.

The recursive inventory retains the historical source commit and records 59 new modules and
14 retired targets for this adoption. Large Domain, adapter and error-catalog leaves were
reviewed: they contain named DTO, execution, or issue-family owners; arbitrary new grouping
would add navigation without removing a responsibility. Exact layout and module declarations
remain enforced, including nonempty negative controls. This inventory is structural coverage,
not completed runtime or external-service verification.

### Contained descriptor resources — 2026-10-18

Approved before implementation: DSL input owns `ResourceReader` (`Path -> bytes`),
`read_resource_bytes`, `resource_reader_scope` and `resource_reader_active`, exposed through
`dsl.api` and exact pure input operations for IO readers.
Normal execution retains `Path.read_bytes`. Authoring binds its existing secure workspace
reader around validation and private-child execution. XML, properties and IO file/chunk
readers use this boundary, including paths resolved after property substitution; scoped reads
bypass process-global resource caches. The reader owns no IO or Authoring imports. Existing
IO-to-DSL and Authoring-to-DSL dependencies suffice; no new component or dependency grant.
This closes the observed eager-properties and substituted-source escape paths without
claiming that arbitrary descriptor Python becomes sandboxed.

Installed Domain datasets retain a separate narrow read invariant: IO Files publishes
`packaged_dataset_scope(path, package_root)` for the exact caller-owned installed data
root. Domain obtains that root from its existing package-location calculation and wraps
its existing FileUtil calls. Environment-selected and custom paths keep the active workspace
reader. This preserves packaged generators without granting arbitrary outside reads or adding
a Domain-to-DSL dependency; dataset root semantics remain with Domain and reading with IO.
Domain also publishes `configured_dataset_overrides` through its existing API. Bounded
execution rejects inherited DATAMIMIC_ROOT/DATAMIMIC_DOMAIN_DATA before catalog/runtime
reads; normal execution retains those settings. The variable-name facts stay with Domain.

### Native boundary corrections — 2026-10-18

Root Authoring publishes named request/result DTOs and keeps internal bounded execution
requests and full captures private. Its schema returns and registry-validated DM JSON scalar
property maps have exact wire-position permissions. Five named constructor protocols remain
typed composition inputs. In-memory parser properties retain the same exact native map
contract as file parsing. No general map or opaque-value permission is introduced.

Native construct checks retain all prohibitions except two explicit single-construct cases:
`parse_literal_values` preserves the foreign `ast.literal_eval` result needed by existing
CE literal modes; `_validated_worker_success` and `_decode_worker_message` inspect complete
pickle state so forged extra fields cannot disappear before validation. Other `Any` or
reflective constructs in those functions remain prohibited. Vendor-cause normalization stays
with IO Clients; exporter-cause normalization stays with IO Exporters, removing the reverse
client-to-exporter dependency. [Amendment 214](../refactoring-study/experiment-2/amendment-214-ce-authoring-measurements.md)
records the historical adoption ceilings. [Amendment 215](../refactoring-study/experiment-2/amendment-215-current-base-reader.md)
records the current-base semantic union and reviewed reader control.
[Amendment 216](../refactoring-study/experiment-2/amendment-216-windows-snapshot.md) binds the Windows
snapshot correction and exact tightened call ceiling; UNKNOWN remains explicit.

## Physical target

```text
<edition>/
  __init__.py                    inert package initializer
  randomness.py                  shared RNG protocol and weighted-index primitive
  interfaces/
    cli/                        inert package, executable startup, command registration, presentation
    mcp/                        inert package, executable startup, optional typed tool transport
    python/                     DataMimic, test harness, factory entry points
      datamimic.py  data_mimic_test.py  factory.py
    demo.py  project.py
    bundle/                     deterministic archives of public CE contracts
  authoring/
    __init__.py  bootstrap.py    pure public entry and lazy adapter composition
    ports.py                    named typed adapter protocols
    domain/                     DM JSON, requests/results, capabilities, diagnostics, expectations
      acceptance_contract.py  acceptance_evaluation.py  capture.py  proof.py
      build_verification.py  row_conditions.py  environment_bindings.py
      rules/                    retained raw XML schema, semantic and cross-statement checks
    application/                app, compile/decompile use cases, Build and raw XML transactions
      schema.py                 actual DTO/codec schema assembly through ports
    adapters/                   codec, catalog, validator, policy, workspace and bounded child execution
    projection/                 pure acceptance facts and response evidence samples
  engine/
    dsl/
      api.py
      vocabulary/
        constants/  enums/      canonical names and closed values
        source_capabilities.py  source-format and source-mode facts
        contracts/              pure content and bounded-execution metadata
        product_identity.py  value_literals.py  shared capture/literal conventions
      model/
        validation.py  constraints/  flow/  values/  setup/  generation/
        setup/generators/       named and stateful generator definitions
        registry.py             schema facts, never parser implementations
      parsers/
        base/  flow/  values/  setup/  generation/  document/  input/
          properties.py  target.py  xml.py
        registry.py             concrete bindings, composed by DescriptorParser
      statements/
        base/  flow/  values/  setup/  generation/  traversal.py
    runtime/
      api.py  contracts.py
      lifecycle/                invocation, configuration loading, cleanup
      logging.py  process_titles.py
      contexts/                 execution state, row/iteration scope
      storage/                  run-local store handles and lifecycle
      scripting/                expression evaluation, seeded expression globals, read-only script helpers
        plugins/                only real extension implementations
      tasks/
        base/                   task protocols, shared count resolution and dispatch
        registry.py             ordered bindings, loaded once by tasks/__init__.py
        setup/                  ordered descriptor/client/store/generator/state-machine declarations
        flow/
          branches/  loops/  commands/
        values/
          key_variable_task.py  scalar/  structured/  reference/task.py  variable/{task.py, iterator.py}
          construction/{converters.py, entity.py, entity_constructor.py, factory.py, global_increment.py, sequence_table.py}
        sources/                generate.py, length.py, nested.py, reference.py,
                                variable.py, chunk_source_reader.py; statement/context-to-IO adaptation
        generate/
          task.py  export_order.py
          workers/              selected execution strategy
          policies/             capability-based concurrency reduction; no services wrapper
    io/
      api.py  contracts.py
      failures.py               IO-client-owned vendor cause normalization for transport
      memstore.py               raw mutable rows, aggregation and injected-client reconciliation
      clients/                  connections, transport and vendor details
      connection_config/        typed connector settings
      data_sources/             read/count/selection/pagination policy
      files/                    narrow dataset API, readers and cache
      exporters/
        core/  formats/  database/  diagnostics/
        registry.py             exporter construction from target strings
        session.py              worker registration and page dispatch
        lifecycle.py            chunk finalization, artifact publication and temporary-file cleanup
  domains/
    api.py  facade.py
    registry/                   entity/generator discovery and request validation
    domain_core/
      contracts/                schema and domain value types, not executable entities
      datasets/                 neutral path/inventory primitives, no shared generators
      runtime/                  RNG, seed, clock and deterministic primitives
      base_entity.py  base_domain_generator.py  base_literal_generator.py
      base_domain_service.py  property_cache.py
    shared/
      models/  services/  generators/
      datasets/                 locale/profile lookup and dataset loading
      demographics/             profile policy and sampling
      literal_generators/
        numeric/  primitives/  temporal/  person/  contact/  business/
        identity/               codes/, keys/, security/
      converters/
        base/  text/  temporal/  privacy/  structural/
    finance/                    contracts.py, models/, generators/, services/; luhn.py remains local
    healthcare/                 models/, generators/, services/
    insurance/                  models/, generators/, services/
    ecommerce/                  models/, generators/, services/
    public_sector/              models/, generators/, services/
  errors/
    base.py  codes.py  factory.py  formatters.py
    catalog/
  resources/
    api.py  demos/  examples/
```

DSL `flow/` uses the same branches/loops/commands families; DSL `values/`
uses scalar/structured/references/variables families. These are grouping names,
not a new DSL vocabulary. Keep model, parsing and statement layers separate.
Exporters has seven deliberate owners: shared primitives, three output families,
construction, worker page dispatch and completion. Session and lifecycle use
registry independently; another grouping would add no boundary (amendment 86).
IO retains eight distinct owners after separating the mutable Memstore from
exporters. Runtime owns store registration/lifecycle; IO Memstore owns raw rows,
aggregation and its existing caller-supplied client reconciliation. Generic source
loading, paging and cyclic selection stay in IO/data_sources. The empty nominal
Exporter marker lives in IO contracts to avoid a storage/exporter cycle.
[Amendment 168](../refactoring-study/experiment-2/amendment-168-memstore-data-owner.md)
records the exact no-shim move, changed Python module/serialization paths and
separate behavior/worker acceptance. No old defining-module alias is retained.
Every existing CE source scope, including namespace folders and initializer-only
code, has a review entry; exact module moves take precedence over package moves.
Unchanged leaf modules stay with their reviewed owner. Non-Python datasets keep
their resource paths unless an independently verified packaging migration requires a move.

Seven children is a review trigger, not a correctness law. The exact retained
groups and reasons are in `structure-review.json`. Domains keeps its real
facade beside registry and API; ordered setup declarations remain together.
Adding a wrapper solely to reduce a count would make navigation worse.

## Lifecycle and boundaries

```mermaid
flowchart LR
  CLI["CLI / Python"] --> RA["Runtime API"]
  MCP["MCP / authoring CLI"] --> AA["Authoring API"]
  AA --> APP["Application"]
  APP --> AD["Adapters"]
  APP --> PR["Derived projections"]
  PR --> IF["Canonical intent facts"]
  AD --> DF["DSL / domain facts"]
  AD -->|"bounded run / capability facts"| RA
  RA --> LIFE["Lifecycle"]
  LIFE --> PARSE["DSL parse → typed statements"]
  LIFE --> SETUP["Setup"]
  SETUP --> TASKS["Task dispatch"]
  TASKS --> GEN["Generate: policy → worker → rows"]
  GEN --> READ["IO source operations"]
  GEN --> DOMAIN["Domain generators"]
  GEN --> WRITE["IO exporter operations"]
  WRITE --> RESULT["Result / typed error"]
```

This is declared lifecycle intent, not proof of runtime call order.
Full run, bounded dry-run and factory execution share Runtime operations.
CLI and MCP translate/present requests; they do not repeat application policy.
MCP's bounded run is not permission to execute an unrestricted CLI run.

| Boundary | Owns / exposes | Must not do |
|---|---|---|
| DSL | Element metadata, validation, parsing and typed statements; parser binding belongs to parsers | Execute tasks, connect clients, import Authoring |
| Runtime | Typed run/session request and result; lifecycle starts Setup, Generate chooses workers | Implement connector or exporter internals |
| IO | Typed source/count/registration/write operations; IO owns concrete clients/exporters | Read Runtime context or interpret task statements |
| Domains | Typed entity/generator/converter capabilities and deterministic primitives | Import Runtime; core must not import shared implementations |
| Authoring | DM JSON, Build expectations and compile/lint/verify operations; adapters gather runtime facts | Duplicate DSL facts or let pure projection import Runtime |
| Errors | Stable codes/types/catalog/formatting | Own validation policy, runtime settings or import IO clients |
| Interfaces | Command/tool/Python adaptation | Become a second workflow engine |

Types live with their semantic owner. No global `types/`, `models/`,
`services/` or `utils/` catch-all. A public interface may be an existing typed
function or class; it does not require a new wrapper module. Nested public lists
are local to their boundary and do not automatically publish through the parent.
Concrete model and statement types are legitimate internal interfaces; concrete
clients and exporter implementations are not the Runtime-facing API.

The DSL pre-validation boundary is accepted for the bounded local slice. It
accepts raw `dict[str, object]` attributes and returns the same dictionary;
constraint facts remain closed
types. ArchKeel 0.8.5 can express the outer dictionary and depth-1 opaque-value
allowances at its eight input/return positions. Local bounded acceptance
removed eight findings (103 -> 95), with no added or changed remaining finding;
150 counted UNKNOWN remain, including lazy-supplier evidence. Opaque-value
acceptance does not prove type closure. This slice passes, but whole-goal
acceptance remains open.
([Amendment 91](../refactoring-study/experiment-2/amendment-91.md),
[ArchKeel #253](https://github.com/rapiddweller/archkeel/issues/253)).
Typed model construction still decides descriptor validity.

Authoring Domain owns acceptance and replay verdicts, full captures in `capture.py`,
and public evidence in `proof.py`/`requests.py`. Application sequences runs through
typed ports; bounded execution produces evidence. Policies never import the execution
adapter. The current exact Domain inventory is reviewed for cohesion; it replaces
the earlier eight-child exception in Amendment 80.

The IO facade drops five unused concrete exporter re-exports; live runtime
consumers still use its Memstore and TestResultExporter types.
File readers own JSON shape classification internally; sibling source consumers
use the published row-loading operation. The exporter registry's Memstore
dependency is declared at IO-MEMSTORE.
File readers are published through `engine.io.files.api`, not the Runtime-facing
root facade. Removing its documented `FileUtil` import is a deliberate CE 5.0
Python import break, without a shim ([Amendment 81](https://github.com/rapiddweller/datamimic/blob/384b7723d950d8b312b1080d23ffd89a5343c9b0/docs/architecture/refactoring-study/experiment-2/amendment-81.md)).
Open reader values remain unchanged; the file facade is not yet covered by the
root boundary-type rule. Fewer root findings do not prove better reader typing.
Exporter sessions call the registry only to construct target exporters; target
construction has no dependency on session state.
The parent IO facade does not publish registry, exporter config, worker state,
buffered implementation, or exporter-list construction; those remain at their
owning modules. Runtime's crossing operation is `ExportSession`.
Runtime source-selection operations cross into IO through `io.api`; the
selection algorithms remain owned by IO data sources.
For SQL statements, Runtime selects the configured target and IO invokes it
through the `SqlScriptClient` capability. Do not restrict injected clients to
`RdbmsClient` or probe the capability before calling it; preserve one direct
method lookup and the method's native failure behavior.
Target-call syntax is parsed by DSL input code. The linter adapter supplies
buffered exporter names to its rule context; pure authoring rules do not import IO.

## Changes that need more than a file move

- Dissolve `tasks/task_util.py`: dispatch uses the existing registry; evaluation
  goes to Scripting; converter binding stays with value construction; Generate
  owns page ordering, IO owns exporter setup/write/serialization.
- Dissolve `ExporterUtil`: the IO registry exposes the actual construction and
  consumption functions. Drop its unused serializer and path-check helpers;
  keep the live JSON encoder and XML-row conversion at their owners.
- Split source expression/context adaptation from IO read/count/selection policy.
  Preserve read, template evaluation and seed timing; never pass Runtime context
  or a closure over it into IO.
- Move the pure `source=` capability catalog from model constraints into DSL
  vocabulary. IO may consume those facts without depending on model validation.
- Move the neutral dataset path/inventory primitive below `domain_core`.
  Remove the current `domain_core → shared` permission; do not replace it with
  an injection framework or a reverse facade.
- Move ordered task bindings into `tasks/registry.py`. Retain one explicit import
  in `tasks/__init__.py`: cold multiprocessing/Ray workers enter below Lifecycle.
  Dispatch primitives do not import concrete task implementations. Parser registry
  composition instead belongs to DescriptorParser.
- Keep lazy domain entities distinct from passive types: services compose entities
  and generators; entity properties may use generators, never the reverse.
  Move shared `DemographicConfig` to `shared/demographics/config.py` so generators
  do not import the entity-model layer. Model ownership is a narrow exception for
  cached properties whose extraction would change observable lazy reads or RNG
  order; generators own independent rules over resolved inputs. Preserve public
  getter/access and RNG order. The current exceptions are:
  - `Order.discount_amount` draws eligibility before resolving `product_list` and
    prices, then draws the discount rate.
  - `EducationalInstitution.founding_year` reads the reference year first and
    conditionally reads the public `type` property for its age range; keep that
    lazy access at the property rather than pre-resolving it as generator input.
  - `MedicalDevice.specifications` draws common values before lazy `device_type`
    access, then interleaves type-specific draws with generator helpers.
  - `MedicalProcedure.cost` is already model-owned because its cached calculation
    reads other lazy clinical properties between RNG draws.
  These cases do not grant general permission for models to generate independent
  values; any additional exception needs its own evidence and target decision.
- `IncludeTask` stays with Setup because it executes an included descriptor's Setup;
  putting it under Flow would introduce a reverse orchestration dependency.
- Drop Generate's empty `services/` wrapper. Policies sit directly beside workers;
  the EE policy implementations use the same owner.
- Move EE vendor-error mapping behind IO. `errors/` receives structured facts,
  not an import of the client SQL identifier parser.
- Retain grammar definitions at their typed owners. Split EE DSL contract
  models, parser binding, runtime reflection and bundle assembly by ownership.
- Keep validation semantics in DSL. `ModelUtil` is public only inside the
  DSL-model boundary for sibling models; it is not part of the parent DSL
  contract or `dsl.api`. Publish only the named validation functions needed by
  Authoring through `dsl.api`. Raw XML attributes remain an open mapping until
  model validation; do not present them as already validated DTOs.
- Treat the CE count-bound comparison bug as a separate behavior change. Do
  not fold the EE correction into a structural move before Alt/Neu descriptor
  results and the invalid-input behavior are reviewed.
- Narrow current IO/Runtime facades: a renamed concrete class is not a typed
  operation boundary. Existing root type findings remain visible.
- Keep Runtime source adapters split by operation: generate loading, source
  length, nested-key loading/finalization and reference selection. These modules
  adapt statements and context; source algorithms remain in IO/data_sources.
- `errors/context/` is still deferred in CE by Amendment 18. Do not create an
  empty mirror of an EE feature that has no CE consumer.
- Public Python module paths move for 5.0 without shims. Keep installed CLI
  command behavior via entry-point configuration; migrate repository scripts
  and documented callers in the same implementation slice.

## Measurement and honesty

Published ArchKeel **0.9.0** revalidation supports recursive `inside` contracts. Mounted boundaries
declare complete assignment, explicit dependency directions, local interfaces
and component acyclicity. One root module-cycle rule covers deeper imports,
including `TYPE_CHECKING`; function-local imports do not erase a cycle.
Canonical `packages` selectors and `root_layout` rules describe the future
structure at every depth, including paths not created yet. The move map accounts
for each source from the frozen commit. Historical observations describe the old
structure; absent target paths and remaining old paths keep acceptance red.

Remaining limits are explicit:

- `root_layout` forbids unexpected children but does not require absent ones.
  Keep the existing physical-presence check and compare the move map at completion.
- ArchKeel 0.9.0 includes selected source initializers in nested ownership checks.
  Use `exact_modules` for a namespace's deliberate owner without claiming its
  descendants. Responsibility alone does not establish ownership or behavior.
  [Amendment 97](https://github.com/rapiddweller/datamimic/blob/384b7723d950d8b312b1080d23ffd89a5343c9b0/docs/architecture/refactoring-study/experiment-2/amendment-97.md) records five
  candidate owners: four can proceed, while Errors waits for a checker fix.
  Five other initializer decisions remain open.
- Static imports/types do not prove behavior, data-flow purity or dynamic loading.
  UNKNOWN is not PASS; narrow tests and source review remain necessary.
- A package can pass its contract while a large function remains poorly factored.
  The operation-level splits above remain implementation acceptance work.

`make architecture-definition-check` validates the recursive definition and its
mapping, not current architecture conformance. `make architecture-check` remains
strict and is expected to fail until the source reaches this target.
Do not rewrite `known-violations.json` to absorb these newly exposed findings.
The definition commit precedes production moves; descriptor inputs remain frozen.

## Delivery sequence and acceptance

### S3G7 ownership amendment

PhoneNumberGenerator lives in `domains/shared/generators`; `domains/registry/generators.py`
owns the composed builtin inventory and capability projection. Process titles live
in `engine/runtime/process_titles.py` under Runtime Logging; the multiprocessing
worker keeps its local import. No legacy forwarding modules or descriptor edits.

### S3G10 IO-to-DSL imports

IO uses DSL vocabulary modules and input parsers directly; `dsl.api` remains the facade for external consumers.

### S3G13 Runtime internal boundaries

Contexts use the public script execution operation; task families share declared value-construction operations. `WhileTask` accepts the common subtask bases directly.
`Context` and `SetupContext` are public scripting classes, not DTOs.
Checked-in scripts rely on their class identity and client lookup. Type closed
state precisely; review dynamic positions individually. Do not wrap or remove
these exports merely to satisfy the type gate.

### S3G14 IO interface cleanup

The facade drops unused concrete exporter re-exports. JSON shape guards become
named reader operations, and the exporter registry declares its Memstore dependency.

### S3G15 Runtime-to-IO selection facade

Runtime callers use the IO facade for seeded unique and distributed selection;
selection behavior and generic signatures remain owned by IO data sources.

### S3G16 Domain service API

Publish the shared entity services, their `BaseDomainService` return contract, and demographic config through `domains.api`;
the six examples and affected shared-service snippets use that surface. The EE
checkout at `dc7526592` has the same five service owner paths under
`domains/shared/services`, but no `domains/api.py`; parity is not yet claimed.

Standalone deterministic JSON address, person, doctor, and patient use cases
live under `domains/{shared,healthcare}/use_cases`; `services` remains for
registered entity services. The former `services.*_api` import paths are
intentionally removed without shims. The move does not edit XML descriptors or DSL code.

The versioned locale bundle stays in `shared/datasets`: all four JSON use cases
use the same supported-dataset intersection and eager validation. Healthcare
use cases own the generated doctor/patient records, not a second loader.

Domain model types returned by published `BaseDomainService[T]` services are
internal boundary promises. Shared Address, City, Company, Country, and Person
are exact class entries, not whole-module grants. The pinned ArchKeel commit
includes the inherited-generic proof from [#204](https://github.com/rapiddweller/archkeel/issues/204).

### S3G17 Model constraint extension boundary

The model registry reads the canonical `Constraint` and `element_constraints`
projection, and coordinates extension constraint registration atomically with
element structure. The constraints registry exposes per-tag mutation operations
for this internal SPI; atomicity remains owned by the model registry. No
`dsl.api` re-export is added.

### S3G18 Runtime-backed reference adapter

Reference and capability rendering lives in `authoring/adapters/reference.py`
because it combines live Runtime capabilities with DSL and domain facts. The
typed intent-reference projection stays runtime-free.

1. Freeze the target definition and record baseline/tool findings separately.
2. Implement CE slices: neutral primitives and errors; DSL families; IO boundaries;
   Runtime task composition; Authoring/projection; entry points and packaging.
3. Each slice: Luna implementation and independent Terra QA, root review, targeted positive
   and negative cases, unchanged-descriptor oracle, Ruff and full-package MyPy.
   Consult Astra for unresolved technical judgment; Alex decides product conflicts.
   Check shared behavior against the frozen EE implementation before changing CE
   semantics. CE output preservation alone does not establish EE semantic alignment.
4. Final CE gate: every target path reached, no unowned modules, no forbidden/private
   crossings, no executable import cycles, zero violations and independently
   assessed remaining UNKNOWNs. Use the agreed ordinary unit, integration,
   functional and available-service suites; record skipped or unavailable vendor
   cases explicitly. This bounded acceptance does not prove every descriptor/backend.
   Preserve seeded values within CE with identical initial resources/targets;
   unseeded runs retain outcome, counts/declared ranges and structure.
5. Apply the same physical map to EE with its existing, stronger tests intact.
   Keep EE-only policies/connectors/native implementation below their owners.
   CE and EE need not produce the same seeded values.
6. Report structure, behavior and delivery separately. Full EE leaf review and
   cross-edition descriptor execution are not implied by this CE definition.

The 2026-10-18 migration decision adopts transaction-scoped DM JSON and Build in CE.
The frozen EE implementation supplies shared semantics; CE registry vocabulary and
execution remain authoritative. Unsupported EE capabilities are not advertised.

The Python composition boundary publishes exactly the five existing Authoring Port
protocols at `authoring.ports`; the public application constructor accepts them.
Internal bounded capture request/evidence DTOs are not published. Exporter Core
publishes its existing `ExporterError` to the sibling Lifecycle transport normalizer;
the exception remains internal to IO. These declarations add no dependency edge or
boundary-rule exclusion.
