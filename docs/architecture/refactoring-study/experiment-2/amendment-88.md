# Amendment 88: deliberate existing API surfaces

2026-10-02. Decision: Astra, delegated architect. No production change.

Registry performs registration at package load, not a callable service:
declare `TASKS-REGISTRY.public: []`, rather than leaving it undecided.

The Shared and Healthcare use cases contain real deterministic JSON generation
policies consumed by `domains.facade`. Retain their owners; publish only each
existing request/generate pair: AddressRequest/address_api.generate,
PersonRequest/person_api.generate, DoctorRequest/doctor_api.generate and
PatientRequest/patient_api.generate. Helpers remain private.

The existing `authoring/__init__.py` deliberately exports AuthoringSpecV1,
ScaffoldRequest, ScaffoldResult, authoring_spec_json_schema and scaffold.
Assign only that initializer to AUTHORING-API with `exact_modules`. Keep the
existing internal interfaces and five-entry external declaration unchanged.
Do not change source exports, publish the recursive namespace or move files.

Astra corrected the original placement: component `public` governs internal
imports; `declarations.public_api` names external consumers. Published 0.8.4
rejected the original duplicated placement with ten `interface.unused` diagnostics.
The corrected external attempt then exposed incomplete exports. Read-only CE
function probes also found unresolved alias/type-origin closure questions; a
minimal CLI control correctly checks simple aliases and their own fields.
The inherited-field omission is independently reproduced with a complete fixture:
ArchKeel 0.8.4 returns PASS for an undeclared inherited payload type (#243).
Preserve these distinct results and the failed attempt; do not
reroute callers, add fake importers or expand exports just to silence a check.

Astra's final decision splits this step. External Authoring API completion remains
pending checker repair and deliberate API review. Its observed model graph is not
authorization to freeze every reachable class as a supported import. The full
target is unchanged; this ownership correction does not complete the external API.

This repairs omissions, not new behavior. No source, descriptor, oracle or
baseline changes; no empty EE mirror packages. EE adopts the same ownership
principle when its own API is migrated, not CE's different export vocabulary.
Same-checker receipts and negative helper/sibling probes must distinguish a
declared interface from one the analyzer has actually checked. Remaining UNKNOWN
is not accepted as PASS. Step 89 records the measured effects before acceptance.
