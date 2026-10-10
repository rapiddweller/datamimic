# Step 17b: Fail closed on unseeded nested-list counts

The unseeded oracle previously discarded nested-list lengths while merging
shapes. It could therefore accept a changed fixed `nestedKey` count. It now
records lengths per path and checks them against statically provable literal
counts, including the expected number of parent occurrences. Dynamic,
conditional, sourced, or ambiguous lists remain captured as structure but
are `UNVERIFIED`, not equivalent. Seeded digest comparison is unchanged.

Independent Luna implementation and QA passes preceded root review. QA caught
a false UNKNOWN for a `.properties` include; only descriptor includes now make
nested cardinality scope uncertain. Positive and negative cases cover fixed
counts, missing parent evidence, dynamic counts, deep nesting, zero rows,
scalar variation, and legacy evidence without cardinalities.

LOCAL VERIFIED: 61 oracle tests, both script self-tests, Ruff, and
`git diff --check` passed. Selected old/current SQLite seeded and unseeded
descriptors and a source-entity descriptor remained `CAPTURED` and equivalent.
An existing script-count descriptor is `UNVERIFIED` in both trees under this
stricter oracle; no parity is claimed for it.

CI-ONLY VERIFICATION: not run. The full descriptor corpus has not yet been
recaptured under this oracle; service-backed descriptors and dynamic nested
counts remain explicit evidence gaps.
