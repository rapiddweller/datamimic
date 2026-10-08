# Step 31: fresh descriptor Alt/Neu check

The frozen Step-0 checkout is `a219163e`; the current CE checkout reports
`be769229` but has uncommitted architecture changes. Both captures used the
current oracle with only the old checkout's import paths adapted, the same
current virtualenv, and no external services. The raw local captures are
`/private/tmp/step0-alt-a219163.json` and
`/private/tmp/step0-neu-be769229.json`.

Both inventories contain 930 XML files with identical status totals:
383 CAPTURED, 70 EXPECTED-ERROR, 16 NOT-A-DESCRIPTOR, 77 UNRUNNABLE, and
384 UNVERIFIED. All 109 seeded CAPTURED results have identical result and
output digests. The comparator reports 481 differences overall; most are
incomplete evidence or inventory metadata, **not** 481 behavior regressions.
Among CAPTURED cases, nine unseeded sample projections differ and nine more
have identical payloads but the shape checker rejects null-only or unknown
leaves. Eight of the nine differing unseeded projections also varied in
same-edition repeat captures. `test_entity_city.xml` remains open: its
population sample differed Alt/Neu but stayed null-only in five current
repeats. The descriptor has no seed. Its DE city CSV is byte-identical at both
revisions; only 952 of 18,882 rows have a population. The reader still calls
the same CSV parser. A random sample difference is plausible, but this is
neither proof of a regression nor proof of equivalence.

The 77 UNRUNNABLE and 384 UNVERIFIED descriptors remain unproved, including
service-backed cases. The comparator's capability projection bridge is also
version-dependent. Exact DSL parity cannot yet be claimed. The next check
must use fresh isolated service state for both editions, retain the dirty-tree
provenance, and resolve or explicitly bound the City and shape-checker cases.

LOCAL VERIFIED: fresh two-checkout capture, comparator, focused same-edition
repeats, and 1,443 CE unit tests (11 skipped, one expected failure).
CI-ONLY VERIFICATION: not run for this provisional step.
