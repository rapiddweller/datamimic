# 2026-09-29 measurement amendment: source-length cache

Step 38 made one existing unknown boundary position measurable. Before:
`SetupContext.data_source_len` had `missing_annotation` status
(`UNKNOWN-BOUNDARY-TYPE-POSITION-8f32585dd1d041bc` in
`test-artifacts/architecture/ce-current-pr209-after-models/architecture.json`).
After: the same return is `dict[tuple[str | None, str | None], int]`, reported as
`VIO-21890c4ef717099c` in
`test-artifacts/architecture/ce-current-main-209/architecture.json`. With the
same analyzer, violations moved 122 → 123 and unknown positions 195 → 194.
Commit `fdf1a18f` changes annotations only; independent QA traced the sole
writer and consumers and passed focused tests.

This is a measurement clarification, not new runtime debt or an accepted
boundary. It is the sole exception to the per-step *count-decreases*
requirement: keeping the correct annotation is allowed, but Step 38 remains
gate-red. Do not add the finding to `known-violations.json`, suppress it, or
generalize this exception to other positions. Final acceptance still requires
zero violations, zero material unknowns, and complete coverage. The public-map
boundary needs a separate, narrow contract decision supported by the checker.
