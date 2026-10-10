# Amendment 168 — Memstore data owner

2026-10-08. Decision: Astra under Alex's delegation. Base `14821e5e`.
Implemented with bounded local checks and architecture review complete; machine binding remains open.

Move the unchanged Memstore implementation to `engine/io/memstore.py`.
IO-MEMSTORE owns run-scoped stored rows, raw access, aggregation and the existing
injected-client reconciliation. It does not construct clients, implement SQL,
load generic sources, choose exporters or manage Runtime store lifecycle.
The structural `get_random_rows_by_columns` call remains a behavioral dependency;
absence of a concrete import does not prove independence.

Move the existing empty Exporter marker into IO contracts. This keeps exporters
and Memstore dependent on one context-free marker without a component cycle.
Keep one canonical class through each existing IO facade name. Update consumers,
exact public declarations, requires, layout, source map and responsibility text.
Declare IO-MEMSTORE → IO-CONTRACTS for the marker, IO-API → sibling IO-MEMSTORE
for facade publication, and parent IO-EXPORTERS → sibling IO-MEMSTORE for target
construction/writes. Delete the old defining modules, EXPORTERS-MEMORY child
and its layout/declarations/publications, and nested registry/session `memory`
grants. Keep IO-EXPORTERS' source-read prohibition, coverage/cycle rules and
frozen baselines.
The historical source map explicitly merges the original IO contracts and
Exporter modules, retaining the separate DSL-contract split contribution.
Eight cohesive IO children need no additional hierarchy. Diagnostics no longer
require exporter core; database exporters retain core routing. These exact
directions follow Astra's reviewed source trace.

RUNTIME-STORAGE owns run-scoped Memstore creation, registration and lookup by ID,
and global increment counters. Remove only its agent-decided Runtime-contracts
grant: no decided storage operation consumes those types. EXPORTERS-CORE owns
exporter context protocols, configuration, buffering, output state, serialization
and target routing. IO-CONTRACTS owns the nominal marker. Other grants stay unchanged.

Follow Amendment 20: no old-path shims or class metadata overrides.
As in Amendment 83, physical module paths, class reprs and source metadata change.
Old direct imports and persisted pickle/dill references may fail. External
introspection, custom serializers and mixed-release workers remain UNKNOWN.
This is not full Python/DSL observational equivalence.

Preserve method bodies, state, dispatch/evaluation order, return values, native
errors, row identity and outer-list replacement behavior. Correct the inaccurate
list-mutation prose only. Bundle the three accepted Step 140 characterization
cases. Check canonical current identity/MRO and same-candidate serialization.
Compare actual SetupContext deepcopy behavior: it shares the original manager
but separately copies namespace values. Do not repair or misdescribe that split.
Ordinary serialization checks do not prove live worker transport.

Acceptance: targeted storage/read/dispatch/source/context checks; full Ruff/MyPy;
exact definition, cycle and pinned full/scoped architecture review. Separately
review an isolated before/after SQLite owner profile before running its destructive
output cleanup. Preserve descriptors/oracle; report broader DSL/EE/worker
UNKNOWNs independently. No tool/EE changes or merge.

LOCAL VERIFIED (Step 141, 2026-10-08): the same nine identity/storage/context/codec
cases and all 122 cases across six affected unit owners passed before and after.
The same six native cases passed at each checkpoint, including SQLite filtering;
cleanup left no residue. Each cohort ran once per checkpoint. Definition correction
passed 12 cases. Full-package Ruff, MyPy (490 files) and pinned Pylint cycle checks
passed on scratch candidates. Root and independent QA accepted these bounded
phases and the three-field responsibility refinement.

Integrated Main checks passed: 38 physical/API/registry cases, 12 definition cases,
four inner-target cases, full Ruff, MyPy (490 files) and pinned Pylint cycles.
The fresh ArchKeel 1.0.0 report has observation PASS and declared rules FAIL:
89 violations and 200 unknown positions. Baseline validation remains exit 2 with
58 new entries and none resolved; its 61 failure strings, measurement scalars and
21 diagnostic subjects match a fresh original `14821e5e` validation. Those entries
are pre-existing relative to the unchanged baseline, not new regressions in this
slice. The baseline, debt allowances and unrelated restrictions remain unchanged.

Machine amendment binding remains OPEN. The built-in writer attempt exited 2
with existing interface-unused/usage-unknown diagnostics; it wrote no JSON
(`artifact=null`, `amendment_status=null`). Its empty widening list does not prove
binding. Human Amendment 168 remains the approved decision. The unamended
comparison reports ten classifications matching the owner move and responsibility
refinement. Astra reviewed and accepted each for this coherent red checkpoint;
the machine-binding guard remains unsatisfied:

```sh
uvx --python 3.11 --from archkeel==1.0.0 archkeel validate --against 14821e5e665bacd47d8240818c739c0756af6212 --baseline known-violations.json --json
```

Full DSL/EE acceptance, historical old-path/metadata/introspection and
persisted-object compatibility, and live or mixed-release workers remain UNKNOWN.
No merge or baseline/oracle/ledger promotion. See the [target](target-architecture.md),
[protocol](protocol.md) and [report acceptance](step-113-report-acceptance.md) for
separate overall gates. CI-ONLY VERIFICATION: exact final-head CI remains pending.
