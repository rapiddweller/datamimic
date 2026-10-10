# Amendment 171 — Engine namespace; regular root retained

2026-10-09. Astra under Alex's delegation; CE base `7c152d47`.
Bounded installed-wheel pair and integration checks verified; final-head CI pending.

Remove only the empty `engine/__init__.py` and its module declaration; record the
frozen source removal. Engine remains the physical grouping for DSL, IO and
Runtime. Their ownership, APIs, dependencies, rules and decision labels remain
unchanged. No compatibility shim, artificial owner, baseline/oracle or EE change.

Retain the copyright-only regular root as the installed-distribution origin
anchor used by the wheel test and frozen Step0 guard. `_compat` owns interpreter
helpers, not distribution infrastructure. The root's unresolved component and
projection ownership stays visible; Amendment68's import-purity guard remains.

LOCAL VERIFIED: the existing installed-wheel owner passed once per disposable
checkpoint. Isolated offline builds and target installs passed; complete package
payloads are 1682 → 1681 with only the empty Engine marker removed. Installed
payload bytes, regular root origin, Engine namespace/path, three public APIs,
lazy CLI/MCP identity, entrypoints/help and domain/schema/demo assertions passed.
Settings/data roots, 21 config-probe origins, parent/config environments and
owned-group cleanup were checked; snapshots remained equal. A candidate prelaunch
cwd/dependency-context failure remains retained and launched no workload.

Independent QA accepted the pair. Main Ruff, MyPy (488 files), 12 definition
cases, four inner-target cases and Pylint cycles passed. Fresh pinned 1.0.0 report
exit 0 has observation/coverage PASS but still declares FAIL: 88 violations and
200 measured UNKNOWN positions; its complete 88 violation/254 canonical UNKNOWN
records match `7c152d47`. Two cycle edges and 1230 unresolved calls are unchanged.
The recorded-packet projection lists 25 levels/150 agent-authored components;
only the regular root's ownership gap remains. Engine's removed marker no longer
creates that gap; this does not establish whole semantic responsibility acceptance.
Recorded-packet DSL/IO/Runtime filters retain the global FAIL and root gap.

Known-baseline validation exits 2 with 60 failures/19 `interface.usage_unknown`
diagnostics, 57 new baseline entries and 0 resolved. Unamended comparison against
`7c152d47ff872e91f9870b18a3e3dd9381ae8f5f` exits 2 with 61 failures/the same 19
diagnostics and one `contract.declarations` widening for the Engine declaration
removal; amendment status/artifact are null. No writer or baseline/oracle change.
Astra accepts this coherent RED checkpoint; the checker failure remains.
Machine binding is OPEN (#415).
The initial unsupported filter queries remain retained; corrected queries read
the recorded packet without a rescan. Final-head CI is pending; prior `7c152d47`
push/PR CI each completed with 24 successes, two architecture failures and two skips.
Whole leaf-process environment and overall architecture acceptance remain UNKNOWN.

Engine file/spec/loader/path metadata and discovery can change. External consumers,
other Python versions, EE Maturin packaging and full DSL/worker compatibility
remain UNKNOWN. See the [target](../../inner/target.md) and
[protocol](protocol.md). No merge acceptance.
