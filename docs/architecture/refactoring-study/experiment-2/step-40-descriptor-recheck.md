# Step 40: Descriptor recheck after runtime typing

The local oracle inventoried all 930 XML files at `757e643a`. It captured 383, found 70 expected errors and 16 non-descriptors, and left 77 unrunnable plus 384 unverified. These status totals match the earlier CE capture. It skips external services and stages local descriptors in temporary directories.

All 109 seeded `CAPTURED` descriptors match the frozen Step-0 capture in result, output, and combined digests. Of 274 unseeded captures, the comparator flags 16 against Step 0. In a focused same-edition repeat of the 19 cases that differed from the previous CE capture, 16 varied again. `test_entity_order.xml` stayed different from Step 0 across five current runs; its only shape difference was whether optional notes appeared in ten unseeded rows (the generator chooses a note with probability 0.2 per row). `test_casting_xml_value.xml` also differs in XML child-shape grouping and varied in a later same-edition repeat. Neither is proof of a code regression or equivalence.

Raw captures: `/private/tmp/step0-neu-757e643a.json` and targeted repeat files alongside it. The capability projection hash still differs from the frozen hash under Amendment 60's version-sensitive bridge. The full descriptor gate remains open because of incomplete service/shape evidence; this local run does not prove all 930 equivalent.

LOCAL VERIFIED: full local oracle capture, seeded digest comparison, focused same-edition repeats, and 1,444 unit tests (11 skipped, one expected failure). CI and external-service parity were not rerun.
