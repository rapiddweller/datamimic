# Step 62: complete the demographic record boundary

Declared the existing `DemographicAgeBand` and `DemographicConditionRate` at
the root Domains boundary. No source or descriptor changed. [Amendment 73](amendment-73.md)
records why the frozen contract was incomplete.

LOCAL VERIFIED: six focused ownership tests and five recursive target tests
passed. Independent Luna QA traced both public paths and the nested owner.
The same ArchKeel
candidate scanned 491/491 modules before and after: violations 121 → 117,
with exactly four owner-type finding IDs removed, no new violation or
UNKNOWN IDs, and 161 UNKNOWN positions unchanged. Removing either declaration
in a temporary probe restored its corresponding findings. The remaining
demographic typed-map findings remain visible. `git diff --check` passed.

CI-ONLY VERIFICATION: not run. The full descriptor-equivalence and
external-service gates remain open; this contract-only step did not alter
descriptor execution.
