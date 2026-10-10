# Step 63: declare component-owned types

The root contract now declares `ConditionBranchStatement` under DSL and
`MemstoreManager` under Runtime ([Amendment 74](amendment-74.md)). Their nested
contracts retain ownership; no
facade exports or source changes were needed. A focused test checks each root
owner and excludes both from global `public_api`.

LOCAL VERIFIED: 7 focused architecture tests passed; `git diff --check` passed.
With the pinned candidate checker (`0.8.1.dev20+g0c1252490`), violations fell
117 → 115: `VIO-c7b50a08ba2544ae` and `VIO-b641da70c3c7bc84` resolved, with no
new IDs. Coverage remained 491/491 and UNKNOWN positions remained 161.
`declared_rules` remains FAIL; this slice does not make the report green.
Reports: `/tmp/ce-step63-before.json`, `/tmp/ce-step63-after.json`.

CI-ONLY VERIFICATION: not run.
