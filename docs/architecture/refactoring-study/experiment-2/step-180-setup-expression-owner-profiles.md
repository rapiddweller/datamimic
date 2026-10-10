# Step 180 — setup-expression owner profiles

Two unchanged native owners ran once each at original `a219163e` and current
`c2d40e4d`:

- `test_assert_setup_level_holds` returned three integer `42` rows from
  `assert_setup_level.xml`.
- `test_count_accepts_an_expression` returned integer `i=1..12` from
  `count_expression.xml`.

Each complete typed capture matched across endpoints. Both tests passed and
had no native exception. The XML blobs are identical at both endpoints, and
each owner body differs only by the moved `DataMimicTest` import. Four separate
detached clones, one project interpreter and dependency profile, normal pytest
plugins, serial execution, zero reruns and bounded process groups were used.
Collection found one item and the same fixture closure for each profile.
Loaded CE/test modules came from their own clones. No Python-level service
connection or subprocess was observed. Tracked sources and protected primary
files remained unchanged; no `temp_result_*` remained.

The [receipt](step-180-setup-expression-owner-profiles-receipt.json) pins both
preflights, native streams/JUnit, captures and comparisons. The accepted ledger
starts from accepted Step 179, changes two rows and preserves the other 929 raw
lines byte-for-byte. Independent QA passed: **131/931** owner profiles are
reviewed, leaving **800 UNKNOWN**. Historical oracle and `c992` fields are
unchanged.

This establishes only the two exact native owner profiles in one current
dependency environment. Standalone XML safety, full transient effects,
interrupted cleanup, frozen-oracle parity, other descriptors and EE remain
UNKNOWN.

LOCAL VERIFIED: one exact native test per endpoint and profile, complete typed
captures, identities, dependencies, cleanup and accepted ledger delta.
CI-ONLY VERIFICATION: none for this bounded evidence step.
