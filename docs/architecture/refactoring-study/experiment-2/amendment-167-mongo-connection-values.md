# Amendment 167 — typed Mongo connection values

2026-10-08. Decision: Astra under Alex's delegation. Base `a183c486`.

Name the existing five-key result of `MongoDBConnectionConfig.get_connection_config`
as `MongoDBConnectionValues`, a required-key `typing.TypedDict` beside its producer.
Keep `host: str`, `port: int`, `database: str`, and nullable `user`/`password` values.
Publish that result type through the existing IO facade, beside the public model.
This is an additive typed API, not a new runtime object or driver-kwargs contract.

`IO-CONNECTION-CONFIG` owns the result. `IO-API` already consumes that component;
root IO already publishes the facade. No component, dependency, public-module
permission, baseline or allowed-position change is approved or needed.

Keep the getter's dict literal, fresh mutable container, field-value identity,
Pydantic extras/defaults and native errors. The Mongo client builds connection
kwargs separately and still reads its model/extras. Keep the abstract and RDBMS
getters unchanged: RDBMS returns an open model dump. Do not validate, cast, wrap
or restrict bypassed `model_construct`, assigned or subclass states.

The existing missing return annotation is a real source UNKNOWN. A local-only
named type does not prove publication through the root IO facade in ArchKeel
1.0.0. The explicit re-export makes the result type usable through the supported
API; it is not a grant added to lower a score.

Acceptance requires the existing Mongo config and setup-boundary tests, full
package Ruff/MyPy, unchanged method body/model/client and existing architecture
checks. Inspect the exact return position and its five field obligations in the
pinned report; a reduced total alone is insufficient. No mirror test or changed
descriptor, oracle, EE source or runtime behavior is approved.

Downstream annotation introspection and unusual dynamic consumers remain
UNKNOWN. This static contract adds no runtime guarantee for bypassed model
states. Full DSL, CE/EE and all-depth report acceptance remain open.

LOCAL VERIFIED: seven baseline Mongo config tests; 20 candidate connection-config
and Mongo/SQL setup tests passed. Candidate tests retain two Pydantic serializer
warnings; the Mongo warning also occurs in the baseline. Full-package Ruff and
MyPy passed (491 files). Pinned definition/structure tests: 12 passed.

ArchKeel 1.0.0 decides the getter's named return and records its five fields.
The missing-annotation obligation is removed; publication adds an
`inherited_surface` UNKNOWN for `MongoDBConnectionValues.__inherited_methods__`.
IO's decided positions rise from 213/255 to 214/256; its 42 UNKNOWNs remain.
The decoded 89 violation obligations are unchanged, with 200 measured UNKNOWNs
and 254 canonical UNKNOWN records globally. Observation PASS, declared rules
FAIL; architecture validation remains exit 2 with 21 existing diagnostics.

Astra and independent QA accept the precise source API while retaining the new
inherited/generated-surface uncertainty. A clean minimal stdlib TypedDict fixture
reproduces that UNKNOWN. An object-valued field still produces a violation while
the separate inherited uncertainty remains. The eager-annotated TypedDict has
unproven source-member binding; this concerns its inherited/generated surface,
not the getter's dictionary body. Track the tool policy in
[ArchKeel #412](https://github.com/rapiddweller/archkeel/issues/412).
No source workaround is approved.

CI-ONLY VERIFICATION: final-commit results are separate from this local receipt.
Previous `a183c486`
PR/push runs each completed with 24 successful jobs, two failed architecture
gates and two skipped jobs; these are not candidate verification.
