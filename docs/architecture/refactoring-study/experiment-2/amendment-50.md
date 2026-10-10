# Amendment 50: fail-closed unseeded shape evidence

Date: 2026-09-28.

The Step-0 oracle now records field presence and nested object keys. Unknown or
all-null shapes no longer count as structural equivalence. Nullable samples
remain comparable only when both sides observe the same concrete type.

This strengthens the frozen behavioral gate; it changes no descriptor or
runtime behavior. Older unseeded snapshots lack presence evidence and must be
recaptured. A presence-count difference is inconclusive until repeated runs or
descriptor semantics distinguish randomness from a regression. Exported-file
schemas and service-backed descriptors still require separate evidence.
