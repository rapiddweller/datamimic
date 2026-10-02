# Step 73: validate identical capability projections

CE [#278](https://github.com/rapiddweller/datamimic/issues/278): the comparator
applied the historical migration bridge even to identical current captures.
The shared helper now accepts literal identity only after byte/hash, JSON
object, installed-version and nonempty-elements checks. The historical bridge
and other projection comparisons are unchanged. No descriptors or runtime
code changed; no baseline, budget, shape exclusion or contract was relaxed.

Independent Luna implementation and QA, then Astra review, found and fixed
an initial fail-open empty-manifest path and negative tests that could pass
through unrelated version mismatches. Final QA includes 31 identity cases
plus the 106 retained oracle tests. Reconstructed RED evidence matches the
initial two-line candidate; it is not a retained pre-fix snapshot.

The retained BEFORE projections now pass self-comparison and BEFORE/AFTER
comparison. Full comparison still fails: 930 descriptors, 477 differences
(469 incomplete-evidence records and eight unseeded shape differences).
Removing one comparator false positive is not full DSL-equivalence proof.
Service cases remain outside this capture lane.

LOCAL VERIFIED: final normal-plugin oracle/identity suite: 137 passed.
The exact three-file checkpoint applied to clean `49c586c6` passes 1,524 Unit
tests, with 11 skipped, 1 xfailed and two Pydantic warnings; Make Ruff and
full-package MyPy (491 files) pass. Its retained projection self/pair checks
pass; full descriptor comparison remains FAIL with the totals above. The
broader dirty checkout separately passed 1,533 Unit tests; its earlier source
changes are not published here. Scoped script/test Ruff and whitespace pass.
CI-ONLY VERIFICATION: pending publication of this scoped step. The previous
checkpoint's architecture job remains FAIL; no merge/release is implied.
