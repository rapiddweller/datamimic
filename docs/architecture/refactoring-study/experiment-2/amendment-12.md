# Amendment 12: separate structural acceptance from quality debt

Date: 2026-09-23. Approved by Alex after the final verification review.

## Decision

The experiment reports three separate verdicts:

1. **Structure reached:** the exact package layout, component graph, API boundaries, and
   declared rules pass with complete coverage, zero violations, and zero material unknown
   positions. The baseline contains no violation fingerprints. Numeric measurement budgets
   may remain positive but must not increase.
2. **Behavior preserved:** descriptor, projection, and public-entry compatibility checks pass.
   Unverified descriptors and environment-dependent tests remain explicit, never counted as
   passes.
3. **Delivery ready:** all required local gates, integrated ArchKeel release, and remote CI pass.
   A structural pass alone does not authorize a CE merge or release.

## Why the original wording was wrong

Protocol item 2 required validation without a baseline. ArchKeel requires `--baseline` when
`measurement_budgets` are declared, so that command exits 2 even with zero violations. The
same file stores violation fingerprints and numeric ratchets. An empty *violation list* is the
structural target; deleting the budget file would remove useful regression protection.

The 171 measured `cycle_edges` are package/module strongly connected component edges.
`NO-COMPONENT-CYCLES` separately checks the component graph and reports no violation. The
other positive measurements (typing positions, unresolved calls, untyped private accesses)
are visible quality debt, not evidence that a forbidden component edge remains. Requiring
all of them to reach zero inside this refactoring would change the target and reward proxy
fixes rather than verified behavior.

`unknown_positions=0` is the checker's material verdict, not a claim that it emitted no
UNKNOWN records. Amendment 11 documents 20 neutral raw UNKNOWN records with the same checker.

## Guardrails

- No `architecture-contract.json`, baseline budget, production, or DSL change accompanies this
  protocol amendment. The target prose now states the exact construct-rule scope instead of
  claiming complete internal typing. The four measurement values remain in the verification note.
- The structural verdict is local to the final candidate ArchKeel checker until its PRs are
  integrated and a released version repeats the gate.
- Pylint and six current OrbStack MSSQL/Oracle tests remain red for the documented baseline
  and local-service reasons. The 322 oracle-unverified entries remain unverified. These do
  not become green by renaming the verdict.
- No machine amendment JSON is generated: the architecture contract itself is unchanged.
