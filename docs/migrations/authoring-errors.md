# CE Authoring and Errors migration

This migration replaces CE Intent/Scaffold with the Build contract below. Tracks CE #270.
Baseline: CE `84a9f4657148bcfa0bc560908ed42b1d5fa3efab`;
semantic reference: EE `37d74ddb3553ca23597a1b9264649361fe68a233`.
Python becomes >=3.11, without an added upper bound. CE keeps SCM package versioning;
Build `4.0` is a protocol version. This migration does not authorize merge or release.

## Follow-up corrections

Parser and Execute user failures use catalog exceptions with logical locations.
Missing SQL clients, missing script files and failed Bash now raise `TaskConfigError`;
native causes remain attached where present. Bash emits the shared warning `W007`.
Under `<setup rngSeed>`, a `<execute>` Python script that draws entropy while it loads (a module-level call,
a default argument, an entropy import inside a function or class body) emits the shared warning `W008`
with the script name and line; nothing is rejected, and Build's deterministic replay stays the hard check.

Build and raw XML verification reject XML over 1,000,000 characters with a typed
`limit` diagnostic, rather than leaking an internal validation exception. Compile
alone still proves syntax and does not promise bounded execution.

For changes shared with EE, run the paired `test_bounded_descriptor_size.py` cases
and full-capture negatives in both editions. Keep registry/runtime adapters local.
CE roles, derived counts, caller requirements and replay/smoke remain explicit
edition differences; matching protocol labels do not make requests interchangeable.

### Build row limit (#426)

`build_request_v5.max_count` changes from `integer, default 10` to `integer or null,
default null`. The version stays `"5.0"`. Omit the field rather than send `null`:
CE before this change and EE reject `null`. When the field is omitted, Build derives
the limit from the declared total: literal counts, the literal count of a source, and
the producer rows of a memstore readback whose producer has a literal count and
no source; a nested literal count multiplies the bound of its parent (at least 10,
at most 1000). Every `<condition>` branch counts in full,
so the limit can be higher than a run. A product
without such a bound (a file source without count, a script count, a count range)
keeps the limit 10. An explicit `max_count` below the declared total is refused
before execution. Old files stay valid; a file that omitted `max_count` with more
than 10 declared rows was rejected and is now ready. `datamimic run` ignores
`max_count`, and the XML does not change. EE has no Build v5 yet; an EE port must
derive the limit the same way.

### Failed assert (#420)

A failed `<assert>` rejects Build with `assert_failed` at the assert line, keeps the
products that completed before it and lists the other checks as `not_executed`.
`assert_failed` echoes only a literal message: text without `{`, `}` or `__`, at most
200 characters. It is author text from the descriptor file, never a resolved value.
The `review_artifact` of a stopped run lists each workspace file that the run read
before the assert, with its digest, as a ready Build does. A changed source file
changes the artifact. A `<variable source>` of a product after the assert is not read
and not listed. Build counts the rows of a top-level `<generate source>` before the
run, so that file is listed also after the assert. An `<assert>` tag over several
lines reports its last line; the runtime and Build read the same line.

## Public contract

Persist XML as the executable project. `DmJsonDocumentV1` is an in-memory agent
representation of one XML file. Expectations and roles live in the project's
`acceptance/build.json`, beside the XML they prove. `ee_version`, `ee_error`, `EeErrorIdentity` become `ce_version`,
`ce_error`, `CeErrorIdentity`; producer and installed version identify CE.

| Old entry | Replacement / consumer | Verification to retain |
|---|---|---|
| `AuthoringSpecV1`, `authoring.spec`, `ScaffoldRequest/Result` | Project XML + `acceptance/build.json` (`BuildRequestV5`), discriminated Ready/Rejected | Counts, roles, nested FK, memstore readback, time series, decimal/constraints |
| Root `scaffold`, `authoring.api.scaffold` | `create_authoring_application().build` | Full capture acceptance; explicit caller requirements with origin |
| `api.check`, `api.run` | Application-owned lint and bounded execution through CE ports | Parser diagnostics, per-generate caps, timeout/cleanup |
| `api.capabilities`, `api.reference` | Application capabilities, typed lookup, reference, schema, document_schema | CE registry projections and exact running DTO schemas |
| CLI `scaffold`, top-level authoring commands | `datamimic authoring {version,schema,capabilities,capability,reference,compile,decompile,build,lint,dry-run,run,export-contract}` | File/stdin/JSON, exit codes and bounded limits |
| MCP scaffold/discovery/check/bounded-run tools | Build, Compile/Decompile and discovery over the same application DTOs | Optional installation, stdio purity and transport parity |
| `datamimic run`, Domain/demo/Python runtime API | Existing owner and command retained | Seeded output, resources and normal runtime behavior |
| `DomainError`, `InvalidLocaleError`, `DomainErrorCode` | Same CE identities plus portable catalog/factories | ValueError ancestry where present, to_dict/path/hash/hint/details/locale and pickle |

The Python facade publishes the application and factory; typed requests and results
live under `authoring.domain` and discovery methods belong to the application. CE Build adds typed `product_roles`,
origin-tagged `acceptance_requirements`, and `verification` options for smoke/replay.
Roles are proof input, never runtime XML attributes or a second stored model.

CE proof DTOs live in `authoring.domain`:
- `ProductRoleDeclaration(product, field, list_field, role)` carries discriminated
  identifier/FK/timestamp/value roles; FK retains parent product/field identity.
- `AcceptanceRequirement(expectation, origin)` carries model/caller/derived origin.
  Legacy derived count/range/allowed-values, per-parent and nested-list checks are
  exported explicitly, then checked against new projection; none may disappear.
- `BuildVerificationOptions(smoke_export=False, deterministic_replay=False)` and
  `BuildVerificationEvidence` retain distinct `not_requested`, `not_applicable`,
  `blocked`, `failed`, `passed` outcomes for each gate.
- Legacy `product + list_field + field` subjects map to explicit nested-list
  subjects; per-parent checks keep their root-row boundary and parent field.

Build rejects unknown role subjects, conflicting requirements and missing
mandatory count/relationship/readback proof. Optional fields cannot weaken those
checks. Decompile returns syntax only; it cannot invent the omitted role facts. It does not publish concrete adapters or
copy all EE exports. Ports are Codec, Catalog, Validator, BoundedPolicy, Executor;
bootstrap chooses implementations. Application never imports adapters. Domain and
Projection perform no filesystem or Runtime operations. Existing CE parser,
Runtime session and IO owners keep their paths.

## Transfer matrix

| Reference part | Decision | CE owner / reason |
|---|---|---|
| Authoring `__init__`, `bootstrap`, `application/{app,use_cases}`, `ports` | CE-adapt | Runtime-free facade, injected ports, CE composition |
| `domain/{common,dm_json,requests,diagnostics,document_identity,validation}` | CE-adapt | Typed CE identity and CE proof extensions; supported Pydantic APIs |
| `domain/{expectations,acceptance,acceptance_evaluation,acceptance_projection,row_conditions,parent_references}` | CE-adapt | Shared subjects plus retained nested-list/count/role/relationship protection |
| `domain/{capabilities,reference,rules}` and pure projections | CE-adapt | CE registry facts, diagnostics and discovery; no EE capability inventory |
| `domain/{environments,environment_bindings}` | CE-adapt | Existing CE connection profiles; only CE-supported clients |
| `domain/{spec,fields,products,sources,targets,plan,usage_examples}`, teaching model adapter | CE-adapt where needed | Internal teaching only; never restore a second public intent compiler |
| `adapters/dm_json_codec` | CE-adapt | CE model registry supplies kinds, aliases, properties, content and children |
| `adapters/{catalog,teaching_specs}` and teaching resources | CE-adapt | Curated CE examples only; codec compiles requested examples lazily |
| `adapters/{workspace,validator}` | CE-adapt | Symlink containment and in-memory CE parser; logical descriptor identity |
| Bounded policy/preflight/executor/runtime/child/diagnostic adapters | CE-adapt | CE session, memstore, profiles, exporters and process cleanup; preserve CE bounds |
| `local.py` | Obsolete for transfer | CE composition has one facade; no additional local API wrapper |
| Portable Errors base/context/contracts, codes, definitions, guidance, formatting/factories | CE-adapt | Preserve CE domain types; stable shared code numbers; logical locations |
| Parser/include/task/source/exporter/generator/condition/state-machine/operation warning catalogs | Adopt relevant entries | Only entries integrated into reachable CE paths; no unused catalog completion claim |
| Client/vendor fallbacks and expression diagnostics | CE-adapt relevant entries | Backend classification stays in IO; explicit portable facts enter Errors |
| Error docs generator | Obsolete for transfer | No new documentation framework; maintained CE migration/usage docs suffice |
| Redis/Rust/ML/Kafka/RabbitMQ-specific types, settings, teaching examples and catalogs | EE-only | No runtime import, published CE capability or blanket relicensing |
| Old CE compiler/spec/scaffold transports and repair guidance | Retire at cutover | One-time migration first; no runtime shim or second active compiler |

Copyright stays with Rapiddweller. Only the explicitly transferred scope receives
CE MIT wording. Other EE packages and data are not relicensed.

## Proof and bounded semantics

| Operation / fact | Meaning |
|---|---|
| Compile/decompile | Lossless supported syntax, deterministic normalization; no execution claim |
| Raw XML bounded run | Keep CE per-generate-instance capping, including nested/dynamic/ranged counts |
| Build | No Ready without required complete capture and acceptance, even with no explicit expectations |
| Samples | Bounded display only; sample length is not total count |
| Smoke requested | Same first full capture as acceptance; exercise actual CE exporter dialect/encoding/chunks/final counts |
| Replay requested | Exactly one additional complete capture; explicit seed; compare all rows/order/counts/products |
| Replay omitted | `not_requested`; never `passed` |
| Isolated external target | Captured evidence only; no external DB/write/readback or sandbox claim |
| Missing/mixed/scalar rows, bad count/provenance/completeness | Reject at child boundary before all consumers; do not filter rows |
| Timeout/crash/bad reply/cleanup failure | Separate typed failed evidence; terminate/reap descendants |

Read-only policy and target isolation apply recursively to loaded/includes too.
Fail closed when completeness or bounded eligibility is unproved. Never inject a
count into persisted XML just to obtain Ready. A passing smoke/replay cannot erase
another failed gate. CE before/after compares CE data semantics; CE/EE compares
shared language/contract semantics, without requiring identical random values.

CE and EE codecs preserve decoded Unicode and whitespace-only leaf text. CE raw
XML strings are Unicode; EE raw XML retains its established byte/declaration
contract. Shared issue codes remain stable; CE I825 omits generated values from
public error text.

Portable runtime diagnostics retain codes, logical descriptor identity and repair guidance.
They omit evaluated expressions, constructor arguments and automatic record dumps.
Explicit descriptor output and Python exception causes retain their contracts.

A constructor returning a non-Converter now raises `TaskConfigError` (`E013/I840`).
Callers that caught `TypeError` must catch the portable type. Native construction
failures remain available as causes.

Bounded resources use contained opened handles, including properties substitution
and cached file reads. Installed Domain datasets are read through their own loader;
custom `DATAMIMIC_DOMAIN_DATA`/`DATAMIMIC_ROOT` overrides reject bounded execution.
Connection profiles are workspace-local. Build and dry-run prove a project: the entry
descriptor plus its literal, setup-level include graph (`.xml` steps and `.properties`),
read from the workspace. Expectations and product roles address products of every file;
product names stay unique per project, clients belong to the entry, and memstore
producer facts span the whole graph. Property-expanded sources can still
hit the pre-existing static unknown-source lint rule; executor support alone does
not prove public Build eligibility.

Bounded SQL sources use a conservative query subset and backend read-only transactions
(PostgreSQL, MySQL, Oracle, SQLite); SQL Server reads reject. MongoDB blocks parsed
write/script operations. These controls do not sandbox arbitrary Python or privileged
backend extensions. A setup-level Python library in `<execute>` is admitted after a
static check (data-module imports only, no file or dynamic-code builtins, and under
`rngSeed` no imports inside a body). That check is no sandbox either; a seeded model
that loads Python always runs deterministic replay. Float-backed decimal ranges retain the former 15-place proof
limit. Compile support, bounded proof and real target delivery remain separate.

## Legacy intent models

There is no automated migration from the retired intent compiler. Re-author each
model as a project: write its XML as `datamimic.xml`, declare its expectations and
roles in `acceptance/build.json`, and run `datamimic authoring build <project>`.
Only `outcome: "ready"` establishes readiness. Keep the original until its data
matches the new project's output.

## Destructive database operations (BC-4.0-016)

CE 5.0 adds `clientId.clear` (every RDBMS row or Mongo document) and `clientId.drop` (Mongo collection); see I928
for the shape rules. A `delete` that reads a database `source` now needs a `selector`. Without one, the delete would
remove everything the source returns, so it fails with `I928` before any database access. Migrate each such model:

| Before | After |
|---|---|
| `<generate type="users" source="mongodb" target="mongodb.delete"/>` | `<generate targetEntity="users" target="mongodb.clear"/>` |
| `<generate source="db" sourceEntity="t" targetEntity="t" target="db.delete"/>` | `<generate targetEntity="t" target="db.clear"/>` |

A `delete` on generated rows (no `source`) or on a file source is unchanged: it deletes by the row keys. A selector
with an empty Mongo filter (`filter: {}`) still works as a delete; prefer `mongodb.clear` for that intent.

## Memstore read and write entities (#422)

In CE, `type` never sets the memstore entity that a product writes. On a `<generate>` that reads `source="mem"`,
`type` names only the entity it reads. The entity a product writes is `targetEntity`, else the product name.
Before CE 5.0, `type` also set the written entity, so a step that read one
entity and wrote the store appended its rows to the entity it read. A read of an entity that no product wrote now
fails with `MissingMemstoreProductError` instead of a log line and zero rows. `mem.entityCount` stays lenient.

| Before | After |
|---|---|
| `<generate name="slots" source="mem" type="demand" target="mem">` wrote `demand` | it writes `slots` |
| to keep the old routing | add `targetEntity="demand"` |

EE differs: it still writes `targetEntity`, then `type`, then the product name (see
[edition alignment](../architecture/inner/edition-alignment.md)). For a project that runs in both editions, read with
`sourceEntity`, write with the product name or `targetEntity`, and do not put `type=` on a memstore source. Build
names the cause when no product, or more than one product, writes the entity a memstore source reads.

## Enforcement and closure

Use the current upstream ArchKeel 3.0.1 pin with Python 3.11.12, as approved in
the [independent reader review](../architecture/refactoring-study/experiment-2/archkeel-3.0.1-review.md).
The adoption phase
[Amendment 214](../architecture/refactoring-study/experiment-2/amendment-214-ce-authoring-measurements.md)
and its 2.0.0 observations remain historical. Current-base integration requires fresh
3.0.1 baseline and merged-source evidence plus independent review; do not relabel
old measurements or receipts. [Amendment 215](../architecture/refactoring-study/experiment-2/amendment-215-current-base-reader.md)
records the reviewed first-merge measurements and strict controls.
[Amendment 216](../architecture/refactoring-study/experiment-2/amendment-216-windows-snapshot.md)
binds the Windows snapshot correction and tightened current ceiling. Existing public entries stay only until their
consumers migrate; future APIs are `planned`.
Promote them when implemented and remove retired entries with their callers.
Module declarations/layouts track real implementations when introduced, without
placeholder source modules. The stricter Application-to-Adapters target may expose
existing violations until the port migration; these are not accepted new grants.

Complete assignment/requires/interfaces and forbidden dependencies cover structural
boundaries. Runtime purity, row completeness, format semantics, factory integration
and serialization require behavior tests and independent review; structural PASS
alone cannot prove them. Check positive, forbidden-crossing and missing/empty scan
controls with the same pin. Keep existing architecture evaluators until equivalent
replacement evidence exists.

Closure requires focused and broad CE checks, baseline-bound output comparisons,
installed-wheel Python 3.11/current and lowest-Pydantic checks, true spawn and MCP
profiles, independent target/integration review and full CI on the final PR head.
Missing mandatory evidence keeps the work open. Raw private evidence stays outside
Git. Current guides/fixtures/repair text migrate with Python/CLI/MCP consumers.
