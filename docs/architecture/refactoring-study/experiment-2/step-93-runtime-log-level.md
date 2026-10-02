# Step 93: typed Runtime log level

2026-10-02. Base 26ed7f6b; published ArchKeel 0.8.4. Independent Luna QA and
implementation, then Astra specification/code-quality review: PASS for this slice.

DataMimic keeps its args parameter and translates the old name lookup to a
stdlib integer. RunRequest carries log_level instead of argparse.Namespace.
Runtime configures logging after process bootstrap/title setup. Defaults,
unknown/non-string fallback, custom names/integers, NOTSET, exception propagation,
existing-handler behavior and descriptor execution/capture are preserved.
No helper, enum, configuration layer, permission or contract change.

Compatibility decisions: direct RunRequest(args=...) breaks for CE5.0; old
positional Namespace/None arguments now bind to log_level. Repository callers
were migrated/checked, but external direct callers remain UNKNOWN. A malformed
Python args object's conversion failure now precedes Runtime's best-effort
title effects; the same exception still propagates. Any stdlib integer remains
valid, without a closed level enum or range guard. These are explicit boundary
decisions, not universal compatibility proof.

LOCAL VERIFIED: root's normal-plugin RED: 3 failures/32 passes; independent QA
GREEN: 37 passes with socket-restricted plugins disabled. Root's unchanged Make
unit target runs normal plugins: 1610 passes, 11 skips, one existing xfail and the
same two Pydantic missing-port warnings as the parent. Ruff, full-package MyPy
(492 files), seven definition checks and pinned Pylint executable-cycle check pass.
All six selected descriptors (two seeded, four unseeded) and four Authoring
projections match before/after: 0 differences, 0 tolerated variances. Full 930-file
runtime/service parity and historical capabilities projection drift remain open.

Fresh report/against validation: 106 violations, 157 counted UNKNOWN positions,
69 baseline-new fingerprints, 0 resolved; global architecture remains FAIL. All
492 files parse; no invalid-contract diagnostics. Calls unresolved 1269, typing
positions 145 and package/type cycle edges 2 remain unchanged. The baseline,
descriptors, comparator, gates, skips and xfails are unchanged. No ArchKeel edit
or reproduced checker blocker; report usability/inherited-type issues remain
with the other agent. Selected local checks do not certify every semantic leaf,
EE parity or complete Actual/Target/Diff navigation.

CI-ONLY VERIFICATION: pending for this commit. Parent 26ed7f6b CI completed with
only architecture failing; E2E/release skipped. PR274 remains Draft. CE #282 is
separate: no nested-reference output fix or oracle adjustment is included.
