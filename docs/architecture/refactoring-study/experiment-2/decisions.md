# Experiment 2 decision log

## D1 — `services` is deleted

**FACT:** `datamimic_ce/services` contains only `source_script_evaluator.py`.

**Decision:** move template evaluation to `engine.runtime.evaluation`; do not create a replacement
service layer.

## D2 — Authoring projects owner facts

**FACT:** the element registry, Pydantic models, constraints, generators, exporters, and domain
registries already own the executable facts.

**Decision:** Authoring owns intent and projection. It does not maintain a second DSL or capability
catalog. Bounded execution crosses `engine.runtime.api` only.

## D3 — types are local

**Decision:** each component owns its contracts. There is no shared `types`, `models`, `common`, or
`foundation` package. Cross-component signatures expose types from the owning component's
`contracts.py`.

## D4 — public APIs are per component

**Decision:** architecture components expose `api.py` and `contracts.py`; ordinary subpackages do
not get ceremonial facades. External Python compatibility paths remain where documentation proves
they are public.

## D5 — `domains` remains top-level

**FACT:** README and developer documentation import domain services and models directly.

**Decision:** keep `domains` as a first-class public component. Moving it under `engine` would add a
large compatibility layer without making its ownership clearer.

## D6 — domain datasets use a narrow IO facet

**FACT:** 29 domain modules load packaged CSV or JSON datasets. Parsing and caching those files is
IO behavior; the dataset contents and selection logic belong to `domains`.

**Decision:** allow `domains` to depend on `io` only through `engine.io.dataset_api`, which exposes
file loading and caching but no database client. Keep domain-specific paths, fallback, weighting,
and selection in `domains`. Do not add a shared foundation or duplicate the parsers.

## D7 — logging uses the standard library directly

**FACT:** all affected modules use the same named `logging.Logger` object. ArchKeel 0.6.0 resolves
methods on the former imported module variable but not on `logging.getLogger(...)` bindings.

**Decision:** remove the cross-component runtime logger dependency and use
`logging.getLogger("DATAMIMIC")` directly. Accept the resulting call-resolution measurement reset
as an analyzer limitation; do not rewrite ordinary logger calls as unidiomatic class-method calls.

## D8 — runtime consumes domain generators through a typed iterator

**FACT:** runtime needs the concrete generator classes because the DSL supports heterogeneous
constructor signatures. Exporting the existing registry dictionary would make that mutable,
untyped structure the component contract.

**Decision:** `domains.api` exposes declared generator classes and
`iter_generator_types() -> Iterator[type]`. Runtime builds its private name index from that
iterator. The registry dictionary remains an internal domain implementation detail.

## D9 — capability facts stay with their executable owners

**FACT:** generator classes already define the names and constructor parameters shown by the
Authoring reference. Package scanning duplicates component discovery and crosses internal module
boundaries.

**Decision:** the DSL owns the typed `GeneratorCapability` projection. Domains and runtime publish
their own capabilities through typed APIs; Authoring only composes those projections.

## D10 — DSL statements contain no execution decisions

**FACT:** count expressions require a runtime context, count ranges consume the run RNG, and Mongo
upsert detection inspects live clients. None is descriptor structure.

**Decision:** DSL statements expose parsed values only. Runtime evaluates counts, selects ranges,
and inspects configured clients.

## D11 — connection objects belong to IO

**FACT:** `MongoDBStatement` constructed an unused client while parsing. Both database statements
also constructed IO-owned connection configs.

**Decision:** connection statements retain their validated DSL models. Runtime tasks construct the
IO configs and clients when setup executes; parsing has no connection-object side effects.

## D12 — properties are DSL input; environment selection is runtime policy

**FACT:** descriptor parsing needs companion property files, but choosing the runtime environment
depends on process configuration.

**Decision:** DSL owns property parsing and its per-path cache. Runtime selects the environment and
passes it into the parser explicitly. DSL does not import runtime or IO.

## D13 — IO accepts narrow owner contracts

**FACT:** exporters need read-only run context and clients need entity serialization, but neither
requires runtime task classes or concrete domain entities.

**Decision:** IO defines a structural read-only exporter context. DSL defines the nominal
`EntityValue` contract implemented by domain entities. IO imports neither runtime nor domains.

## D14 — runtime owns execution; interfaces adapt it

**FACT:** `DataMimic`, `DataMimicTest`, CLI, factory, and Authoring dry-run duplicated or reached
through parts of the parse-and-run lifecycle.

**Decision:** `engine.runtime` owns process setup, validation, parsing, task creation, execution,
and capture. `interfaces` exposes the compatibility-facing adapter. Boundary requests and results
use declared Pydantic root models; compatibility facades unwrap them to the existing dictionaries.
The wrappers use construction without validation so the existing dictionary identity and accepted
values remain unchanged.

## D15 — the DSL facade is the canonical cross-component vocabulary

**FACT:** runtime, Authoring, IO, and domains already consume DSL statements, enums, constants,
constraints, and parser facts directly from internal modules.

**Decision:** `engine.dsl.api` re-exports the exact cross-component vocabulary with object identity
preserved. Consumers import that facade instead of wrappers or duplicate types. DSL-internal
modules continue to import their owning implementations directly to avoid facade cycles.

## D16 — the domain facade exposes existing domain capabilities

**FACT:** runtime, Authoring, interfaces, and shipped resource scripts already use domain
generators, converters, entity registry facts, deterministic runtime helpers, and demographic
types.

**Decision:** `domains.api` exposes those existing cross-component names as identity re-exports,
plus its two facade-owned capability iterators. Domain internals do not import their own facade.

## D17 — IO owns smoke-export execution

**FACT:** Authoring inspected the private buffered-exporter registry, constructed exporter state,
and built a runtime `SetupContext` solely to test file serialization.

**Decision:** IO keeps the registry private and exposes one typed `smoke_export` operation.
Authoring projects supported names through `buffered_exporter_names()` and sends opaque rows and
parameters through IO-owned root contracts without validation or copying.

## D18 — runtime loads descriptor properties for transports

**FACT:** the CLI reached through IO only to load the descriptor's companion properties before
constructing a runtime request.

**Decision:** runtime exposes `load_descriptor_properties(Path) -> PlatformProperties`; transports
do not depend on IO. DSL remains the owner of property-file parsing and caching.
