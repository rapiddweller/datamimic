# Step 90: native smoke-export payloads

2026-10-02. Base `25eee585`; released ArchKeel 0.8.4. Astra approved removal of
two empty payload wrappers. Authoring still captures rows and reports DM002;
IO still checks options, writes, finalizes and counts. No responsibility moves.

SmokeExportRequest now carries native rows/options. The existing production path
bypassed RootModel validation; row identity, native/nested values and the shallow
options copy are preserved. External Python wrapper imports are UNKNOWN and may
break under the approved no-shim target. This is not a new DSL feature.

[Amendment 62](amendment-62.md) admits exactly four annotation records at two
request fields, not an entire facade. Source-only measurement makes the open
payloads visible; the contract change is disclosed, not hidden by another wrapper.

| Released-checker snapshot | Violations | Counted UNKNOWN |
|---|---:|---:|
| Base | 106 | 157 |
| Source only | 110 | 157 |
| Exact four-record amendment | 106 | 157 |

All three parse 492 modules at 100% AST coverage; unresolved calls remain 1269,
typing positions 145 and package-roll-up cycle edges 2. Pylint's executable
import-cycle check reports none. No invalid-contract diagnostics remain.
Digest-bound amended validation exits 1: 69 baseline-new fingerprints and
existing measurement drift. The baseline remains unchanged; global FAIL remains.

LOCAL VERIFIED: independent QA first recorded 12 failures / 7 passes on the base.
Standard-plugin focused exporter/boundary and unchanged Authoring tests now pass
(54). Root's full Make unit suite passes (1592, 11 skips, one existing xfail).
Definition checks (7), pinned Pylint, Ruff and full-package MyPy (492 files) pass.
These sets overlap and must not be summed.

The unchanged oracle inventories 930 XML files. Four selected runtime descriptors
(two seeded, two unseeded) compare with zero differences and zero tolerated
variances. Seeded values/output match within CE; unseeded shape/counts and all
four Authoring projections match. An earlier 13-selection probe leaves 11
Authoring fixtures UNVERIFIED by runtime-oracle policy; their real smoke tests
run in the unchanged Authoring suite. Full corpus/service parity is still open.
Descriptors, comparator and historical baseline are unchanged.

Independent released-checker probes confirm the exact positive and reject an
allowance moved to another method, another field or a misspelled field path.
Changing only the fixed `basename` annotation to an open map produces two
findings there; the four allowances remain unchanged. The probe baseline exists
only in a disposable copy, not in the repository. Astra's independent
specification and code-quality reviews pass for this bounded checkpoint;
neither verdict certifies the complete target.

CI-ONLY VERIFICATION: pending for Step 90. Base 25eee585 CI completes with tests,
services, replay, lint/types/build and Sonar passing, architecture failing.
PR274 remains Draft. Complete structure/behavior/report acceptance remains open;
ArchKeel gaps are delegated to the other agent, never patched in this CE step.
