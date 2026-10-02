# Step 75: type the insurance coverage record

The existing producer projects six string fields. `InsuranceCoverageData`
now names that result; generator, cached model data and serialization share
it. Bodies, RNG, errors and ordinary-dict runtime output are unchanged.
[Amendment 79](amendment-79.md) declares only this inner public type.
No new package, root facade, row restriction, allowance or budget change.
The static return contract narrows; universal external typing compatibility
is not claimed. Separate Luna implementation/QA and Astra review approve.

LOCAL VERIFIED: the exact slice on clean `4e39e81` passes Make lint and
full-package MyPy (491 files), 1,528 Unit tests (11 skipped, 1 xfailed, two
Pydantic warnings) and 34 affected insurance API/DSL tests. Dirty integration
also passes recursive definition (5 tests); selected insurance service-replay
checks pass 25, skip 3. Frozen/current focused tests each pass 18, with guarded
baseline imports. Positive/negative static probes and runtime-body AST
comparison pass. No Python 3.10 runtime or EE execution was performed.

Public ArchKeel 0.8.1 retains exactly the same violation/UNKNOWN ID sets:
112 violations, 158 counted UNKNOWN (233 raw), 145 typing positions against
budget 143 and 2 cycle edges. This improves one real producer contract; it
does not reduce root findings or satisfy the final architecture gate.
Dirty source digest: `9a809f3c380ac4d9c9f34b00ae7dbc05b4ee7190beaffe578a3f96ccf28e6c1a`.
The hierarchy renderer is unreleased `0.8.2.dev27+g5d1506f11`; its JSON is
byte-identical to the public observation. Visual acceptance stays separate.

Two private serial captures inventory all 930 XML files. BEFORE/AFTER totals
match: 383 CAPTURED, 70 EXPECTED-ERROR, 16 NOT-A-DESCRIPTOR, 77 UNRUNNABLE,
384 UNVERIFIED. No status changes; all four projection payloads and all 109
captured seeded result/output digests match. Descriptors/comparator unchanged.
The same comparator remains FAIL: 477 differences, including 470 incomplete
records and 7 unseeded shape/output differences; three existing optional-shape
variances are tolerated. No exclusion or new oracle permission was added.
Service-classified cases remain excluded by this capture lane. Its historical
Podman-outage reason is stale, not evidence that Docker/OrbStack is unavailable.

Captured Python files match the working baseline before this slice. Snapshots
retain the older copied Git metadata; their source, not that copied HEAD label,
defines the comparison. Earlier dirty integration changes are not published
by this checkpoint. Full-corpus and architecture acceptance remain open.

CI-ONLY VERIFICATION: run `36766950609` at pushed `8927a0e3` passes normal
tests, external services, seeded matrix/hash comparison, lint, MyPy, build,
wheel smokes and the Sonar job. Architecture fails: 69 new boundary findings,
typing budget 145 > 143, and baseline ratchet reductions require reconciliation.
E2E/release are skipped. No merge/release or full descriptor pass implied.
