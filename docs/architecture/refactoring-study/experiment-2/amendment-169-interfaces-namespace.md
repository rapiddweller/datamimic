# Amendment 169 — Interfaces namespace

2026-10-08. Astra under Alex's delegation; CE base `fd1c866f`.
Disposable candidate verified; final-head CI pending.

Remove only the docstring-only `interfaces/__init__.py`. Interfaces remains the
physical grouping and root concern; its CLI, MCP, demo, project and Python owners,
publications, dependencies and rules stay unchanged. Keep active CLI/MCP lazy
initializers and all descendant APIs. Record the frozen marker's explicit removal;
preserve historical review and the source commit. No shim, artificial owner,
baseline/oracle change or root/engine initializer decision.

LOCAL VERIFIED: baseline owner 1 PASS; its original observer FAIL remains
retained (pytest's current-directory alias counted the same wheel twice). Additive
retained-wheel/config completion passed with zero new build/install/pytest calls;
the candidate owner then passed once. Complete package payloads are 1683 → 1682,
with only the marker removed; installed namespace, lazy exports, three Python
classes, entrypoints/help and domain/schema/demo assertions passed. The config
probe's 21 installed origins, settings, bytes, environment and cleanup were
independently verified. Wheel version/RECORD metadata was compared separately.

All new source gates, reports and filters below are from the disposable candidate
clone. Ruff, MyPy (489 files), 12 definition and four inner-target cases, and Pylint
cycles passed. Known-baseline validation returns exit 2: 88 violations, 200 measured
UNKNOWN positions and 60 failures (including 19 `interface.usage_unknown`), 57 new baseline entries and zero resolved.
Unamended comparison against `fd1c866f` returns the same exit 2/failures, no
widenings and null amendment status; no writer was used. Fresh report exit 0 has
observation/coverage PASS (489), but still declares FAIL. Its 254 canonical unknowns
are a separate count from the 200 measured UNKNOWN positions. The recorded-packet
Interfaces query selects zero violations and all five adapter IDs; global
root/engine ownership gaps and UNKNOWNs persist. Three negative guard checks reject
marker reintroduction and active CLI/MCP removal; the initial diagnostic scope
error remains retained. Final-head CI is pending; viewer navigation (#408) stays open.

Parent file/doc/spec/loader/path metadata and recursive discovery can change.
External introspection and discovery compatibility remain UNKNOWN; supported
consumers relying on regular-package semantics require a decision before proceeding.
This CPython 3.11 proof does not establish EE Maturin packaging, other Python
versions or full DSL/worker compatibility. Global FAIL/UNKNOWNs and machine
amendment binding (#415) remain separate; binding is UNKNOWN.
No tool/EE changes or merge. See the [target](../../inner/target.md) and
[alignment](../../inner/edition-alignment.md).
