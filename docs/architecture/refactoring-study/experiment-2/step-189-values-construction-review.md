# Step 189 — keep the value-construction component

Astra accepts `VALUES-CONSTRUCTION` as one deliberate semantic leaf at
`7e9e8973`. Its six modules bind DSL value declarations to executable values
and run state. No observed responsibility leak or reversed dependency justifies
another component, facade or relocation.

| Module | Responsibility and existing boundary |
|---|---|
| `factory.py` | Select/bind generators and primitive defaults; Context owns cache/RNG. |
| `entity.py` | Bind constructor arguments, demographics and identifiers; Domains produces values. |
| `entity_constructor.py` | Parse constructor text shared with identifier policy. |
| `converters.py` | Bind ordered converters and run Hash key; callers execute conversion. |
| `global_increment.py` | Bind run-scoped increments; Storage owns counter state. |
| `sequence_table.py` | Bind sequence/page ranges; IO owns SQL, connections and transactions. |

All paths are under `datamimic_ce/engine/runtime/tasks/values/construction/`.
The existing machine contract declares this owner, public operations and
dependency decisions. Its visible modules are implementation details of the
same responsibility. Keep all six visible; no contract or production change
is required. The shared CE/EE target already places stateful sequence generation
beside this factory.

The [receipt](step-189-values-construction-review-receipt.json) pins Astra's
complete caller/state/IO trace. Preserve dynamic signatures, cache identity,
RNG consumption, native errors and sequence reservation semantics. This static
review does not prove concurrency, exact sequence counts or behavioral parity.
The lazy sequence-recovery call/signature mismatch is a separate investigation.

LOCAL VERIFIED: six-module ownership review and immediate boundary traces;
current production source matches the reviewed revision. CI-ONLY VERIFICATION:
none for this semantic decision. Other semantic scopes and full acceptance remain open.
