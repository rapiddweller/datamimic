# Step 97: scalar statement types

Parent `6901abf0`; published ArchKeel 0.8.5. Statements expose parsed
configuration; tasks still execute it. Eight getter return annotations and
one generator-name field annotation record existing model guarantees.
No execution logic, initialization, contract, baseline, budget, descriptor,
oracle or gate changed.

## Measured result

| Check | Parent | Candidate |
| --- | --- | --- |
| Violations | 95 | 95 |
| Counted UNKNOWN | 150 | 142 |
| Raw UNKNOWN records | 204 | 196 |
| Files read/parsed | 492/492 | 492/492 |
| New baseline findings | 63 | 63 |

Exactly eight missing-return-annotation UNKNOWNs disappear. No new UNKNOWN
or violation appears. The DSL aggregate changes from 301/364 to 309/364
decided positions; unrelated UNKNOWN semantics, coverage and import-cycle
records are unchanged. Executable-import Pylint passes; two static cycle
edges remain in the observation. The overall architecture gate still FAILS.

## Local evidence

- Independent test first failed for all eight missing annotations; model
  values already passed. After implementation: 18 focused tests pass.
- Make units: 1,652 passed, 11 skipped, one xfail; two existing warnings.
- Lint/full MyPy pass; MyPy checks 492 files. Seven recursive-definition
  checks, four physical-target checks and pinned Pylint 3.3.7 pass.
- AST comparison removes only the eight named return annotations and
  `self._name: str` on its original assignment. All other nodes match.
- Five of eight frozen runtime cases compare successfully: one seeded case
  matches its output digest; four unseeded cases match their structural
  evidence. All four Authoring projections are identical.
- The full eight-case comparator remains red for three pre-existing
  UNVERIFIED nested-list cases. Their reasons remain unchanged. Existing
  converter/list consumer tests supplement, but do not close, those gaps.

This is an annotation checkpoint, not full affected-DSL parity or merge
approval. A separate list-evidence step must precede behavioral changes on
those paths. Full 930-descriptor equivalence, unit coverage, EE alignment,
complete report navigation and remaining type boundaries are still open.

`EchoStatement.value` remains excluded: an empty echo reaches Runtime with
None and crashes before placeholder handling. [CE #283](https://github.com/rapiddweller/datamimic/issues/283)
records the real runtime reproduction and the unresolved empty-text policy.
`get_parent_full_name` and the generator registry also remain separate work.

LOCAL VERIFIED: bounded source/AST review, tests and measurements above.
CI-ONLY VERIFICATION: the parent 6901abf0 pipeline passed runtime/test/build
jobs, but failed its strict architecture gate; E2E was skipped. Candidate
remote CI is not yet claimed.
