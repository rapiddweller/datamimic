# Step 08C19: pin the architecture gate

## Change

- `make architecture-check` runs ArchKeel 0.6.1 under Python 3.11 against
  `known-violations.json`. ArchKeel is not a CE runtime dependency: CE still
  supports Python 3.10.
- A separate CI job invokes the Make target. Tag publication now depends on
  that job. No product, XML, contract, or baseline file changed.

## Evidence

- The exact pinned Make target passed locally with a fresh uv cache:
  474/474 parsed, 0 violations, 0 unknown positions, no baseline drift,
  `declared_rules=PASS`.
- A pinned `--against eafc119f` check also passed with no new or resolved
  baseline findings.
- Independent implementation tested a disposable checkout containing a new
  forbidden `interfaces -> dsl` import; validation failed. YAML parses,
  `make -n architecture-check` and `git diff --check` pass.
- Remote CI has not run. The CI baseline gate catches observed drift, not a
  coordinated widening of the contract and baseline; `--against` and
  amendment review remain mandatory for contract changes.
