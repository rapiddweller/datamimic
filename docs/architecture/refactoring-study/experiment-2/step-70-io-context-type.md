# Step 70: expose the IO context support type

Commit `69d4021c` re-exports the existing `MemstoreProvider` protocol through
`io.api`, where `ExporterContext` was already public. The root contract still
does not publish the implementation module; see [Amendment 75](amendment-75.md).

LOCAL VERIFIED on an isolated checkout: five focused IO tests, full-package
MyPy (491 files), Ruff, recursive target-definition and the Pylint cycle gate
passed. ArchKeel observed 491/491 files. Exactly
`VIO-d299a523e216ed64` disappeared; no violation or UNKNOWN ID was added.
Violations 91 → 90; UNKNOWN positions remain 168. The preceding report is the
negative probe: without the alias, that exact violation exists.

This is contract accuracy, not runtime behavior or target completion.
`declared_rules` still fails. The full descriptor parity gate and external
service tests were not rerun for this step. CI has not run for this commit.
