# Step 88: exact Registry ownership

2026-10-02. Base: `134628a7d8f0f4355f1c2d3007d5251efdd14ee5`.
Decision: [Amendment 87](amendment-87.md), Astra; independent Luna implementation and QA.

Use published ArchKeel `0.8.4`. Assign the executable Tasks initializer to Registry
with `exact_modules`, not a recursive Tasks selector. The existing definition
target runs the new static assertion. No production, descriptor, oracle, baseline,
public-interface or dependency-permission change.

## Same-checker comparison

Both inputs parse all 492 Python files. Source SHA-256:
`b9795afc1b3f35f99d59a22df88a54b53fcc1afc25fbf57bff5fc4c35414dbe6`.
Analyzer: `archkeel-python-analyzer 0.63.0`, code SHA-256:
`c2e05f4ac71d3bb4c5e4ada3f5f225f0f7080762fda5695c94589ad8f474cc18`.

Exactly one owner changes: Tasks initializer, unassigned → Registry. The other 49
task identities and owners stay fixed; a synthetic sibling stays unassigned.
Target contains the initializer once, with its unchanged responsibility sentence.
TASKS-ASSIGNMENT stays PASS; TASKS-REQUIRES-COMPLETE gains its 50-subject receipt
and moves UNKNOWN → PASS. Rule assessments: 228 PASS / 30 UNKNOWN / 5 FAIL →
230 PASS / 28 UNKNOWN / 5 FAIL.

All 106 violation and 218 raw UNKNOWN signatures remain identical, including
multiplicities. Counted UNKNOWN positions remain 157; these are not raw record
or rule-assessment counts. Git-bound validation reports 69 baseline-new findings
and zero baseline-resolved findings before and after. These are existing debt;
this step adds none. Validation remains FAIL, exit 1, with no input diagnostic.
An earlier archive-only comparison lacked Git metadata and exited 2; the clean
Git-bound comparison replaces it, not the accepted baseline.

Baseline SHA-256 stays
`166f55bec9ce690900e35b99b8f2cd91d3cb12a0fc2328b235512d65cd48d69e`.
The digest-bound amendment is [amendments/amendment-87.json](amendments/amendment-87.json).

## Verification and limits

LOCAL VERIFIED: focused test failed before the selector; fresh standard definition
checks (6 passed), cold CLI/registration/multiprocessing and physical-target checks
(8 passed), Pylint executable-cycle check (exit 0), and diff check. Earlier on the
same source candidate: unit suite 1,586 passed / 11 skipped / 1 xfailed, Ruff passed,
full MyPy passed for 492 files. Two existing Pydantic serializer warnings remain.

CI-ONLY VERIFICATION: pending the scoped experiment-branch push. No fresh full DSL
or external-service run, Ray execution, coverage measurement or CE merge here.
Registry still omits `public`: the checker represents this as undecided (`None`),
not deliberately empty. That separate target-definition repair remains open.
The whole CE target and its behavioral acceptance are not complete.
