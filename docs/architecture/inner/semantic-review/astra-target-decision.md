# Astra target decision

Status: **target decided; implementation and acceptance still pending**.

This decision supersedes the tentative ownership proposals in the four semantic
reviews. It resolves all 17 `unclear` entries. It does not rewrite the historical
773-entry baseline or certify the current layout.

[Machine-readable freeze inputs](astra-target-decisions.json) contain the exact
22 contract scopes, future package selectors, 488 source-module dispositions,
158 Python-directory concerns, boundary-type decisions, and implementation slices.
They are migration inputs, not a second live architecture contract.

## Authority and evidence

- CE source: `3b844b5083e5af89269ef917bc0614601d30cf61`.
- EE read-only evidence: `dc7526592073985ed69902b21d6a1c861ac02fa0`.
- Astra decides the target under Alex's delegation; root reviews application.
- EE leads shared boundary design. That does **not** authorize silent changes
  to CE descriptor results, error behavior, evaluation order or seed streams.
- The shared physical core convention applies to both editions. Edition-only
  behavior earns a real module; parity does not require empty placeholders.
  Do not import EE Rust or runtime-configuration infrastructure.

## Canonical contract, not a target projection

Freeze supported ArchKeel `packages` selectors at their **future physical
locations**. The pure target diagram reads these same selectors and concerns.
Do not add unsupported `target_packages`, a second selector map, or a heuristic
source-group-to-target projection.

Keep the old manifest and observation as historical **Ist**. While files have
not moved, missing target paths and unassigned old paths are pending/failing
migration evidence, not green architecture. Validate migration definitions
against the frozen source commit; validate the final physical set separately.

Root applies the exact selectors from the JSON to canonical contracts. From
then on those contracts are the live SPOT; this decision remains immutable
rationale. Package `root_layout` rules must cover all future scopes, not merely
their intersection with today's directories.

## Target concern tree

Names below are under `datamimic_ce`; EE substitutes its package prefix.
The JSON records Python concern directories and exact component selectors;
packaged data-only trees retain their existing owners.

```text
interfaces/     cli, mcp, demo, project, python/
                  datamimic.py, data_mimic_test.py, factory.py
authoring/      api.py, contracts.py, spec/, domain/, projection/,
                adapters/, application/
engine/
  dsl/          api.py, vocabulary/
    model/      validation.py, constraints/, registry.py
                setup/, generation/, flow/, values/
    parsers/    base/, registry.py, document/, input/
                setup/, generation/, flow/, values/
    statements/ base/, traversal.py
                setup/, generation/, flow/, values/
  runtime/      api.py, contracts.py, storage/, logging/, scripting/,
                lifecycle/, contexts/
    tasks/      base/, registry.py, setup/, flow/, sources/
      values/   key_variable_task.py, scalar/, structured/, references/,
                variables/, construction/
      generate/ task.py, export_order.py, workers/, policies/
  io/           api.py, contracts.py, clients/, connection_config/,
                files/, data_sources/, exporters/
    exporters/  core/, formats/, database/, memory/, diagnostics/,
                registry.py
domains/        api.py, facade.py, registry/, domain_core/, shared/,
                finance/, healthcare/, insurance/, ecommerce/, public_sector/
  shared/       models/, datasets/, generators/, services/,
                literal_generators/, converters/, demographics/
errors/         codes.py, base.py, catalog/, formatters.py, factory.py
resources/      api.py, demos/, examples/
_compat.py      existing interpreter compatibility, not legacy import shims
randomness.py   existing RandomSource contract and cumulated-index primitive
```

Each DSL `flow` retains branches, loops and commands. Each `values` retains
scalar, structured, reference and variable responsibilities. Domains retain
their existing useful family subdivisions. The exact names/files in the JSON,
not this compact view, define the migration inventory. Seven children triggers
a cohesion review; it is not a quota.

## Binding semantic decisions

| Decision | Final owner and invariant |
| --- | --- |
| Generator, StateMachine, Demographics declarations | DSL `setup` in all three layers; runtime definition tasks in `tasks/setup`. Setup executes document order, not an eager declaration pre-pass. |
| KeyVariableTask / ElementModel | Shared value base directly under runtime `values`; Element grammar remains a real scalar model. Delete the artificial model/base grouping, not ElementModel. |
| Flow / Execute | Keep command and branch aggregates. Execute retains nested-row variables and root namespace behavior. Inheritance does not make it setup-only. |
| Source policy | IO/data_sources owns dispatch, count/read/page, distribution, uniqueness, cyclic windows and cached pools. Runtime resolves context, expressions, defaults, statement identity and seed into typed IO requests. No Context or Statement enters IO. This reverses the assessment's tentative Runtime-selection conclusion. |
| GlobalIncrement | Generator in Runtime `values/construction/global_increment.py`; existing counter registry in `storage/global_increment.py`. Context and generator both depend on storage, never Context → tasks. Preserve DSL name and behavior. |
| Neutral types | EntityValue is the IO serialization ABC, so moves to `engine/io/contracts.py`. StateTransitionRule and GeneratorCapability move to Domain core generation contracts; generator signature metadata to Domains registry. DSL uses the same plain transition tuple shape without importing Domains. Keep executable BaseEntity at `domain_core/base_entity.py`. |
| Randomness primitive | Merge existing RandomSource and cumulated_index into root `randomness.py`, below Domains, IO and Runtime. IO selection otherwise creates an IO → Domains → IO cycle. No wrappers or duplicated sampling math; remove old Domains API exports and migrate callers. |
| StatementUtil | Consumer grammar stays DSL; scalar source-entity fallback goes IO/data_sources; target metadata/routing goes IO/exporters. Preserve Mongo's different fallback and file naming. |
| Parser composition | Concrete registry above base dispatch; document orchestration above low-level `input/xml.py` and `input/properties.py`. Task composition likewise lives in a real registry module. |
| TaskUtil | Delete forwarding. Preserve boolean condition rejection in scripting; converter construction in values; dependency-sensitive export order in Generate; serialization/write routing in IO. |
| Authoring | Keep public CompilePlan in contracts; contracts/spec/domain remain one semantic domain aggregate because DTOs and rules are mutually related. Retain derived_facts in Domain: both DM408 and application results consume its semantic facts. The initial projection assignment was wrong and would create a cycle. No DTO copy, wrapper or duplicated derivation; preserve edition semantics. |
| Interfaces | Delete forwarding api/contracts/factory_config modules, updating every consumer. The Python test factory is one `factory.py`, not a one-file folder. Keep the behavior-bearing Domains facade at `domains/facade.py`. |
| Domains / resources | Keep coherent aggregates. DbUnit is a file-format exporter. Examples become runnable packaged resources, not a new demo registry/API. Root errors remain stable. |

### Credentials: structural correction without a semantic rewrite

IO owns credential profile filesystem loading. Runtime document composition
supplies a typed **on-demand** loader to parsing; `parsers/base/client_config.py`
owns the pure attribute merge below concrete setup parsers. The IO loader may
reuse `parsers/input/properties.py`, not concrete DSL parsers. This avoids a
base/setup cycle and is an actual dependency inversion, not a pass-through service.

Preserve CE's current conditional lookup, timing and mutable property state:
load only when environment/system require it; preserve descriptor directory →
cwd → home/datamimic fallback, truthy `env_props` alias/update behavior,
environment-over-descriptor precedence and sequential static-property includes.
Do not eagerly read every profile.

Implementation review: pass the loader only through known built-in parse paths;
custom-tag extension signatures stay unchanged. Preserve the current nested
parsers' default production environment rather than silently propagating the
outer environment as an unrelated fix.

EE's descriptor-over-environment precedence is a separately recorded semantic
alignment opportunity. It does not block or belong inside this structural
migration. Conflicting-credential fixtures must prove the unchanged CE winner.

### Two real cycle remedies

Registry follow-up: `DescriptorParser` composes the parser registry explicitly;
private parser-dispatch tests initialize that registry without weakening their
assertions. Runtime keeps a meaningful `tasks/__init__.py` that imports its
registry once: multiprocessing and Ray workers enter below the lifecycle runner.
This is package composition, not an old-name facade. Children must import explicit
leaf modules, never the initializer. Move ordered bindings unchanged; add no
initialization flag or per-run refresh. Prove cold spawned-worker and Ray entry.

1. **Statements:** high-level `statements/traversal.py` owns Generate/Condition
   traversal. Common Statement/CompositeStatement no longer import or type their
   specialized descendants. Preserve executed-branch set iteration, registration,
   descendant lookup, include order and existing failure behavior.
2. **Contexts:** co-locate Context and SetupContext in `contexts/context.py`
   as a closed execution-context hierarchy. Keep both classes visible in the
   diagram. This approximately 800-line unit is a deliberate cohesion tradeoff,
   not claimed decoupling. Separately parameterize expression globals with
   explicit seeded dependencies and a lazy Faker supplier. Preserve unseeded
   short-circuit behavior and exact RNG draws. Do not add a 53-property protocol.

Both remedies must remove real dependency cycles, not hide them under
`TYPE_CHECKING`. Review retained file size and cohesion during implementation.

### Boundary types and packaging

The historical observation has **30 raw boundary positions**, not 30 independent
architectural failures. The JSON names each exact position and disposition.
Path, datetime, Random, Traversable, strict Pydantic values, lxml trees and JSON
Schema values remain their actual types. Allow only reviewed positions; no
whole-API waiver and no string coercion to satisfy the checker.

Astra corrected D18 after tracing the constructors: subclasses do not share
`BaseDomainService`'s constructor signature. Rename the existing lookup to
`get_entity_service_factory`, retaining `Callable[..., BaseDomainService] | None`;
this is an explicitly dynamic DSL constructor boundary, not argument-type proof.
Class discovery remains `EntitySpec.service_cls: type[BaseDomainService]`.
Do not add a local callable alias, wrapper or private Runtime-to-Domains import.
Explicit DSL keywords must still reach the concrete constructor unchanged.
Model-class discovery and zero-argument constraint suppliers are intentional.
Deleted interface forwarders need no surviving allowances.

Moving dataset/schema loaders breaks `__file__`-relative assumptions unless
resource lookup is repaired. Keep packaged data ownership stable and resolve
it from a stable package resource location, retaining explicit overrides and
fallback policy. An installed-wheel domain generation and schema-validation
check is mandatory; a checkout-only test can miss this failure.

New grouping folders can be namespace packages under the existing packaging
configuration. Do not manufacture empty `__init__.py` files for the report.
Keep meaningful initialization. Astra corrected the proposed dotenv relocation:
retain root `load_dotenv()` unchanged, once per normal package import with
`override=False`. MCP reads defaults during import; standalone Domains also
consume environment settings without Runtime. Moving this call changes timing
and caller-relative `.env` lookup. Runtime `Settings` retains its separate cwd
file lookup. No bootstrap wrapper or new initialization flag is needed.

## Dependency direction

- Interfaces call Authoring or Runtime; they do not own their workflows.
- Authoring application coordinates its contracts/domain/projections/adapters.
- Runtime executes DSL statements and calls IO/Domain operations.
- IO accepts resolved typed inputs; no Runtime context or DSL statement imports.
- Domains depend on core, IO serialization/dataset contracts and canonical DSL
  vocabulary leaves, not Runtime or high-level DSL parsing/model/statement APIs.
  Lazy models may call generators; generators must not call models/services.
- Registry/composition modules depend on implementations, never the reverse.
- Domains, IO and Runtime may use the neutral randomness leaf; it imports none
  of them. Seed lifecycle and business generation do not move into it.
- Stable errors are low-level. Vendor error translation remains with IO.

Source extraction must stage **read → Runtime evaluation → IO selection**.
Eagerly preparing every seed changes the random stream. The IO chunk pool owns
selection and retained page order; Runtime coordinates loading, template
evaluation and the subsequent seed request. No callback may smuggle Context or
Statement into IO. A three-method `MemstoreSource` protocol in IO contracts
avoids a data-sources/exporters cycle without a wrapper.

Preserve different source precedence: Generate/count use file → memstore →
client; Variable uses weighted → selector → file → client → memstore. Preserve
CSV/JSON/XML's different template/error handling, unknown counts, deferred
iteration selectors and existing DbUnit offset behavior. These are behavioral
constraints, not permission to standardize the implementations during the move.

A vocabulary enum used to express IO or Domain policy is not a Statement
dependency. Import its canonical leaf, not the high DSL facade. IO credential
loading may reuse the low-level property-input reader. Do not duplicate enums
or property syntax solely to remove those narrow dependencies.

## Implementation and measurable acceptance

Apply slices in dependency order; keep each independently reviewable:

1. **Freeze contracts/mapping:** all 17 unclear decisions resolved, 488 source
   modules accounted for exactly once, 22 future contract scopes. Definition
   checks and physical acceptance report distinct states.
2. **Moves/imports/resources:** no old-path aliases; exact target file inventory;
   migrate callers/docs/tests; build and install wheel; prove datasets, schemas
   and runnable examples work outside the checkout.
3. **DSL:** unchanged grammar/capability/schema baseline; positive and negative
   credentials, include, setup-order and traversal fixtures; no statement SCC.
4. **Runtime:** no context SCC; same seed stream/Faker laziness; global increment
   scope/reset, generator caching, state-machine instance isolation, nonbool
   rejection, nested Execute variables and parent/child export ordering.
5. **IO:** source-family counts/reads, ordered paging, shuffled pool load-once,
   unique/cyclic selection, variable modes, reference cycling and target routing;
   no Context/Statement boundary leakage. Exercise failure/exhaustion cases.
6. **Integration:** fresh structural observation, exact physical set, no stale
   imports or unauthorized edges, exact reviewed boundary exceptions, relevant
   full unit suite, full-package mypy, ruff and installed-wheel proof. Report
   unavailable external-database and remote-CI lanes separately.

Preserve the frozen behavioral oracle. A changed test expectation needs a
specific approved semantic decision; relocation alone is not one. No green
structural counter substitutes for these behavior and packaging gates.

LOCAL VERIFIED: source/contract inspection and decision-record consistency.
No runtime equivalence or completed migration is claimed.

CI-ONLY VERIFICATION: none performed for this decision record; implementation
must report local, external-service and remote-CI evidence separately.
