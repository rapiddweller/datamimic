# Step 210 — native seeded state-machine owner evidence

[Receipt](step-210-receipt.json) curates independently admitted evidence for exactly
`tests_ce/integration_tests/test_state_machine/test_state_machine.py::test_seed_makes_the_walk_reproducible`.
Native sources are original `a219163e533d661bcc7bda0faa5ecc77909ab5aa` and current
`cf5cb9c4bd513444f0fc819b80fb359f97a8d2b9`; publication starts from `b1ca599c722fabb4a032789400f5fb67abac971d`.
**No native run at b1 is claimed.** No runtime, configuration or contract changes.

Two once-only owner launches produced **eight executions and eight complete captures**.
Every capture has 600 ordered rows: `dict[str, list[dict[str, str]]]`, sole product
`claims`, sole field `status`. All four corresponding capture bytes and complete
native type trees agree. At each endpoint, the three seed-2024 captures agree;
the seed-99 capture differs. All owner setup/call/teardown phases pass; errors are empty.
Per-call helper IDs agree through init/execute/capture, and the unchanged observer
returns the original capture result directly. IDs identify helpers; repeated IDs
between completed calls permit Python reuse. Captured-object identity/alias graphs remain UNKNOWN.

The independent admission is bound to final native freeze
`da873b4e8f8addec7735e00f2aa76a915fd225806959cd75f1909610cc6415f9`.
Source, descriptors, helpers, fixtures, interpreter, dependency/configuration profiles,
full captures, raw comparison and the recorded 13 rejection controls are hash-bound
in the receipt. Curation does not rerun those controls or the engine.

**Retained concern: the global primary-HEAD-unchanged claim failed.** Primary advanced
cf5→b1 through exactly `.github/workflows/main.yml`, `Makefile`, and unselected
`tests_ce/unit_tests/test_architecture_checker_pin.py`: a CI-only change.
The later integrity verifier exited **1**; its source, command and stderr stay retained.
Each launch's primary before/after agrees. Clone-owned source and observed reads support
bounded admission; they do not make the failed global anchor pass.

New external `/private/tmp/ce-step210-ledger.jsonl` adds only
`native_seeded_state_machine_owner_evidence` to the exact `complex_machine.xml` and
`complex_machine_seed99.xml` rows. All historical fields and owner supplements remain;
**929 other raw lines stay byte-identical**. Step208 stays immutable at
`9b3a61ad64899af8784333ec9ab2fb0fabea753e9842c84155824afd9d8dcb6a`.
Historical counts remain **931 rows / 180 reviewed / 751 UNKNOWN**; no promotion.
Standalone descriptor dependencies/isolation and unrelated DSL remain UNKNOWN.
Architecture remains **11 violations / 253 canonical UNKNOWN records / 199 positions**;
`declared_rules: FAIL`, full CE/EE target acceptance open.

LOCAL VERIFIED: source/raw hashes, receipt/ledger invariants and diff integrity;
one stdlib curation check, no engine imports or native calls.
CI-ONLY VERIFICATION: no new CI checked or launched; root retains b1/successor CI separately.

Skipped reruns, collection, services, broader tests and sealed re-inventory.
Risk: bounded CPython audit/profiler evidence excludes universal OS/native effect closure;
zero recorded connects is not a no-socket/bind/listen claim. Raw proof remains local.
