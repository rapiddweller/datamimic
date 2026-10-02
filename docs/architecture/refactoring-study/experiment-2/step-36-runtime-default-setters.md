# Step 36: Runtime default setters

The three `SetupContext` setters for separator, locale, and dataset now declare `str -> None`. Their getters already returned `str`; production assignments are guarded against `None`. No runtime behavior or descriptor changed.

The existing setup-merge test covers all three values. Independent QA passed it. Ruff and full-package mypy passed. With the same local ArchKeel analyzer as Step 35, `unknown_positions` fell from 207 to 201; violations stayed at 122. The target gate still fails.
