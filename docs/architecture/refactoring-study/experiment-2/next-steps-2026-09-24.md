# Experiment 2 continuation, 2026-09-24

The structural target is reached locally, but behavior and delivery are not
accepted. Batch logs arithmetically report 100 of 273 service-classified XMLs
paired with Step 0. The strict path ledger currently classifies only 14 by
individual path and evidence class, including eight matching expected errors;
259 remain `UNVERIFIED`. This is an
evidence-accounting correction, not evidence that the earlier runs failed.
The 200,000-row SQLite case has count/schema parity, not exact row parity.
`make lint` remains red on both revisions, and remote CE CI has not run.
Keep frozen `a219163e` and the exact 930 XML bytes as controls.

## Order

1. **Close behavioral evidence.** Compare each remaining executable descriptor
   against Step 0. Use fresh copies and disposable SQLite databases or
   Docker/OrbStack services with asserted endpoints. Seeded cases require exact
   captured rows and normalized file/DB output; unseeded cases require outcome,
   counts, and shape parity. Record intentional failures, non-descriptors, and
   blocked fixtures separately. First bind every claimed comparison to an
   exact XML path and evidence class; leave unprovable cases UNVERIFIED. The
   read-only service inventory lists all 273 service-classified XMLs and owner
   *candidates*. Resolve owner, config, backend, and destructive setup manually
   for each residual case before running it. Never point destructive setup at
   shared data. An unused MySQL fixture that could restart `mysql-local` was
   removed after independent unit-test review (Step 08C31).
2. **Improve CE tests in small slices.** Deduplicate fixture lifecycle and
   assertions only where a shared invariant exists. Preserve coverage and XML
   bytes. Track duplicate tests separately from runtime-equivalence evidence;
   ArchKeel does not scan `tests_ce` yet.
3. **Review residual architecture debt.** Challenge the seven internal SCCs,
   171 cycle edges, facade sizes, unresolved calls, and typing positions.
   Narrow the contract only with a measured, dated amendment; do not call a
   passing component graph a cycle-free codebase.
4. **Separate EE-to-CE product work.** Compare existing CE authoring projection
   with EE before porting anything. Then take authoring derivation, error
   handling, and logging as separately tested changes. Preserve CE public APIs
   and descriptor behavior. Reimplement CE-owned behavior; do not copy
   Enterprise-licensed code into MIT CE without a license decision. The Rust
   core stays EE-only.
5. **Feed Experiment 3.** Turn reproduced checker blind spots into ArchKeel
   negative fixtures and rules, including module-level cycles, public facade
   quality, unresolved calls, and test-namespace governance. Dart is outside
   this worktree and this acceptance run. The typed-iterator `boundary_types`
   repro is drafted in `archkeel-issue-typed-iterator.md`; filing is blocked by
   GitHub integration 403 and an invalid local `gh` token.

## Separation and gates

- Luna implementation changes one approved slice; Luna verification owns the
  independent Step-0 comparison; Luna review challenges both before acceptance.
  The orchestrator owns contract changes, integration, commits, and verdicts.
- Per slice: targeted positive/negative tests, affected descriptor/projection
  parity, ArchKeel baseline/against, relevant serial suites, Ruff, full-package
  MyPy, diff review, and a step log. Do not weaken a gate to hide a regression.
- The pinned ArchKeel 0.6.1 Make/CI baseline gate is now committed. It catches
  observed drift, not a coordinated contract-and-baseline widening; contract
  edits still require an explicit `--against` run and amendment review.
- Report **structure**, **behavior**, and **delivery** separately. Open a CE PR
  only after local gates and the full descriptor ledger are honest; merge or
  release only after independent review and remote CI.
