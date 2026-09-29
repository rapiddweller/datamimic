# Step 68: use the checker that understands module targets

Released ArchKeel 0.8.0 rejects this contract's `declarations.modules`, added
after that release, before architecture rules are evaluated. Both Make targets
now use immutable ArchKeel commit `0c1252490e736f4e742f02caf34923fc50395ec6`
(`0.8.1.dev20`). The report parses all 491 CE modules.

This does not make the gate green. The current validate run still reports
`interface.unused` for inherited service result types (ArchKeel #204), plus
baseline-new findings. Do not delete truthful public promises to satisfy the
checker or describe the target as achieved.

LOCAL VERIFIED: the pinned `archkeel --version`, `make architecture-report`,
recursive target-definition tests, and validate diagnostics. CI is pending.
