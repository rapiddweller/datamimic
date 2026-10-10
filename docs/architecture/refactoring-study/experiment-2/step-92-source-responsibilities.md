# Step 92: Runtime source ownership

2026-10-02. Base `694c4208`; published ArchKeel 0.8.4.
Independent Luna QA/implementation and Astra source review support retaining
the reference and variable adapters in Runtime. Tasks own execution/cursor
lifetime and scope writes; IO owns source reads and selection algorithms.

Correct only the two module responsibility sentences and matching manifest
entries. Reference also identifies shared-rotation requirements; variable
plans source modes. No source, path, public interface, permission, descriptor,
oracle or baseline changes. This accepts those sentences/owners, not complete
behavioral correctness or the remaining recursive target.

The review found [CE #282](https://github.com/rapiddweller/datamimic/issues/282):
`unique="true"` inside a condition recreates the same seeded reference pool.
Root's real XML/SQLite run produced six identical IDs without exhaustion;
the direct four-row control produced four distinct IDs. Independent task/IO
probe agrees. Relevant paths match parent3f; Astra also found the mechanism
in frozen source. Historical runtime was not rerun. Keep the behavioral fix
separate: finite cursor lifetime belongs Runtime, not an endless IO cycle.
Intentional changed output needs its own frozen-oracle/protocol decision.

LOCAL VERIFIED: unchanged reference/source-routing tests56passed; Make target
definition7passed; JSON parsing and diff checks pass. Source digest unchanged.
Decoded before/after report differs only in contract metadata and the two
declared responsibility strings; observed facts and UNKNOWNs are identical.
Validation against the base has no invalid diagnostics or permission change,
but exits1:106violations,157countedUNKNOWN,69baseline-new fingerprints, typing
145against budget143. None is waived; global architecture remains FAIL.

CI-ONLY VERIFICATION: not run for this step yet. Parent694c CI completed with
tests/services/replay/build/lint/types/Sonar passing; architecture failing;
E2E/release skipped. Complete leaf acceptance, full930descriptor parity, EE
alignment and every-depth report usability remain open.
