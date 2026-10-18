# CE Authoring and Errors migration

This migration replaces CE Intent/Scaffold with the Build contract below. Tracks CE #270.
Baseline: CE `84a9f4657148bcfa0bc560908ed42b1d5fa3efab`;
semantic reference: EE `37d74ddb3553ca23597a1b9264649361fe68a233`.
Python becomes >=3.11, without an added upper bound. CE keeps SCM package versioning;
Build `4.0` is a protocol version. This migration does not authorize merge or release.

## Public contract

Persist XML as the executable project. `DmJsonDocumentV1` is an in-memory agent
representation. Expectations are Build transaction input, declared again after
decompiling XML. `ee_version`, `ee_error`, `EeErrorIdentity` become `ce_version`,
`ce_error`, `CeErrorIdentity`; producer and installed version identify CE.

| Old entry | Replacement / consumer | Verification to retain |
|---|---|---|
| `AuthoringSpecV1`, `authoring.spec`, `ScaffoldRequest/Result` | DM JSON + `BuildRequestV4`, discriminated Ready/Rejected | Counts, roles, nested FK, memstore readback, time series, decimal/constraints |
| Root `scaffold`, `authoring.api.scaffold` | `create_authoring_application().build` | Full capture acceptance; explicit caller requirements with origin |
| `api.check`, `api.run` | Application-owned lint and bounded execution through CE ports | Parser diagnostics, per-generate caps, timeout/cleanup |
| `api.capabilities`, `api.reference` | Application capabilities, typed lookup, reference, schema, document_schema | CE registry projections and exact running DTO schemas |
| CLI `scaffold`, top-level authoring commands | `datamimic authoring {version,schema,capabilities,capability,reference,compile,decompile,build,lint,dry-run,run,export-contract}` | File/stdin/JSON, exit codes and bounded limits |
| MCP scaffold/discovery/check/bounded-run tools | Build, Compile/Decompile and discovery over the same application DTOs | Optional installation, stdio purity and transport parity |
| `datamimic run`, Domain/demo/Python runtime API | Existing owner and command retained | Seeded output, resources and normal runtime behavior |
| `DomainError`, `InvalidLocaleError`, `DomainErrorCode` | Same CE identities plus portable catalog/factories | ValueError ancestry where present, to_dict/path/hash/hint/details/locale and pickle |

Python facade publishes application, document/request/result/expectation/diagnostic
DTOs and required capability queries. CE Build adds typed `product_roles`,
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

Bounded resources use contained opened handles, including properties substitution
and cached file reads. Installed Domain datasets are read through their own loader;
custom `DATAMIMIC_DOMAIN_DATA`/`DATAMIMIC_ROOT` overrides reject bounded execution.
Connection profiles are workspace-local. XML includes are not bounded-eligible;
contained properties includes remain supported. Property-expanded sources can still
hit the pre-existing static unknown-source lint rule; executor support alone does
not prove public Build eligibility.

Bounded SQL sources use a conservative query subset and backend read-only transactions
(PostgreSQL, MySQL, Oracle, SQLite); SQL Server reads reject. MongoDB blocks parsed
write/script operations. These controls do not sandbox arbitrary Python or privileged
backend extensions. Float-backed decimal ranges retain the former 15-place proof
limit. Compile support, bounded proof and real target delivery remain separate.

## One-time legacy migration

Keep the frozen CE checkout at `84a9f4657148bcfa0bc560908ed42b1d5fa3efab`
and its compatible Python environment. From the new checkout:

```bash
PYTHONPATH=. .venv/bin/python script/migrate_authoring.py /project/model.dm.json \
  --legacy-source /path/to/frozen-ce \
  --legacy-python /path/to/frozen-ce/.venv/bin/python \
  --xml-output /project/model.xml > /tmp/migration-receipt.json
```

The script checks exact revision, clean package source and compiler origin before
importing the old compiler in an isolated subprocess. It keeps original input and
resources, refuses overwrite, and requires XML beside the original input to retain
relative paths. It compiles only; no engine or external target runs automatically.
Optional `--acceptance-requirements caller.json`, `--smoke-export`,
`--deterministic-replay`, `--max-count` and `--sample-rows` transfer transaction
requirements/options; they do not persist another intent model.

The receipt carries original/XML hashes, frozen revision, legacy plan/facts and a
separate typed `build_request`. It retains model expectations, caller/derived
origins, identifier/FK/timestamp/value roles (including nested-list fields), decimal
strings, list subjects, uniqueness scope and per-parent checks. Unknown semantics
reject at a specific input path. DM JSON in the receipt is temporary interchange.

Decompilation uses the new public application. To run the separate proof:

```bash
.venv/bin/python -c 'import json,sys; json.dump(json.load(sys.stdin)["build_request"],sys.stdout)' \
  < /tmp/migration-receipt.json | datamimic authoring build - --workspace-root /project
```

Only a new `outcome: "ready"` result establishes Build readiness. Compare its
compiled XML/data/acceptance with the preserved legacy receipt, especially nested
FK, file/memstore sources, time series, and decimal/list constraints. A successful
migration receipt alone is not verification. Keep the original until this comparison
passes. The installed runtime contains no legacy compiler or import shim.

## Enforcement and closure

Use the current upstream ArchKeel 3.0.1 pin with Python 3.11.12, as approved in
the [independent reader review](../architecture/refactoring-study/experiment-2/archkeel-3.0.1-review.md).
The adoption phase
[Amendment 214](../architecture/refactoring-study/experiment-2/amendment-214-ce-authoring-measurements.md)
and its 2.0.0 observations remain historical. Current-base integration requires fresh
3.0.1 baseline and merged-source evidence plus independent review; do not relabel
old measurements or receipts. [Amendment 215](../architecture/refactoring-study/experiment-2/amendment-215-current-base-reader.md)
binds the reviewed current-base measurements and strict controls. Existing public entries stay only until their
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
