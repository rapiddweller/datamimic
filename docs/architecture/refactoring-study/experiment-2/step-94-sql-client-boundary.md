# Step 94: SQL ownership and client types

2026-10-02. Base `b15d265b`; published ArchKeel 0.8.4. Independent Luna
implementation and QA; fresh Astra source/specification and policy review PASS.

IO checks SQL capability and executes the unchanged query. Runtime holds a
typed client-ID dictionary and explicitly handles absent lookups. Constructor,
setter, registration, namespace binding, disposal and deepcopy retain identity
and ordering. No new registry class, TypeGuard, cast or dynamic dispatch.

CE5 decision: SQL accepts RdbmsClient and subclasses. Other injected SQL-capable
clients are rejected; unsupported targets now raise TypeError rather than
incidental AttributeError. Missing/None targets keep KeyError after content
resolution. Non-string registry keys are outside the typed API. External use is
UNKNOWN; this is not universal low-level Python compatibility.

Amendment 90 corrects the blanket model requirement for this native registry.
Only its constructor/getter/setter positions admit dict[str, Client]. Source-only
typing initially exposed 107 violations/154 UNKNOWN; no debt was accepted.
Independent full-evaluator probes recover each violation when its permission is
removed, reject bare/object/Any/wrong-key/union maps at all three seams, and
retain seam-local UNKNOWNs when Client cannot resolve. No checker was changed.

LOCAL VERIFIED: normal-plugin RED 4 failures/16 passes; final focused QA 21
passes. Unchanged Make unit target: 1621 passed, 11 unchanged skips, one existing
xfail, two existing Pydantic missing-port warnings. Ruff, full MyPy (492 files),
seven recursive-definition checks and pinned Pylint executable-cycle check pass.
Package-inclusive negative type probe reports exactly three expected errors.
Existing SQL integrations plus IO architecture tests: 21 passes. Installed CLI
help and current Python entry-point import smoke pass against isolated source.

Eight descriptors (two seeded, six unseeded) and four Authoring projections
match before/after: zero differences or tolerated variances. Inventory remains
930; this is not full-corpus/runtime-service parity. Historical capabilities
projection drift, complete report navigation and final behavior acceptance stay
open. The descriptor files, comparator, skips, xfails and baseline are unchanged.

Fresh amended report: 106 -> 104 violations; 157 -> 154 counted UNKNOWN
positions. Zero new finding/UNKNOWN IDs; two violations and three UNKNOWNs
removed. Baseline-new fingerprints 69 -> 68, resolved 0. All 492 files parse,
no contract diagnostics. Unresolved calls 1269 -> 1268; typing positions 145 and
two package/type cycle edges unchanged. Global architecture remains FAIL.

CI-ONLY VERIFICATION: this checkpoint pending push. Base CI completed with
architecture as its only failed job; E2E/release skipped. PR274 stays Draft.
CE #282, full descriptor parity, EE alignment and the 90% unit-coverage goal
remain separate. No ArchKeel issue, fix, merge or release is part of this step.
