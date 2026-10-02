# Step 86: IO owns export completion

Parent: `b38899c9`. Decision: amendment 86; independent Luna implementation,
Luna QA and Astra review. Runtime retains statement traversal and the global
finalize-before-publish order. IO owns chunk completion, publication and cleanup.
The three relocated function ASTs are unchanged. No compatibility aliases.

## LOCAL VERIFIED

The exact staged snapshot was checked separately from older unstaged edits:

- Unit suite: 1,572 passed, 11 skipped, one existing strict xfail.
- Lifecycle/exporter and recursive-definition checks: 118 passed, one existing xfail.
- Full-package Ruff and MyPy: clean; 492 files checked. Pinned Pylint cycle check: clean.
- Seeded nested JSON/CSV: all eight named output-file hashes match the parent.
- Unseeded multiprocess JSON/CSV: six content hashes match as a multiset;
  worker arrival can exchange collision-suffixed filenames. Named-file parity is not claimed.
- Released ArchKeel 0.8.3: 492/492 files parsed, observation and coverage PASS.
  Parent and staged snapshot both have 106 violations and 157 counted UNKNOWN
  positions, with identical violation counts per rule. `declared_rules` remains FAIL.

The dirty worktree separately passed 1,580 unit tests and reports 102 violations
and 155 counted UNKNOWN positions. Those older changes are not in this step.
The reports and byte-probe artifacts remain local under `test-artifacts/`.

## Limits

The unchanged frozen oracle selected six descriptors: two CAPTURED, four
UNVERIFIED. Its comparator exits 1 with five differences, including multiprocess
per-file schema partitioning. Its four canonical projections match before/after
this step. Full corpus parity is not established; no descriptor, oracle, baseline,
allowance, skip or xfail was changed.

The existing conditional-child publication xfail remains. Cleanup failure can
still replace an export exception; this pre-existing behavior was not changed.
EE migration and every-depth browser acceptance remain unverified.

## CI-ONLY VERIFICATION

Not run for this step at recording time. The prior CI result does not certify
this staged snapshot. No merge or final target-completion claim.
