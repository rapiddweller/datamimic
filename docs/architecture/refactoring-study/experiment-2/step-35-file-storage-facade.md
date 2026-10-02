# Step 35: remove duplicate file-cache facade export

`FileContentStorage` has no in-repo callers through `engine.io.api`; dataset code
already uses the narrower `engine.io.files.api`. Remove only the redundant
root-IO re-export. The cache implementation and dataset API are unchanged;
no descriptor was edited. A boundary test checks both absence from the broad
facade and continued availability from the file facade.

The same ArchKeel #209 analyzer reports 123 → 122 violations and 209 → 207
untyped import positions; `IO-API-TYPES` falls 34 → 33. The frozen baseline
still has 92 new positions and validation still fails. This is a facade
narrowing, not a passing architecture gate.

LOCAL VERIFIED: four focused IO architecture tests, Ruff on changed files,
ArchKeel validation (FAIL with the counts above), and `git diff --check`.
CI-ONLY VERIFICATION: not run for this provisional slice. Full DSL parity
remains open as recorded in [Step 31](step-31-descriptor-parity.md).
