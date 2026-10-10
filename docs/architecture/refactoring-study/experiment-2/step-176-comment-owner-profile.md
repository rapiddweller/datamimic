# Step 176 — comment owner profile

One unchanged native owner test, `test_comment_is_noop`, ran at original
`a219163e` and current `019f9cbc`. Each test executed `comment_noop.xml` then
`comment_baseline.xml` once. All four complete typed captures matched:
`{"people":[{"i":1,"label":"x"},{"i":2,"label":"x"},{"i":3,"label":"x"}]}`.
Both owner tests passed. No native exception occurred.

The first original collection attempt stopped in the observation harness before
pytest collection because `/tmp` resolved to `/private/tmp`. The corrected
attempt stopped during pytest configuration: the installed rerun plugin could not
bind a localhost socket in the sandbox. Neither attempt collected a test or ran
a descriptor. Both FAIL receipts remain under `/tmp/ce-dsl-comment-20261010`.
Separate socket-capable collection and native attempts passed at both endpoints.

The exact XML blobs match both revisions. The owner body is unchanged; only its
`DataMimicTest` import moved. Native runs used the same project interpreter and
dependency versions, separate detached clones, normal pytest plugins, serial
execution, zero retries and bounded owned process groups. Runtime settings
matched except for original's `DEFAULT_LOGGER`. Loaded CE/test modules came from
their own clones. No service connection or subprocess was observed. Tracked
sources and protected primary files remained unchanged; no `temp_result_*`
remained. The raw open-path, stdout, stderr, JUnit and capture records are retained.

The additive ledger is based on accepted Step 175. Exactly two rows
change; the other 929 raw lines are byte-identical. Independent QA accepted
the evidence: reviewed owner profiles become **127/931**, leaving **804 UNKNOWN**.
Historical oracle and `c992` fields remain unchanged. See the
[receipt](step-176-comment-owner-profile-receipt.json).

This proves only this two-input native owner profile in one current dependency
environment. Standalone XML safety, full dynamic effects, interrupted cleanup,
frozen-oracle parity, other descriptors and EE remain UNKNOWN.

LOCAL VERIFIED: exact native runs and complete typed capture comparison, source
identities, environment/dependency profile, retained FAILs and cleanup.
CI-ONLY VERIFICATION: none for this bounded evidence step.
