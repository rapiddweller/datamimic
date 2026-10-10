# Step 68: use the checker that understands module targets

Released ArchKeel 0.8.0 rejects this contract's `declarations.modules`, added
after that release, before architecture rules are evaluated. Both Make targets
now use immutable ArchKeel commit `20ee2979dedbc45bae125dcd3d13f58b28092d14`
(`0.8.1.dev27`). This includes the merged inherited-generic fix (#204).
The report parses all 491 CE modules.

This does not make the gate green. The current validate run has no contract
diagnostics, but still reports 85 violations, 169 UNKNOWN positions, and 66
baseline-new findings on the dirty worktree. Do not describe the target as
achieved.

LOCAL VERIFIED: the pinned `archkeel --version`, `make architecture-report`,
recursive target-definition tests, and validate diagnostics. CI is pending.
