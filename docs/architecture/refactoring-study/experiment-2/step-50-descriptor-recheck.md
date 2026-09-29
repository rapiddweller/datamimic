# Step 50: local descriptor recheck

The current CE tree inventories all 930 XML files. The local oracle status for
every path matches Step 40: 383 captured, 70 expected errors, 16 non-descriptors,
77 unrunnable, and 384 unverified. All 109 seeded captures retain the same
result, output, and combined digests as Step 40. The two changed expected-error
messages only reorder the listed allowed attributes.

Six unseeded captures have a different output schema from Step 40. Five vary
in an immediate repeat on this same checkout; the sixth (`multi_xml.xml`)
varies in a second isolated repeat. These comparisons show same-edition
randomness, not cross-version equivalence for every unseeded value.

Compiler, authoring-reference, and scaffold-reference projection hashes match
Step 40. The capability projection differs: the schema version advanced and
`<transition>` now advertises `from`, `to`, and `weight` attributes. The
transition metadata change is recorded in the dated transition-grammar
amendment. The current comparator still recognizes only Amendment 60, so its
full projection gate reports a difference until the exact approved delta is
encoded and negatively tested.

LOCAL VERIFIED: 1,477 CE unit tests passed (11 skipped, 1 xfailed); 930 local
oracle cases ran with four workers and were compared with Step 40. Repeat
captures for the six unseeded schema differences ran serially. Raw captures:
`/private/tmp/ce-step53-oracle.json`, `/private/tmp/ce-step53-unseeded-repeat.json`,
and `/private/tmp/ce-step53-multi-xml-repeat3.json`.

CI-ONLY VERIFICATION: not run. The full descriptor gate remains open: 77
unrunnable and 384 unverified cases still need their applicable service or
shape evidence. This local recheck does not claim them equivalent.
