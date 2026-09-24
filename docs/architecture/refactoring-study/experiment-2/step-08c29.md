# Step 08C29: make service evidence path-addressable

The existing batch logs claim 100 of 273 service-classified XMLs compared to
frozen Step 0, but an independent audit could not reconstruct each path's
evidence class from the aggregate hashes and summaries. The standard oracle
still marks all 273 as skipped. The arithmetic 100/173 is not a deterministic
acceptance ledger.

`script/architecture_study/service_evidence_ledger.py` now derives the exact
273-path universe from the read-only inventory and promotes only paths
individually named in comparison records. As of Step 08C28 it has 1
`exact_seeded`, 8 `normalized_error`, 3 `normalized_unseeded`, and 261
`UNVERIFIED`. Matching expected errors are not counted as successful DSL runs.
The metadata names `658f3a5f` as a target *code/XML control*, not as the exact
execution HEAD for every older record; source and XML diffs from it to
`6190932d` are empty.

Independent QA verified all twelve cited path statements and found that an
early version accepted empty provenance references. The implementation now
rejects missing, absolute, traversing, out-of-scope, and nonexistent evidence
references. The stdlib self-check covers those negative cases, duplicate
inventory paths, unknown classes, and out-of-inventory evidence. Ruff and the
self-check pass. This ledger is deliberately conservative: a batch claim does
not become per-path proof merely by listing its member names.
